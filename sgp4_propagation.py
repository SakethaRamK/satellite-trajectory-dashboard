from sgp4.api import Satrec, jday
from datetime import datetime, timezone, timedelta
from vector_operations import subtraction, magnitude
import matplotlib.pyplot as plt
import numpy as np
from tle_parser import validate
import requests
from pathlib import Path
import json
satellites = []
earth_radius = 6371
DATA_DIR = Path(__file__).resolve().parent
CACHE_FILE = DATA_DIR / "satellite_latest.tle.txt"
METADATA_FILE = DATA_DIR / "tle_cache_metadata.json"
CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php"
TLE_GROUP = "STATIONS"

def _read_metadata():
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def _write_metadata(metadata):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary_file = METADATA_FILE.with_suffix(".tmp")
    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)
    temporary_file.replace(METADATA_FILE)

def get_tle_status():
    metadata = _read_metadata()
    return {
        "cached": CACHE_FILE.exists(),
        "last_attempt_utc": metadata.get("last_attempt_utc"),
        "last_success_utc": metadata.get("last_success_utc"),
        "source": metadata.get("source","Local cache" if CACHE_FILE.exists() else "No cached TLE file"),
        "last_message": metadata.get("last_message", ""),
    }

def tle_parse_date(tle_record):
    line1 = tle_record[1]
    epoch = line1[18:32]
    year = int(epoch[:2])
    date = float(epoch[2:])
    if year < 57:
        year += 2000
    else:
        year += 1900
    return datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=date - 1)

