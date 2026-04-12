from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.plots import heatmap_hour_weekday



def render(df: pd.DataFrame):
    st.title("Time Pattern Intelligence")

    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    st.plotly_chart(heatmap_hour_weekday(df), use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        seasonal = (
            df.groupby("month", as_index=False)["play_hours"]
            .sum()
            .sort_values("month")
        )
        fig = px.line(
            seasonal,
            x="month",
            y="play_hours",
            markers=True,
            template="plotly_white",
            title="Monthly Seasonality",
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        temp = df.copy()
        temp["day_period"] = temp["listening_hour"].apply(lambda h: "Day" if 6 <= h < 18 else "Night")
        day_night = temp.groupby("day_period", as_index=False).agg(hours=("play_hours", "sum"), plays=("play_hours", "size"))
        fig = px.bar(day_night, x="day_period", y="hours", color="plays", title="Night vs Day Listening", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        temp = df.copy()
        temp["week_segment"] = temp["weekday_num"].apply(lambda x: "Weekend" if x >= 5 else "Weekday")
        segment = temp.groupby("week_segment", as_index=False).agg(hours=("play_hours", "sum"), avg_minutes=("play_minutes", "mean"))
        fig = px.bar(segment, x="week_segment", y="hours", color="avg_minutes", title="Weekday vs Weekend", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        hour_curve = df.groupby("listening_hour", as_index=False)["play_hours"].sum()
        fig = px.area(hour_curve, x="listening_hour", y="play_hours", title="Hour-of-Day Listening Curve", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
