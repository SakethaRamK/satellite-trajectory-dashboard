from datetime import timedelta, timezone
from pathlib import Path
import numpy as np
import plotly.graph_objects as go
from PIL import Image
from sgp4.api import Satrec, jday
EARTH_RADIUS_KM = 6371.0
PROJECT_DIR = Path("C:/Projects/Satellite")
EARTH_TEXTURE = PROJECT_DIR / "earth_texture.jpg"
SPACE_BG = "#020817"
TEXT_COLOR = "#eaf4ff"
GRID_COLOR = "rgba(65, 140, 210, 0.20)"
ORBIT_COLORS = [
    "#ffb000",
    "#ff5c5c",
    "#57d6a1",
    "#c49aff",
    "#55c8ff",
    "#ff8ec7",
    "#d8e56a",
    "#f5f5f5",
]

def propagate_position(tle_record, timestamp):
    name, line1, line2 = tle_record
    satellite = Satrec.twoline2rv(line1, line2)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    else:
        timestamp = timestamp.astimezone(timezone.utc)
    jd, fr = jday(
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour,
        timestamp.minute,
        timestamp.second + timestamp.microsecond / 1_000_000,
    )
    error, position, velocity = satellite.sgp4(jd, fr)
    if error != 0:
        raise RuntimeError(f"SGP4 propagation failed for {name}: error {error}")
    return (np.asarray(position, dtype=float),np.asarray(velocity, dtype=float),)

def add_starfield(fig, extent_km=15000, count=450, seed=17):
    rng = np.random.default_rng(seed)
    directions = rng.normal(size=(count, 3))
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    radii = rng.uniform(extent_km * 0.86, extent_km, size=count)
    points = directions * radii[:, None]
    sizes = rng.choice([1, 1.5, 2],size=count,p=[0.72, 0.23, 0.05],)
    colours = rng.choice(["#739bc5", "#b9dcff", "#ffffff"],size=count,p=[0.45, 0.40, 0.15],)
    fig.add_trace(
        go.Scatter3d(
            x=points[:, 0],
            y=points[:, 1],
            z=points[:, 2],
            mode="markers",
            name="Starfield",
            marker=dict(size=sizes,color=colours,opacity=0.85,),
            hoverinfo="skip",
            showlegend=False,
        )
    )

def earth_mesh():
    from PIL import Image
    import numpy as np
    import plotly.graph_objects as go
    n_lat, n_lon = 100, 200
    lat = np.linspace(-np.pi / 2, np.pi / 2, n_lat)
    lon = np.linspace(-np.pi, np.pi, n_lon)
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    r = EARTH_RADIUS_KM
    x = r * np.cos(lat_grid) * np.cos(lon_grid)
    y = r * np.cos(lat_grid) * np.sin(lon_grid)
    z = r * np.sin(lat_grid)
    try:
        img = Image.open(EARTH_TEXTURE).convert("RGB")
        img = img.resize((n_lon, n_lat), Image.Resampling.BILINEAR)
        pixels = np.asarray(img)
        pixels = np.flipud(pixels)
        vertex_colors = [f"rgb({int(c[0])},{int(c[1])},{int(c[2])})" for c in pixels.reshape(-1, 3)]
    except Exception:
        vertex_colors = ["rgb(30,100,160)"] * (n_lat * n_lon)
    ii, jj, kk = [], [], []
    for i in range(n_lat - 1):
        for j in range(n_lon - 1):
            a = i * n_lon + j
            b = a + 1
            c = a + n_lon
            d = c + 1
            ii.extend([a, a])
            jj.extend([b, d])
            kk.extend([c, c])
    return go.Mesh3d(
        x=x.ravel(),
        y=y.ravel(),
        z=z.ravel(),
        i=ii,
        j=jj,
        k=kk,
        vertexcolor=vertex_colors,
        opacity=1.0,
        flatshading=False,
        name="Earth",
        hoverinfo="skip",
        showscale=False,
    )
def earth_grid():
    traces = []
    radius = EARTH_RADIUS_KM * 1.003
    for latitude_deg in range(-75, 76, 15):
        latitude = np.radians(latitude_deg)
        longitude = np.linspace(-np.pi, np.pi, 150)
        x = radius * np.cos(latitude) * np.cos(longitude)
        y = radius * np.cos(latitude) * np.sin(longitude)
        z = np.full_like(longitude, radius * np.sin(latitude))
        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(color="rgba(140, 205, 255, 0.22)",width=1,),
                hoverinfo="skip",
                showlegend=False,
                name="Latitude grid",
            )
        )
    for longitude_deg in range(-180, 181, 30):
        longitude = np.radians(longitude_deg)
        latitude = np.linspace(-np.pi / 2, np.pi / 2, 120)
        x = radius * np.cos(latitude) * np.cos(longitude)
        y = radius * np.cos(latitude) * np.sin(longitude)
        z = radius * np.sin(latitude)
        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(color="rgba(140, 205, 255, 0.22)",width=1,),
                hoverinfo="skip",
                showlegend=False,
                name="Longitude grid",
            )
        )
    return traces

