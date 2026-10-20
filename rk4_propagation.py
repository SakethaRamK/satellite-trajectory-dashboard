import math
import satellite_orbit
def state_derivative(r, v):
    acc = satellite_orbit.grav_acc(r)
    return v + acc

def intermediate_state(r, v, k, dt, fraction):
    r_temp = []
    v_temp = []
    for i in range(len(r)):
        r_temp.append(r[i] + (k[i] * dt * fraction))
        v_temp.append(v[i] + (k[i + 3] * dt * fraction))
    return r_temp, v_temp

def rk4_step(r, v, dt):
    r_new = []
    v_new = []
    k1 = state_derivative(r, v)
    r2, v2 = intermediate_state(r, v, k1, dt, 1 / 2)
    k2 = state_derivative(r2, v2)
    r3, v3 = intermediate_state(r, v, k2, dt, 1 / 2)
    k3 = state_derivative(r3, v3)
    r4, v4 = intermediate_state(r, v, k3, dt, 1)
    k4 = state_derivative(r4, v4)
    for i in range(len(r)):
        r_new.append(
            r[i] + (dt / 6) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])
        )
        v_new.append(
            v[i] + (dt / 6) * (k1[i + 3] + 2 * k2[i + 3] + 2 * k3[i + 3] + k4[i + 3])
        )
    return r_new, v_new

def rk4_propagate(r, v, dt, steps):
    trajectory = []
    new_position = r
    new_velocity = v
    trajectory.append({
        "time": 0,
        "position": new_position,
        "velocity": new_velocity,
        "distance": satellite_orbit.magnitude(new_position),
        "speed": satellite_orbit.magnitude(new_velocity)
    })
    for i in range(1, steps + 1):
        new_position, new_velocity = rk4_step(
            new_position,
            new_velocity,
            dt
        )
        trajectory.append({
            "time": i * dt,
            "position": new_position,
            "velocity": new_velocity,
            "distance": satellite_orbit.magnitude(new_position),
            "speed": satellite_orbit.magnitude(new_velocity)
        })
    return trajectory

def analyze_trajectory(trajectory):
    distances = [point["distance"] for point in trajectory]
    speeds = [point["speed"] for point in trajectory]
    analysis = {
        "minimum_distance": min(distances),
        "maximum_distance": max(distances),
        "minimum_speed": min(speeds),
        "maximum_speed": max(speeds)
    }
    return analysis

def main():
    r = [7000, 0, 0]
    v = [
        0,
        math.sqrt(satellite_orbit.mu / 7000),
        0
    ]
    propagation_time = 1800
    dt = 10
    steps = int(propagation_time / dt)
    trajectory = rk4_propagate(
        r,
        v,
        dt,
        steps
    )
    analysis = analyze_trajectory(trajectory)
    final_state = trajectory[-1]
    print("========== RK4 TRAJECTORY ANALYSIS ==========")
    print(f"Propagation time: {propagation_time} s")
    print(f"Time step: {dt} s")
    print(f"Trajectory points: {len(trajectory)}")
    print(f"\nInitial distance: {trajectory[0]['distance']:.6f} km")
    print(f"Final distance: {final_state['distance']:.6f} km")
    print(f"\nMinimum distance: {analysis['minimum_distance']:.6f} km")
    print(f"Maximum distance: {analysis['maximum_distance']:.6f} km")
    print(f"\nInitial speed: {trajectory[0]['speed']:.6f} km/s")
    print(f"Final speed: {final_state['speed']:.6f} km/s")
    print(f"\nMinimum speed: {analysis['minimum_speed']:.6f} km/s")
    print(f"Maximum speed: {analysis['maximum_speed']:.6f} km/s")
    print("\n========== FINAL STATE ==========")
    print(f"Time: {final_state['time']} s")
    print(f"Position: {final_state['position']}")
    print(f"Velocity: {final_state['velocity']}")

if __name__ == "__main__":
    main()