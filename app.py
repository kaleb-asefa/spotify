from __future__ import annotations

from pathlib import Path

import streamlit as st

from pages import (
    artist_song_analytics,
    behavior_analysis,
    listening_trends,
    machine_learning,
    overview,
    statistical_insights,
    time_pattern_intelligence,
)
from utils.loader import discover_json_files, load_spotify_data
from utils.preprocessing import apply_dashboard_filters, preprocess_listening_data


st.set_page_config(
    page_title="Spotify Personal Listening Analytics Dashboard",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root {
    --spotify-bg: #0e0e0e;
    --spotify-surface: #191414;
    --spotify-card: #1f1f1f;
    --spotify-green: #1DB954;
    --spotify-text: #f5f5f5;
    --spotify-muted: #b3b3b3;
}
.stApp {
    background: radial-gradient(circle at 15% 10%, #1d1d1d 0%, #0b0b0b 60%, #070707 100%);
    color: var(--spotify-text);
}
.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 1.2rem;
}
section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(29, 185, 84, 0.35);
    background: linear-gradient(180deg, #111111, #0f0f0f);
}
h1, h2, h3 {
    letter-spacing: 0.2px;
    color: var(--spotify-text);
}
div[data-testid="stMetric"] {
    background: linear-gradient(150deg, rgba(31,31,31,0.98), rgba(20,20,20,0.98));
    border: 1px solid rgba(29, 185, 84, 0.35);
    border-radius: 14px;
    padding: 0.35rem 0.55rem;
}
div[data-testid="stMetricLabel"] {
    color: var(--spotify-muted);
}
div[data-testid="stMetricValue"] {
    color: var(--spotify-text);
}
div.stButton > button {
    background: linear-gradient(120deg, #1DB954, #18a34a);
    color: #ffffff;
    border: none;
    border-radius: 999px;
    font-weight: 600;
}
div.stButton > button:hover {
    filter: brightness(1.05);
}
</style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def get_processed_data(data_path: str):
    raw = load_spotify_data(data_path)
    return preprocess_listening_data(raw)


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

st.sidebar.title("Spotify Dashboard")
st.sidebar.caption("Portfolio-grade personal listening analytics")

json_files = discover_json_files(DATA_DIR)
if not json_files:
    st.warning(
        "No Spotify JSON exports found. Place one or more JSON files inside the data/ folder and refresh."
    )
    st.stop()

pack = get_processed_data(str(DATA_DIR))
full_df = pack["full"]

if full_df.empty:
    st.warning("Data was loaded but no valid timestamped rows were found.")
    st.stop()

min_date = full_df["date"].min()
max_date = full_df["date"].max()

selected_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(selected_range, tuple) and len(selected_range) == 2:
    start_date, end_date = selected_range
else:
    start_date, end_date = min_date, max_date

artist_options = sorted(full_df["master_metadata_album_artist_name"].dropna().unique().tolist())
selected_artists = st.sidebar.multiselect(
    "Artists",
    options=artist_options,
    default=[],
    help="Optional filter: leave empty to include all artists.",
)

content_types = st.sidebar.multiselect(
    "Content types",
    options=["Songs", "Podcasts", "Audiobooks"],
    default=["Songs", "Podcasts", "Audiobooks"],
)

filtered_df = apply_dashboard_filters(
    full_df,
    start_date=start_date,
    end_date=end_date,
    artists=selected_artists,
    content_types=content_types,
)

st.sidebar.markdown("---")
st.sidebar.write(f"Loaded files: {len(json_files)}")
st.sidebar.write(f"Rows after filters: {len(filtered_df):,}")

page = st.sidebar.radio(
    "Navigate",
    options=[
        "Executive Overview",
        "Listening Trends",
        "Artist & Song Analytics",
        "Listening Behavior Analysis",
        "Time Pattern Intelligence",
        "Statistical Insight Section",
        "Machine Learning",
    ],
)

if page == "Executive Overview":
    overview.render(filtered_df)
elif page == "Listening Trends":
    listening_trends.render(filtered_df)
elif page == "Artist & Song Analytics":
    artist_song_analytics.render(filtered_df)
elif page == "Listening Behavior Analysis":
    behavior_analysis.render(filtered_df)
elif page == "Time Pattern Intelligence":
    time_pattern_intelligence.render(filtered_df)
elif page == "Statistical Insight Section":
    statistical_insights.render(filtered_df)
elif page == "Machine Learning":
    machine_learning.render(filtered_df)