def style_3d_scene(fig,extent_km,title,camera=None,height=750,):
    axis_style = dict(
        showbackground=False,
        showgrid=True,
        gridcolor=GRID_COLOR,
        zerolinecolor="rgba(65, 140, 210, 0.30)",
        color="#9dc9f6",
        showspikes=False,
    )
    scene = dict(
        xaxis=dict(
            title="X (km)",
            range=[-extent_km, extent_km],
            **axis_style,
        ),
        yaxis=dict(
            title="Y (km)",
            range=[-extent_km, extent_km],
            **axis_style,
        ),
        zaxis=dict(
            title="Z (km)",
            range=[-extent_km, extent_km],
            **axis_style,
        ),
        aspectmode="cube",
        bgcolor=SPACE_BG,
        uirevision="satellite-space-camera",
        camera=camera or dict(
            eye=dict(x=1.65, y=1.65, z=1.25)
        ),
    )
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=0, r=0, t=65, b=25),
        paper_bgcolor=SPACE_BG,
        plot_bgcolor=SPACE_BG,
        font=dict(family="Arial, sans-serif",color=TEXT_COLOR,size=12,),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            bgcolor="rgba(2, 8, 23, 0.55)",
        ),
        scene=scene,
        uirevision="satellite-space-figure",
    )
    return fig

def orbit_figure(satellite_coordinates):
    fig = go.Figure()
    max_range = EARTH_RADIUS_KM * 1.5
    for satellite in satellite_coordinates:
        for axis in ("x_coordinates","y_coordinates","z_coordinates",):
            values = satellite.get(axis, [])
            if values:
                max_range = max(max_range,max(abs(value) for value in values),)
    extent_km = max_range * 1.12
    add_starfield(fig,extent_km=extent_km,count=450,seed=17,)
    fig.add_trace(earth_mesh())
    for trace in earth_grid():
        fig.add_trace(trace)
    for index, satellite in enumerate(satellite_coordinates):
        colour = ORBIT_COLORS[index % len(ORBIT_COLORS)]
        name = satellite["satellite"]
        x = satellite["x_coordinates"]
        y = satellite["y_coordinates"]
        z = satellite["z_coordinates"]
        if not x or not y or not z:
            continue
        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                name=name,
                line=dict(color=colour, width=3),
                hovertemplate=(
                    f"<b>{name}</b><br>X: %{{x:.1f}} km"
                    "<br>Y: %{y:.1f} km"
                    "<br>Z: %{z:.1f} km<extra></extra>"
                ),
            )
        )
        fig.add_trace(
            go.Scatter3d(
                x=[x[0]],
                y=[y[0]],
                z=[z[0]],
                mode="markers",
                marker=dict(size=5,color=colour,line=dict(color="#ffffff", width=1),),
                name=f"{name} position",
                showlegend=False,
                hoverinfo="skip",
            )
        )
    style_3d_scene(fig,extent_km=extent_km,title="Satellite Trajectories Around Earth",height=700,)
    return fig

