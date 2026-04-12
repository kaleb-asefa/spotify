from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.spotify_api import (
    fetch_cover_image,
    get_album_metadata,
    get_artist_metadata,
    get_track_metadata,
)
from utils.stats import artist_diversity_score


SPOTIFY_CARD_CSS = """
<style>
.spotify-section-title {
    color: #FFFFFF;
    font-weight: 700;
    margin-top: 0.4rem;
    margin-bottom: 0.6rem;
}
.spotify-card {
    background: linear-gradient(160deg, rgba(32,32,32,0.98), rgba(18,18,18,0.98));
    border-radius: 16px;
    padding: 0.9rem;
    border: 1px solid rgba(29, 185, 84, 0.35);
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    margin-bottom: 0.8rem;
}
.spotify-card h4 {
    color: #FFFFFF;
    margin-bottom: 0.2rem;
}
.spotify-card p, .spotify-card li {
    color: #D7D7D7;
    margin: 0;
    line-height: 1.35;
}
.spotify-pill {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    background: rgba(29, 185, 84, 0.25);
    color: #D9FFE8;
    font-size: 0.8rem;
    margin-right: 0.3rem;
    margin-bottom: 0.3rem;
}
.hero-title {
    font-size: 1.15rem;
    color: #FFFFFF;
    font-weight: 700;
}
.hero-subtitle {
    color: #A9F4C2;
    font-size: 0.92rem;
}
</style>
"""


def _format_minutes_to_hours(minutes: float) -> str:
    if minutes < 60:
        return f"{minutes:.1f} min"
    return f"{minutes / 60:.1f} h"


def _render_featured_track(songs: pd.DataFrame):
    st.markdown('<h3 class="spotify-section-title">Featured Song Obsession</h3>', unsafe_allow_html=True)

    top_track_row = (
        songs.groupby(["master_metadata_track_name", "master_metadata_album_artist_name", "master_metadata_album_album_name"], as_index=False)
        .agg(
            streams=("master_metadata_track_name", "count"),
            listening_minutes=("play_minutes", "sum"),
            first_play=("ts", "min"),
            last_play=("ts", "max"),
            spotify_track_uri=("spotify_track_uri", "first"),
        )
        .sort_values(["streams", "listening_minutes"], ascending=False)
        .head(1)
    )

    if top_track_row.empty:
        st.info("No featured track data available.")
        return

    row = top_track_row.iloc[0]
    track_meta = get_track_metadata(
        track_uri=row["spotify_track_uri"],
        track_name=row["master_metadata_track_name"],
        artist_name=row["master_metadata_album_artist_name"],
    )

    image_url = fetch_cover_image(track_meta.get("album_image"))

    left, right = st.columns([1, 2])
    with left:
        if image_url:
            st.image(image_url, use_container_width=True)
        else:
            st.image("https://placehold.co/600x600/1a1a1a/ffffff?text=No+Cover", use_container_width=True)

    with right:
        st.markdown('<div class="spotify-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="hero-title">{row["master_metadata_track_name"]}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="hero-subtitle">{row["master_metadata_album_artist_name"]} • {row["master_metadata_album_album_name"]}</div>',
            unsafe_allow_html=True,
        )
        st.write("")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Streams", f"{int(row['streams']):,}")
        c2.metric("Listening Time", _format_minutes_to_hours(float(row["listening_minutes"])))
        c3.metric("Popularity", str(track_meta.get("popularity") or "N/A"))

        first_play = pd.to_datetime(row["first_play"]).strftime("%Y-%m-%d")
        last_play = pd.to_datetime(row["last_play"]).strftime("%Y-%m-%d")
        st.write(f"First played: {first_play}")
        st.write(f"Most recent play: {last_play}")

        release_date = track_meta.get("album_release_date")
        if release_date:
            st.write(f"Album release: {release_date}")

        if track_meta.get("external_url"):
            st.link_button("Open Track on Spotify", track_meta["external_url"])

        st.markdown("</div>", unsafe_allow_html=True)


