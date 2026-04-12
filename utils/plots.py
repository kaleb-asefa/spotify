from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def line_chart(df: pd.DataFrame, x: str, y: str, title: str):
    fig = px.line(df, x=x, y=y, markers=True, template="plotly_white", title=title)
    fig.update_layout(hovermode="x unified")
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None):
    fig = px.bar(df, x=x, y=y, color=color, template="plotly_white", title=title)
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    return fig


def heatmap_hour_weekday(df: pd.DataFrame):
    pivot = (
        df.groupby(["weekday_name", "listening_hour"], as_index=False)["play_minutes"]
        .sum()
        .pivot(index="weekday_name", columns="listening_hour", values="play_minutes")
        .fillna(0)
    )

    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = pivot.reindex([d for d in order if d in pivot.index])

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Viridis",
            hovertemplate="Hour %{x}<br>%{y}<br>Minutes %{z:.1f}<extra></extra>",
        )
    )
    fig.update_layout(template="plotly_white", title="Listening Heatmap: Hour x Weekday")
    return fig


def cumulative_line(df: pd.DataFrame):
    frame = df.sort_values("date").copy()
    frame["cumulative_hours"] = frame["play_hours"].cumsum()
    fig = px.line(frame, x="date", y="cumulative_hours", template="plotly_white", title="Cumulative Listening Hours")
    fig.update_layout(hovermode="x unified")
    return fig
