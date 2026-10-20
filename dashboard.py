import streamlit as st
import matplotlib.pyplot as plt
from sgp4_propagation import calculate_trajectory,altitude_plot,get_tle_status,satellites
from satellite_visualization import orbit_figure

def apply_space_theme():
    st.markdown(
        """
        <style>
        .stApp {
            background: #020817;
            color: #eaf4ff;
        }

        [data-testid="stHeader"] {
            background: rgba(2, 8, 23, 0.95);
        }

        .block-container {
            max-width: 1600px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3 {
            color: #eaf4ff !important;
        }

        p, label, [data-testid="stCaptionContainer"] {
            color: #b8d3f0;
        }

        [data-testid="stMetric"] {
            background: rgba(8, 24, 48, 0.9);
            border: 1px solid #164b7b;
            border-radius: 12px;
            padding: 12px;
        }

        [data-testid="stMetricLabel"] {
            color: #9dc9f6 !important;
        }

        [data-testid="stMetricValue"] {
            color: #f4f9ff !important;
        }

        .stButton > button {
            background: #135bd5;
            color: white;
            border: 1px solid #318bff;
            border-radius: 8px;
            min-height: 42px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def format_time(value):
    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M:%S")

def main():
    st.set_page_config(page_title="Satellite Trajectory Monitor",page_icon="🛰️",layout="wide",)
    apply_space_theme()
    st.title("🛰️ Satellite Trajectory Monitor")
    st.caption(
        "SGP4 orbit propagation | Close-approach screening | "
        "Interactive 3D satellite visualization"
    )
    with st.expander("About this project", expanded=False):
        st.write(
            "Satellite trajectories are propagated using SGP4 and TLE data. "
            "Pairwise separation is screened over a prediction window. "
            "Screening categories are heuristic scores, not probabilities "
            "of collision."
        )
    if "results" not in st.session_state:
        st.session_state.results = None
    button_col, info_col = st.columns([1, 3])
    with button_col:
        refresh = st.button("Refresh satellite data",type="primary",use_container_width=True,)
    with info_col:
        st.caption(
            "Downloads current TLE data when possible and falls back "
            "to the local cache when available."
        )
    if refresh:
        with st.spinner("Loading TLEs and calculating satellite trajectories..."):
            try:
                result = calculate_trajectory()
                if result is None:
                    st.error(
                        "Could not generate satellite trajectories. "
                        "Check TLE availability and the terminal output."
                    )
                else:
                    st.session_state.results = result
                    st.success("Satellite data processed successfully.")
            except Exception as exc:
                st.error(f"Unable to process satellite data: {exc}")
    status = get_tle_status()
    st.subheader("Data status")
    status1, status2, status3 = st.columns(3)
    status1.metric("TLE cache","Available" if status.get("cached") else "Unavailable",)
    status2.metric("Data source",status.get("source", "Unknown"),)
    status3.metric("Last successful download (UTC)",status.get("last_success_utc") or "Not recorded",)
    if status.get("last_message"):
        st.caption(status["last_message"])
    if status.get("last_attempt_utc"):
        st.caption(f"Last download attempt (UTC): {status['last_attempt_utc']}")
    if st.session_state.results is None:
        st.info(
            "Click **Refresh satellite data** to generate the orbit "
            "visualization and close-approach screening."
        )
        return
    trajectories, satellite_coordinates, relative_trajectory, events = (st.session_state.results)
    if not trajectories:
        st.error("No satellite trajectories are available.")
        return
    st.subheader("Satellite trajectories around Earth")
    orbit_fig = orbit_figure(satellite_coordinates)
    st.plotly_chart(orbit_fig, use_container_width=True,key="satellite_orbit_overview",)
    st.subheader("Altitude over time")
    altitude_fig = altitude_plot(trajectories)
    st.pyplot(altitude_fig,use_container_width=True,)
    plt.close(altitude_fig)
    close_events = [event for event in events if event.get("minimum_distance", float("inf")) <= 1.0]
    highest_risk = (max(events,key=lambda event: event.get("risk_score", 0),).get("risk_level", "None") if events else "None")
    st.subheader("Propagation summary")
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Satellites propagated",len(trajectories),)
    metric2.metric("Pairs screened",len(events),)
    metric3.metric("Pairs within 1 km",len(close_events),)
    metric4.metric("Highest screening category",highest_risk,)
    st.subheader("Satellite details")
    names = list(trajectories)
    selected_satellite = st.selectbox("Select a satellite",names,key="satellite_details_select",)
    latest = trajectories[selected_satellite][-1]
    detail1, detail2, detail3 = st.columns(3)
    detail1.metric("Latest altitude",f"{latest['altitude']:.2f} km",)
    detail2.metric("Latest speed",f"{latest['speed']:.3f} km/s",)
    detail3.metric("Latest state time (UTC)",latest["time"].strftime("%H:%M:%S"),)
    st.subheader("Close-approach screening")
    st.caption("Risk categories are based on the project's heuristic screening "
        "score; they are not probabilities of collision.")
    levels = ["Low", "Moderate", "High", "Critical"]
    risk_columns = st.columns(4)
    for column, level in zip(risk_columns, levels):
        count = sum(event.get("risk_level") == level for event in events)
        column.metric(level, count)
    show_all = st.checkbox(
        "Include pairs outside the 1 km screening threshold",
        value=False,
        key="show_all_events",
    )
    selected_levels = st.multiselect("Filter by screening category",levels,default=[],key="risk_level_filter",)
    displayed_events = (events if show_all else close_events)
    if selected_levels:
        displayed_events = [event for event in displayed_events if event.get("risk_level") in selected_levels]
    displayed_events = sorted(displayed_events,key=lambda event: event.get("minimum_distance",float("inf"),),)
    if displayed_events:
        table_rows = []
        for event in displayed_events:
            table_rows.append(
                {
                    "Satellite pair": event.get("satellite_pair", "Unknown"),
                    "Classification": event.get("classification", "Unknown"),
                    "Minimum separation (km)": round(event.get("minimum_distance", float("nan")),4,),
                    "TCA (UTC)": format_time(event.get("time")),
                    "Relative speed (km/s)": round(event.get("relative_speed", float("nan")),4,),
                    "Screening score": round(event.get("risk_score", 0),1,),
                    "Category": event.get("risk_level", "Unknown"),
                }
            )
        st.dataframe(table_rows,use_container_width=True,hide_index=True,)
    else:
        st.info("No events match the selected filters.")

if __name__ == "__main__":
    main()