def _render_top_albums_spotlight(songs: pd.DataFrame):
    st.markdown('<h3 class="spotify-section-title">Top Albums Spotlight</h3>', unsafe_allow_html=True)

    top_albums = (
        songs.groupby(["master_metadata_album_album_name", "master_metadata_album_artist_name"], as_index=False)
        .agg(play_count=("master_metadata_track_name", "count"), play_minutes=("play_minutes", "sum"))
        .sort_values(["play_count", "play_minutes"], ascending=False)
        .head(8)
    )

    if top_albums.empty:
        st.info("No album data available.")
        return

    for row_start in range(0, len(top_albums), 4):
        cols = st.columns(4)
        chunk = top_albums.iloc[row_start : row_start + 4]
        for i, (_, album_row) in enumerate(chunk.iterrows()):
            album_meta = get_album_metadata(
                album_name=album_row["master_metadata_album_album_name"],
                artist_name=album_row["master_metadata_album_artist_name"],
            )
            image = fetch_cover_image(album_meta.get("image"))
            with cols[i]:
                st.markdown('<div class="spotify-card">', unsafe_allow_html=True)
                if image:
                    st.image(image, use_container_width=True)
                else:
                    st.image("https://placehold.co/500x500/1a1a1a/ffffff?text=Album", use_container_width=True)
                st.markdown(f"**{album_row['master_metadata_album_album_name']}**")
                st.caption(album_row["master_metadata_album_artist_name"])
                st.write(f"Plays: {int(album_row['play_count']):,}")
                st.write(f"Listening: {_format_minutes_to_hours(float(album_row['play_minutes']))}")
                if album_meta.get("release_date"):
                    st.write(f"Released: {album_meta['release_date']}")
                if album_meta.get("external_url"):
                    st.link_button("Open Album", album_meta["external_url"])
                st.markdown("</div>", unsafe_allow_html=True)


def _render_artist_spotlight(songs: pd.DataFrame):
    st.markdown('<h3 class="spotify-section-title">Artist Spotlight</h3>', unsafe_allow_html=True)

    top_artists = (
        songs.groupby("master_metadata_album_artist_name", as_index=False)
        .agg(total_plays=("master_metadata_track_name", "count"), total_minutes=("play_minutes", "sum"))
        .sort_values(["total_plays", "total_minutes"], ascending=False)
        .head(5)
    )

    if top_artists.empty:
        st.info("No artist data available.")
        return

    total_plays_all = max(int(songs.shape[0]), 1)
    cols = st.columns(5)

    for idx, (_, row) in enumerate(top_artists.iterrows()):
        artist_meta = get_artist_metadata(row["master_metadata_album_artist_name"])
        genres = artist_meta.get("genres") or []
        image = fetch_cover_image(artist_meta.get("image"))

        with cols[idx]:
            st.markdown('<div class="spotify-card">', unsafe_allow_html=True)
            if image:
                st.image(image, use_container_width=True)
            else:
                st.image("https://placehold.co/500x500/1a1a1a/ffffff?text=Artist", use_container_width=True)

            st.markdown(f"**{row['master_metadata_album_artist_name']}**")
            st.write(f"Plays: {int(row['total_plays']):,}")
            share = 100 * row["total_plays"] / total_plays_all
            st.write(f"Share: {share:.1f}%")
            st.write(f"Popularity: {artist_meta.get('popularity') or 'N/A'}")

            if genres:
                shown = genres[:3]
                genres_html = "".join([f'<span class="spotify-pill">{g}</span>' for g in shown])
                st.markdown(genres_html, unsafe_allow_html=True)

            if artist_meta.get("external_url"):
                st.link_button("Open Artist", artist_meta["external_url"])
            st.markdown("</div>", unsafe_allow_html=True)


