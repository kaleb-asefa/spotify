from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st



def render(df: pd.DataFrame):
    st.title("Listening Behavior Analysis")

    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Start/End Reasons", "Skip & Shuffle", "Offline & Incognito", "Platform Trends"]
    )

    with tab1:
        c1, c2 = st.columns(2)
        start_counts = df["reason_start"].value_counts().reset_index()
        start_counts.columns = ["reason_start", "count"]

        end_counts = df["reason_end"].value_counts().reset_index()
        end_counts.columns = ["reason_end", "count"]

        with c1:
            fig = px.bar(start_counts.head(12), x="reason_start", y="count", template="plotly_white", title="How Tracks Start")
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig = px.bar(end_counts.head(12), x="reason_end", y="count", template="plotly_white", title="Why Tracks End")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        skip_by_reason = (
            df.groupby("reason_end", as_index=False)
            .agg(skip_rate=("is_skipped", "mean"), count=("is_skipped", "size"))
            .sort_values("skip_rate", ascending=False)
        )

        shuffle_compare = (
            df.groupby("shuffle", as_index=False)
            .agg(skip_rate=("is_skipped", "mean"), avg_minutes=("play_minutes", "mean"), count=("is_skipped", "size"))
        )
        shuffle_compare["shuffle"] = shuffle_compare["shuffle"].map({True: "Shuffle On", False: "Shuffle Off"})

        with c1:
            fig = px.bar(
                skip_by_reason.head(12),
                x="reason_end",
                y="skip_rate",
                color="count",
                template="plotly_white",
                title="Skip Rate by End Reason",
            )
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig = px.bar(
                shuffle_compare,
                x="shuffle",
                y="skip_rate",
                color="avg_minutes",
                template="plotly_white",
                title="Shuffle vs Skip Behavior",
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        c1, c2 = st.columns(2)
        offline_share = (
            df.groupby("offline", as_index=False)
            .agg(hours=("play_hours", "sum"), skip_rate=("is_skipped", "mean"))
        )
        offline_share["offline"] = offline_share["offline"].map({True: "Offline", False: "Online"})

        incognito_share = (
            df.groupby("incognito_mode", as_index=False)
            .agg(hours=("play_hours", "sum"), plays=("play_hours", "size"))
        )
        incognito_share["incognito_mode"] = incognito_share["incognito_mode"].map({True: "Incognito", False: "Normal"})

        with c1:
            fig = px.pie(offline_share, names="offline", values="hours", title="Offline vs Online Listening")
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig = px.bar(
                incognito_share,
                x="incognito_mode",
                y="hours",
                color="plays",
                title="Incognito Mode Usage",
                template="plotly_white",
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        platform_usage = (
            df.groupby("platform", as_index=False)
            .agg(plays=("platform", "size"), hours=("play_hours", "sum"), skip_rate=("is_skipped", "mean"))
            .sort_values("plays", ascending=False)
        )

        fig = px.bar(
            platform_usage.head(15),
            x="platform",
            y="plays",
            color="skip_rate",
            template="plotly_white",
            title="Device/Platform Usage Trends",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(platform_usage, use_container_width=True)
