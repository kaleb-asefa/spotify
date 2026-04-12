from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.stats import descriptive_stats



def render(df: pd.DataFrame):
    st.title("Listening Trends")

    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    daily = df.groupby("date", as_index=False).agg(play_hours=("play_hours", "sum"))
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date")
    daily["rolling_7d"] = daily["play_hours"].rolling(7, min_periods=1).mean()
    daily["cumulative_hours"] = daily["play_hours"].cumsum()

    weekly = daily.set_index("date").resample("W").sum(numeric_only=True).reset_index()
    monthly = daily.set_index("date").resample("M").sum(numeric_only=True).reset_index()
    yearly = daily.set_index("date").resample("Y").sum(numeric_only=True).reset_index()

    t1, t2, t3 = st.tabs(["Daily & Rolling", "Weekly / Monthly", "Yearly & Cumulative"])

    with t1:
        fig_daily = px.line(
            daily,
            x="date",
            y=["play_hours", "rolling_7d"],
            template="plotly_white",
            title="Daily Listening vs Rolling 7-Day Average",
            labels={"value": "Hours", "variable": "Series"},
        )
        st.plotly_chart(fig_daily, use_container_width=True)

    with t2:
        c1, c2 = st.columns(2)
        with c1:
            fig_weekly = px.bar(weekly, x="date", y="play_hours", template="plotly_white", title="Weekly Listening Hours")
            st.plotly_chart(fig_weekly, use_container_width=True)
        with c2:
            fig_monthly = px.bar(monthly, x="date", y="play_hours", template="plotly_white", title="Monthly Listening Hours")
            st.plotly_chart(fig_monthly, use_container_width=True)

    with t3:
        c1, c2 = st.columns(2)
        with c1:
            fig_yearly = px.bar(yearly, x="date", y="play_hours", template="plotly_white", title="Yearly Listening Comparison")
            st.plotly_chart(fig_yearly, use_container_width=True)
        with c2:
            fig_cum = px.line(daily, x="date", y="cumulative_hours", template="plotly_white", title="Cumulative Listening Hours")
            st.plotly_chart(fig_cum, use_container_width=True)

    stats_payload = descriptive_stats(daily["play_hours"])
    st.subheader("Statistical Metrics")

    if stats_payload:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Mean", f"{stats_payload['mean']:.2f} h/day")
        m2.metric("Median", f"{stats_payload['median']:.2f} h/day")
        m3.metric("Variance", f"{stats_payload['variance']:.2f}")
        m4.metric("Std Dev", f"{stats_payload['std_dev']:.2f}")

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("P25", f"{stats_payload['p25']:.2f}")
        p2.metric("P50", f"{stats_payload['p50']:.2f}")
        p3.metric("P75", f"{stats_payload['p75']:.2f}")
        p4.metric("P90", f"{stats_payload['p90']:.2f}")