def _render_wrapped_insights(songs: pd.DataFrame):
    st.markdown('<h3 class="spotify-section-title">Spotify Wrapped Style Insights</h3>', unsafe_allow_html=True)

    songs_local = songs.copy()
    songs_local["hour"] = songs_local["ts"].dt.hour
    songs_local["is_weekend"] = songs_local["ts"].dt.weekday >= 5
    songs_local["year"] = songs_local["ts"].dt.year

    late_night = songs_local[songs_local["hour"].between(0, 4)]
    late_night_track = (
        late_night.groupby("master_metadata_track_name", as_index=False)
        .size()
        .rename(columns={"size": "plays"})
        .sort_values("plays", ascending=False)
        .head(1)
    )

    most_replayed_artist = (
        songs_local.groupby("master_metadata_album_artist_name", as_index=False)
        .size()
        .rename(columns={"size": "plays"})
        .sort_values("plays", ascending=False)
        .head(1)
    )

    weekend_anthem = (
        songs_local[songs_local["is_weekend"]]
        .groupby("master_metadata_track_name", as_index=False)
        .size()
        .rename(columns={"size": "plays"})
        .sort_values("plays", ascending=False)
        .head(1)
    )

    current_year = int(songs_local["year"].max())
    top_artist_year = (
        songs_local[songs_local["year"] == current_year]
        .groupby("master_metadata_album_artist_name", as_index=False)
        .size()
        .rename(columns={"size": "plays"})
        .sort_values("plays", ascending=False)
        .head(1)
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown('<div class="spotify-card">', unsafe_allow_html=True)
        if late_night_track.empty:
            st.write("Your late-night obsession: N/A")
        else:
            st.write(f"Your late-night obsession: {late_night_track.iloc[0]['master_metadata_track_name']}")
            st.write(f"Night plays: {int(late_night_track.iloc[0]['plays'])}")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="spotify-card">', unsafe_allow_html=True)
        if most_replayed_artist.empty:
            st.write("Most replayed artist: N/A")
        else:
            artist_name = most_replayed_artist.iloc[0]["master_metadata_album_artist_name"]
            st.write(f"Most replayed artist: {artist_name}")
            st.write(f"Plays: {int(most_replayed_artist.iloc[0]['plays'])}")
            artist_meta = get_artist_metadata(artist_name)
            if artist_meta.get("image"):
                st.image(artist_meta["image"], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="spotify-card">', unsafe_allow_html=True)
        if weekend_anthem.empty:
            st.write("Weekend anthem: N/A")
        else:
            st.write(f"Weekend anthem: {weekend_anthem.iloc[0]['master_metadata_track_name']}")
            st.write(f"Weekend plays: {int(weekend_anthem.iloc[0]['plays'])}")
        st.markdown("</div>", unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="spotify-card">', unsafe_allow_html=True)
        if top_artist_year.empty:
            st.write("Your top artist this year: N/A")
        else:
            artist_name = top_artist_year.iloc[0]["master_metadata_album_artist_name"]
            st.write(f"Your top artist this year: {artist_name}")
            st.write(f"{current_year} plays: {int(top_artist_year.iloc[0]['plays'])}")
        st.markdown("</div>", unsafe_allow_html=True)


def _render_classic_tables(songs: pd.DataFrame, top_n: int):
    top_artists = (
        songs.groupby("master_metadata_album_artist_name", as_index=False)
        .agg(plays=("master_metadata_track_name", "count"), hours=("play_hours", "sum"))
        .sort_values("plays", ascending=False)
        .head(top_n)
    )

    top_tracks = (
        songs.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"], as_index=False)
        .agg(plays=("master_metadata_track_name", "count"), hours=("play_hours", "sum"))
        .sort_values("plays", ascending=False)
        .head(top_n)
    )

    top_albums = (
        songs.groupby("master_metadata_album_album_name", as_index=False)
        .agg(plays=("master_metadata_track_name", "count"), hours=("play_hours", "sum"))
        .sort_values("plays", ascending=False)
        .head(top_n)
    )

    repeated_tracks = (
        songs.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"], as_index=False)
        .size()
        .rename(columns={"size": "play_count"})
        .query("play_count >= 5")
        .sort_values("play_count", ascending=False)
    )

    tab1, tab2, tab3, tab4 = st.tabs(["Top Artists", "Top Tracks", "Top Albums", "Repeated Listening"])

    with tab1:
        fig = px.bar(
            top_artists,
            x="master_metadata_album_artist_name",
            y="plays",
            color="hours",
            template="plotly_dark",
            title=f"Top {top_n} Artists by Plays",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top_artists.sort_values("plays", ascending=False), use_container_width=True)

    with tab2:
        top_tracks = top_tracks.copy()
        top_tracks["label"] = top_tracks["master_metadata_track_name"] + " - " + top_tracks["master_metadata_album_artist_name"]
        fig = px.bar(
            top_tracks,
            x="label",
            y="plays",
            color="hours",
            template="plotly_dark",
            title=f"Top {top_n} Tracks",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top_tracks.drop(columns=["label"]), use_container_width=True)

    with tab3:
        fig = px.bar(
            top_albums,
            x="master_metadata_album_album_name",
            y="plays",
            color="hours",
            template="plotly_dark",
            title=f"Top {top_n} Albums",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top_albums, use_container_width=True)

    with tab4:
        st.dataframe(repeated_tracks, use_container_width=True)
        st.caption("Tracks with at least 5 plays are highlighted as repeated listening patterns.")


def render(df: pd.DataFrame):
    st.title("Artist and Song Analytics")
    st.markdown(SPOTIFY_CARD_CSS, unsafe_allow_html=True)

    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    songs = df[df["is_song"]].copy()
    if songs.empty:
        st.warning("No song records found in selected filters.")
        return

    st.caption("Tip: set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in Streamlit secrets or environment variables to enable rich metadata.")

    diversity = artist_diversity_score(songs)
    st.metric("Artist Diversity Score (Simpson Index)", f"{diversity:.3f}")

    _render_featured_track(songs)
    _render_top_albums_spotlight(songs)
    _render_artist_spotlight(songs)
    _render_wrapped_insights(songs)

    st.markdown("---")
    top_n = st.selectbox("Select ranking depth", options=[10, 20], index=0)
    _render_classic_tables(songs, top_n)