def pair_animation_figure(first_tle,second_tle,tca,window_minutes=30,step_seconds=10,):
    from datetime import timedelta, timezone
    import numpy as np
    import plotly.graph_objects as go
    if window_minutes <= 0:
        raise ValueError("Animation window must be positive.")
    if step_seconds <= 0:
        raise ValueError("Frame interval must be positive.")
    if tca.tzinfo is None:
        tca = tca.replace(tzinfo=timezone.utc)
    else:
        tca = tca.astimezone(timezone.utc)
    start_time = tca - timedelta(minutes=window_minutes)
    end_time = tca + timedelta(minutes=window_minutes)
    times = []
    current_time = start_time
    while current_time <= end_time:
        times.append(current_time)
        current_time += timedelta(seconds=step_seconds)
    if times[-1] < end_time:
        times.append(end_time)
    positions_a = []
    positions_b = []
    velocities_a = []
    velocities_b = []
    distances = []
    relative_speeds = []
    for timestamp in times:
        position_a, velocity_a = propagate_position(first_tle, timestamp)
        position_b, velocity_b = propagate_position(second_tle, timestamp)
        position_a = np.asarray(position_a, dtype=float)
        position_b = np.asarray(position_b, dtype=float)
        velocity_a = np.asarray(velocity_a, dtype=float)
        velocity_b = np.asarray(velocity_b, dtype=float)
        positions_a.append(position_a)
        positions_b.append(position_b)
        velocities_a.append(velocity_a)
        velocities_b.append(velocity_b)
        distances.append(float(np.linalg.norm(position_b - position_a)))
        relative_speeds.append(
            float(np.linalg.norm(velocity_b - velocity_a))
        )
    positions_a = np.asarray(positions_a)
    positions_b = np.asarray(positions_b)
    fig = go.Figure()
    fig.add_trace(add_starfield())
    fig.add_trace(earth_mesh())
    for grid_trace in earth_grid():
        fig.add_trace(grid_trace)
    fig.add_trace(
        go.Scatter3d(
            x=positions_a[:, 0],
            y=positions_a[:, 1],
            z=positions_a[:, 2],
            mode="lines",
            line=dict(color="#ffbd45", width=4),
            name=f"{first_tle[0]} trajectory",
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=positions_b[:, 0],
            y=positions_b[:, 1],
            z=positions_b[:, 2],
            mode="lines",
            line=dict(color="#42d9ff", width=4),
            name=f"{second_tle[0]} trajectory",
            hoverinfo="skip",
        )
    )
    marker_a_index = len(fig.data)
    fig.add_trace(
        go.Scatter3d(
            x=[positions_a[0, 0]],
            y=[positions_a[0, 1]],
            z=[positions_a[0, 2]],
            mode="markers+text",
            marker=dict(
                size=8,
                color="#ffbd45",
                line=dict(color="white", width=1.5),
            ),
            text=[first_tle[0]],
            textposition="top center",
            name=first_tle[0],
        )
    )
    marker_b_index = len(fig.data)
    fig.add_trace(
        go.Scatter3d(
            x=[positions_b[0, 0]],
            y=[positions_b[0, 1]],
            z=[positions_b[0, 2]],
            mode="markers+text",
            marker=dict(
                size=8,
                color="#42d9ff",
                line=dict(color="white", width=1.5),
            ),
            text=[second_tle[0]],
            textposition="bottom center",
            name=second_tle[0],
        )
    )
    connector_index = len(fig.data)
    fig.add_trace(
        go.Scatter3d(
            x=[positions_a[0, 0], positions_b[0, 0]],
            y=[positions_a[0, 1], positions_b[0, 1]],
            z=[positions_a[0, 2], positions_b[0, 2]],
            mode="lines",
            line=dict(color="white", width=5),
            name="Current separation",
            hoverinfo="skip",
        )
    )
    def frame_title(index):
        return (
            f"{first_tle[0]} ↔ {second_tle[0]}"
            f" | {times[index]:%Y-%m-%d %H:%M:%S} UTC"
            f" | Separation: {distances[index]:.3f} km"
            f" | Relative speed: {relative_speeds[index]:.3f} km/s"
        )
    frames = []
    for i, timestamp in enumerate(times):
        frames.append(
            go.Frame(
                name=str(i),
                data=[
                    go.Scatter3d(
                        x=[positions_a[i, 0]],
                        y=[positions_a[i, 1]],
                        z=[positions_a[i, 2]],
                        text=[first_tle[0]],
                    ),
                    go.Scatter3d(
                        x=[positions_b[i, 0]],
                        y=[positions_b[i, 1]],
                        z=[positions_b[i, 2]],
                        text=[second_tle[0]],
                    ),
                    go.Scatter3d(
                        x=[positions_a[i, 0], positions_b[i, 0]],
                        y=[positions_a[i, 1], positions_b[i, 1]],
                        z=[positions_a[i, 2], positions_b[i, 2]],
                    ),
                ],
                traces=[marker_a_index,marker_b_index,connector_index,
                ],
                layout=go.Layout(title_text=frame_title(i)),
            )
        )
    fig.frames = frames
    slider_steps = []
    for i, timestamp in enumerate(times):
        slider_steps.append(
            dict(
                method="animate",
                label=timestamp.strftime("%H:%M:%S"),
                args=[
                    [str(i)],
                    dict(mode="immediate",frame=dict(duration=0, redraw=True),transition=dict(duration=0),),
                ],
            )
        )
    fig.update_layout(
        title=dict(
            text=frame_title(0),
            x=0.02,
            font=dict(size=15),
        ),
        paper_bgcolor="#020817",
        plot_bgcolor="#020817",
        font=dict(color="#dcecff"),
        height=760,
        margin=dict(l=0, r=0, t=100, b=100),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,x=0,font=dict(size=10)),
        scene=dict(
            aspectmode="data",
            bgcolor="#020817",
            xaxis=dict(title="TEME X (km)", showbackground=False),
            yaxis=dict(title="TEME Y (km)", showbackground=False),
            zaxis=dict(title="TEME Z (km)", showbackground=False),
        ),
        uirevision="pair-animation-camera",
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.02,
                y=0.02,
                xanchor="left",
                yanchor="bottom",
                showactive=False,
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[
                            None,
                            dict(
                                fromcurrent=True,
                                mode="immediate",
                                frame=dict(duration=150,redraw=True,),
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                    dict(
                        label="❚❚ Pause",
                        method="animate",
                        args=[
                            [None],
                            dict(mode="immediate",frame=dict(duration=0, redraw=True),transition=dict(duration=0),),
                        ],
                    ),
                ],
            )
        ],
        sliders=[dict(active=0,x=0.18,y=0.02,len=0.79,currentvalue=dict(prefix="Time: "),steps=slider_steps,)],
    )
    minimum_index = int(np.argmin(distances))
    summary = {
        "times": times,
        "distances": distances,
        "relative_speeds": relative_speeds,
        "minimum_distance": distances[minimum_index],
        "minimum_time": times[minimum_index],
        "closest_relative_speed": relative_speeds[minimum_index],
    }
    return fig, summary

if __name__ == "__main__":
    print("Satellite visualization module loaded.")
    print(f"Earth texture available: {EARTH_TEXTURE.exists()}")
