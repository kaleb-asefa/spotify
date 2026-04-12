from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st



def render(df: pd.DataFrame):
    st.title("Executive Overview")

    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    total_hours = df["play_hours"].sum()
    total_tracks = int(df["is_song"].sum())
    unique_artists = int(df["master_metadata_album_artist_name"].nunique())
    unique_albums = int(df["master_metadata_album_album_name"].nunique())
    skip_rate = float(df["is_skipped"].mean() * 100)
    shuffle_rate = float(df["shuffle"].mean() * 100)

    hour_activity = df.groupby("listening_hour", as_index=False)["play_hours"].sum()
    day_activity = df.groupby("weekday_name", as_index=False)["play_hours"].sum()

    most_active_hour = int(hour_activity.sort_values("play_hours", ascending=False).iloc[0]["listening_hour"])
    most_active_day = str(day_activity.sort_values("play_hours", ascending=False).iloc[0]["weekday_name"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Listening Hours", f"{total_hours:,.1f}")
    c2.metric("Total Tracks Played", f"{total_tracks:,}")
    c3.metric("Unique Artists", f"{unique_artists:,}")
    c4.metric("Unique Albums", f"{unique_albums:,}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Skip Rate", f"{skip_rate:.1f}%")
    c6.metric("Shuffle Usage", f"{shuffle_rate:.1f}%")
    c7.metric("Most Active Hour", f"{most_active_hour:02d}:00")
    c8.metric("Most Active Day", most_active_day)

    col_left, col_right = st.columns(2)

    with col_left:
        fig_hour = px.bar(
            hour_activity,
            x="listening_hour",
            y="play_hours",
            template="plotly_white",
            title="Listening by Hour",
            labels={"play_hours": "Hours"},
        )
        st.plotly_chart(fig_hour, use_container_width=True)

    with col_right:
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_activity["weekday_name"] = pd.Categorical(day_activity["weekday_name"], categories=order, ordered=True)
        day_activity = day_activity.sort_values("weekday_name")
        fig_day = px.bar(
            day_activity,
            x="weekday_name",
            y="play_hours",
            template="plotly_white",
            title="Listening by Weekday",
            labels={"play_hours": "Hours", "weekday_name": "Day"},
        )
        st.plotly_chart(fig_day, use_container_width=True)

    st.subheader("Summary Insights")
    st.info(
        f"Your listening profile shows {total_hours:,.1f} hours total. "
        f"Peak engagement happens around {most_active_hour:02d}:00 and is strongest on {most_active_day}. "
        f"Shuffle is used in {shuffle_rate:.1f}% of plays, while {skip_rate:.1f}% of plays are skipped."
    )