def load_tle_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            content = [line.strip() for line in file.readlines() if line.strip()]
        loaded_satellites = []
        if len(content) % 3 == 0:
            for i in range(len(content) // 3):
                if (content[3 * i][0] not in ("1", "2") and content[3 * i + 1].startswith("1 ") and content[3 * i + 2].startswith("2 ")):
                    name = content[3 * i]
                    line1 = content[3 * i + 1]
                    line2 = content[3 * i + 2]
                    if validate(line1, line2):
                        loaded_satellites.append((name, line1, line2))
                else:
                    print(f"This data is not in standard TLE. Incomplete record for {content[3 * i]}")
        else:
            print("Incomplete TLE information.")
            return []
    except Exception as e:
        print(e)
        return False
    return loaded_satellites

def create_satellite(time, tle_record):
    max_tle_age = 24.0
    name, line1, line2 = tle_record
    satellite = Satrec.twoline2rv(line1, line2)
    tle_epoch_time = tle_parse_date(tle_record)
    tle_age = time - tle_epoch_time
    tle_age_h = tle_age.total_seconds() / 3600
    print(f"Satellite: {name}")
    print("Satellite number:", satellite.satnum)
    print("Inclination:", satellite.inclo)
    print("Eccentricity:", satellite.ecco)
    print(f"TLE age: {tle_age_h:.2f} hours\n")
    if tle_age_h > max_tle_age:
        print(f"TLE status: Stale, exceeds the max tle age of {max_tle_age}")
    elif 0 <= tle_age_h <= max_tle_age:
        print("TLE status: Valid")
    else:
        print("TLE status: Invalid as TLE epoch is in the future")
        return None
    return satellite, name

def generate_trajectory(start_time, tle_record, duration, timestep):
    trajectory = []
    created = create_satellite(start_time, tle_record)
    if created is None:
        print(f"Skipping {tle_record[0]} because its TLE epoch is in the future.")
        return False
    satellite, name = created
    for second in range(0, duration, timestep):
        current_time = start_time + timedelta(seconds=second)
        jd, fr = jday(current_time.year,current_time.month,current_time.day,current_time.hour,current_time.minute,current_time.second)
        elapsed = (current_time - start_time).total_seconds()
        error, position, velocity = satellite.sgp4(jd, fr)
        if error != 0:
            print(f"Propagation failed, Error: {error}")
            return False
        distance = magnitude(position)
        speed = magnitude(velocity)
        trajectory.append({
            "satellite": name,
            "time": current_time,
            "elapsed_seconds": elapsed,
            "position": list(position),
            "velocity": list(velocity),
            "distance": distance,
            "speed": speed,
            "altitude": distance - earth_radius,
        })
    return trajectory

def relative_motion(trajectories, times):
    satellites_present = list(trajectories.keys())
    rel_trajectories = []
    for i in range(len(satellites_present)):
        j = i + 1
        while j < len(satellites_present):
            for step in range(times):
                new_satellite = satellites_present[j]
                constant_satellite = satellites_present[i]
                rel_pos = subtraction(trajectories[new_satellite][step]["position"],trajectories[constant_satellite][step]["position"])
                rel_vel = subtraction(trajectories[new_satellite][step]["velocity"],trajectories[constant_satellite][step]["velocity"])
                rel_trajectories.append({
                    "satellite_pair": f"{new_satellite} <-> {constant_satellite}",
                    "time": trajectories[new_satellite][step]["time"],
                    "rel_position": rel_pos,
                    "rel_velocity": rel_vel,
                    "distance": magnitude(rel_pos),
                    "relative_speed": magnitude(rel_vel),
                })
            j += 1
    return rel_trajectories

def load_snapshot(filename):
    loaded = load_tle_file(filename)
    if not loaded:
        return None
    return loaded[0]

def test_snapshots():
    snapshot1_path = DATA_DIR / "satellite_20261010_032858.tle.txt"
    snapshot2_path = DATA_DIR / "satellite_20261010_033052.tle.txt"
    if not snapshot1_path.exists() or not snapshot2_path.exists():
        print("Snapshot test skipped: required TLE snapshot files are unavailable.")
        return
    snapshot1 = load_snapshot(snapshot1_path)
    snapshot2 = load_snapshot(snapshot2_path)
    if snapshot1 is None or snapshot2 is None:
        print("Could not load both TLE snapshots")
        return
    print("Snapshot 1:", snapshot1[0])
    print("Snapshot 2:", snapshot2[0])
    comparison_time = datetime.now(timezone.utc)
    trajectory1 = generate_trajectory(comparison_time, snapshot1, 601, 10)
    trajectory2 = generate_trajectory(comparison_time, snapshot2, 601, 10)
    if not trajectory1 or not trajectory2:
        print("An error took place while generating the trajectory")
        return False
    times = []
    disagreements = []
    for point1, point2 in zip(trajectory1, trajectory2):
        difference = subtraction(point1["position"], point2["position"])
        position_difference = magnitude(difference)
        times.append(point1["time"])
        disagreements.append(position_difference)
    if len(disagreements) == 0:
        return False
    average = sum(disagreements) / len(disagreements)
    print(f"Average Disagreement: {average:.6f}km")
    print(f"Maximum Disagreement: {max(disagreements):.6f}km")
    print(f"Final Disagreement: {disagreements[-1]:.6f}km")
    plt.figure(figsize=(10, 6))
    plt.plot(times, disagreements, color="blue", linewidth=3)
    plt.title("Variation of disagreements over time")
    plt.xlabel("Time (UTC)")
    plt.ylabel("Disagreement (km)")
    plt.grid(True)
    plt.show()

def plot_earth(ax, earth_radius):
    u = np.linspace(0, 2 * np.pi, 60)
    v = np.linspace(0, np.pi, 30)
    x = earth_radius * np.outer(np.cos(u), np.sin(v))
    y = earth_radius * np.outer(np.sin(u), np.sin(v))
    z = earth_radius * np.outer(np.ones(np.size(u)), np.cos(v))
    ax.plot_surface(x, y, z, alpha=0.35, linewidth=0, antialiased=True)
    ax.plot_wireframe(x, y, z, rstride=3, cstride=3, alpha=0.12, linewidth=0.5)

def satellite_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata = _read_metadata()
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    last_attempt = metadata.get("last_attempt_utc", "")
    if last_attempt:
        try:
            last_attempt_date = datetime.fromisoformat(last_attempt.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            last_attempt_date = None
        if last_attempt_date == today:
            loaded = load_tle_file(CACHE_FILE) if CACHE_FILE.exists() else []
            if loaded:
                satellites.clear()
                satellites.extend(loaded)
                metadata["source"] = "Local cache"
                print(f"Using cached TLE data; today's download attempt has already been used. Loaded {len(satellites)} satellites.")
                return True
            print("Today's download attempt has already been used and no valid cache is available.")
            return False
    metadata["last_attempt_utc"] = now.isoformat()
    metadata["last_message"] = "Download attempt started"
    _write_metadata(metadata)
    try:
        response = requests.get(CELESTRAK_URL,params={"GROUP": TLE_GROUP, "FORMAT": "TLE"},headers={"User-Agent": "SatelliteTrajectoryMonitor/1.0"},timeout=(5, 10))
        response.raise_for_status()
        if not response.text.strip():
            raise ValueError("CelesTrak returned an empty TLE response.")
        temporary_tle = DATA_DIR / "satellite_download_temp.tle.txt"
        with open(temporary_tle, "w", encoding="utf-8") as file:
            file.write(response.text)
        loaded_satellites = load_tle_file(temporary_tle)
        if not loaded_satellites:
            temporary_tle.unlink(missing_ok=True)
            raise ValueError("Download received, but no valid TLE records were found.")
        temporary_tle.replace(CACHE_FILE)
        metadata["last_success_utc"] = now.isoformat()
        metadata["source"] = "CelesTrak download"
        metadata["last_message"] = (f"Downloaded and cached {len(loaded_satellites)} satellites.")
        _write_metadata(metadata)
        satellites.clear()
        satellites.extend(loaded_satellites)
        print(metadata["last_message"])
        return True
    except requests.exceptions.HTTPError as e:
        status_code = (e.response.status_code if e.response is not None else "unknown")
        metadata["last_message"] = (f"CelesTrak returned HTTP {status_code} no retry will occur today.")
        print(metadata["last_message"])
    except requests.exceptions.ConnectionError:
        metadata["last_message"] = ("Connection error; no retry will occur today.")
        print(metadata["last_message"])
    except requests.exceptions.Timeout:
        metadata["last_message"] = ("CelesTrak request timed out; no retry will occur today.")
        print(metadata["last_message"])
    except requests.exceptions.RequestException as e:
        metadata["last_message"] = (f"TLE download failed: {e} no retry will occur today.")
        print(metadata["last_message"])
    except Exception as e:
        metadata["last_message"] = (f"TLE download failed: {e} no retry will occur today.")
        print(metadata["last_message"])
    _write_metadata(metadata)
    loaded_satellites = (load_tle_file(CACHE_FILE) if CACHE_FILE.exists() else [])
    if loaded_satellites:
        satellites.clear()
        satellites.extend(loaded_satellites)
        metadata["source"] = "Local cache (download failed)"
        _write_metadata(metadata)
        print(f"Using last valid cached TLE data.Loaded {len(satellites)} satellites.")
        return True
    print("No valid cached TLE file is available; satellite acquisition failed.")
    return False

def calculate_risk(event, screening_threshold):
    Vref = 10
    distance_risk = 1 - (event["minimum_distance"] / screening_threshold)
    velocity_risk = event["relative_speed"] / Vref
    risk_factor = 100 * (0.7 * distance_risk + 0.3 * velocity_risk)
    risk_factor = max(0, min(100, risk_factor))
    if risk_factor < 30:
        risk_level = "Low"
    elif risk_factor < 60:
        risk_level = "Moderate"
    elif risk_factor < 80:
        risk_level = "High"
    else:
        risk_level = "Critical"
    return risk_factor, risk_level

def calculate_trajectory():
    if not satellite_file():
        print("Satellite acquisition failed. Stopping simulation.")
        return None
    trajectories = {}
    satellite_coordinates = []
    events = []
    relative_trajectory = []
    satellite_radius = 0.01
    collision_threshold = satellite_radius * 2
    screening_threshold = 1
    print("\n========== SGP4 TRAJECTORY ==========")
    time = datetime.now(timezone.utc)
    for i in range(len(satellites)):
        x_coordinates = []
        y_coordinates = []
        z_coordinates = []
        trajectory = generate_trajectory(time, satellites[i], 5401, 10)
        if not trajectory:
            print("Skipping the satellite due to trajectory failure")
            continue
        trajectories[satellites[i][0]] = trajectory
        for point in trajectory:
            x, y, z = point["position"]
            x_coordinates.append(x)
            y_coordinates.append(y)
            z_coordinates.append(z)
        satellite_coordinates.append({
            "satellite": satellites[i][0],
            "x_coordinates": x_coordinates,
            "y_coordinates": y_coordinates,
            "z_coordinates": z_coordinates
        })
    if len(trajectories) == 0:
        return None
    relative_trajectory = relative_motion(trajectories,len(next(iter(trajectories.values()))))
    satellite_pairs = {item["satellite_pair"] for item in relative_trajectory}
    for pair in satellite_pairs:
        distance = []
        record = []
        for item in relative_trajectory:
            if item["satellite_pair"] == pair:
                distance.append(item["distance"])
                record.append(item)
        if not distance:
            continue
        minimum_distance = min(distance)
        coarse_index = distance.index(minimum_distance)
        coarse_record = record[coarse_index]
        print(
            f"Satellites: {pair}\n"
            f"Minimum Distance: {coarse_record['distance']:.2f} km\n"
            f"Time: {coarse_record['time']}\n"
            f"Relative Speed: {coarse_record['relative_speed']:.2f} km/s\n"
        )
        refined_start = coarse_record["time"] - timedelta(seconds=10)
        satellite_first, satellite_second = pair.split(" <-> ")
        index_first = next((i for i, sat in enumerate(satellites) if sat[0] == satellite_first),None)
        index_second = next((i for i, sat in enumerate(satellites) if sat[0] == satellite_second),None)
        if index_first is None or index_second is None:
            continue
        trajectory_one = generate_trajectory(refined_start, satellites[index_first], 21, 1)
        trajectory_two = generate_trajectory(refined_start, satellites[index_second], 21, 1)
        if not trajectory_one or not trajectory_two:
            continue
        refined_relative_trajectory = []
        for step in range(21):
            p1 = trajectory_one[step]["position"]
            p2 = trajectory_two[step]["position"]
            v1 = trajectory_one[step]["velocity"]
            v2 = trajectory_two[step]["velocity"]
            relative_position = subtraction(p2, p1)
            relative_velocity = subtraction(v2, v1)
            refined_relative_trajectory.append({
                "time": trajectory_one[step]["time"],
                "relative_position": relative_position,
                "relative_velocity": relative_velocity,
                "distance": magnitude(relative_position),
                "relative_speed": magnitude(relative_velocity),
            })
        refined_distances = [point["distance"] for point in refined_relative_trajectory]
        refined_minimum = min(refined_distances)
        refined_index = refined_distances.index(refined_minimum)
        refined_record = refined_relative_trajectory[refined_index]
        if refined_record["distance"] > screening_threshold:
            classification = "No close approach"
        elif refined_record["distance"] >= collision_threshold:
            classification = "Close approach"
        else:
            classification = "Collision condition"
        event = {
            "satellite_pair": pair,
            "time": refined_record["time"],
            "minimum_distance": refined_record["distance"],
            "relative_speed": refined_record["relative_speed"],
            "classification": classification,
        }
        risk_score, risk_level = calculate_risk(event, screening_threshold)
        event["risk_score"] = risk_score
        event["risk_level"] = risk_level
        events.append(event)
    return trajectories, satellite_coordinates, relative_trajectory, events

def orbit_3d_plot(satellite_coordinates):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    colors = plt.cm.tab10.colors
    for i, satellite in enumerate(satellite_coordinates):
        name = satellite["satellite"]
        x = satellite["x_coordinates"]
        y = satellite["y_coordinates"]
        z = satellite["z_coordinates"]
        ax.plot3D(x, y, z, label=name,color=colors[i % len(colors)], linewidth=1.5)
        ax.scatter(x[0], y[0], z[0],color=colors[i % len(colors)],marker="o", s=50, label="_nolegend_")
    plot_earth(ax, earth_radius)
    ax.set_title("Satellite Trajectories Around Earth")
    ax.set_xlabel("X Position (km)")
    ax.set_ylabel("Y Position (km)")
    ax.set_zlabel("Z Position (km)")
    ax.legend()
    max_range = 0
    for satellite in satellite_coordinates:
        max_range = max(max_range,max(map(abs, satellite["x_coordinates"])),max(map(abs, satellite["y_coordinates"])),max(map(abs, satellite["z_coordinates"])))
    ax.set_xlim(-max_range, max_range)
    ax.set_ylim(-max_range, max_range)
    ax.set_zlim(-max_range, max_range)
    ax.set_box_aspect((1, 1, 1))
    plt.tight_layout()
    return fig

def altitude_plot(trajectories):
    fig, ax = plt.subplots(figsize=(10, 6))
    for satellite_name, trajectory in trajectories.items():
        times = [point["elapsed_seconds"] / 60 for point in trajectory]
        altitudes = [point["altitude"] for point in trajectory]
        ax.plot(times, altitudes, label=satellite_name)
    ax.set_title("Satellite Altitude vs Time")
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Altitude (km)")
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    return fig

def main():
    results = calculate_trajectory()
    if results is None:
        print("Could not calculate trajectories from available TLE data.")
        return
    trajectories, satellite_coordinates, relative_trajectory, events = results
    orbit_3d_plot(satellite_coordinates)
    altitude_plot(trajectories)
    test_snapshots()
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()