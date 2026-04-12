from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def descriptive_stats(values: pd.Series) -> dict[str, float]:
    series = pd.to_numeric(values, errors="coerce").dropna()
    if series.empty:
        return {}

    return {
        "mean": float(series.mean()),
        "median": float(series.median()),
        "variance": float(series.var(ddof=1)) if len(series) > 1 else 0.0,
        "std_dev": float(series.std(ddof=1)) if len(series) > 1 else 0.0,
        "p25": float(series.quantile(0.25)),
        "p50": float(series.quantile(0.50)),
        "p75": float(series.quantile(0.75)),
        "p90": float(series.quantile(0.90)),
    }


def confidence_interval_mean(values: pd.Series, confidence: float = 0.95) -> tuple[float, float] | None:
    series = pd.to_numeric(values, errors="coerce").dropna()
    if len(series) < 2:
        return None

    mean = series.mean()
    sem = stats.sem(series)
    interval = stats.t.interval(confidence, len(series) - 1, loc=mean, scale=sem)
    return float(interval[0]), float(interval[1])


def zscore_anomaly_days(daily_df: pd.DataFrame, threshold: float = 2.5) -> pd.DataFrame:
    frame = daily_df.copy()
    if frame.empty or "play_hours" not in frame.columns:
        return frame.iloc[0:0]

    frame["zscore"] = stats.zscore(frame["play_hours"], nan_policy="omit")
    frame["zscore"] = frame["zscore"].fillna(0.0)
    return frame[frame["zscore"].abs() >= threshold].sort_values("zscore", ascending=False)


def weekday_weekend_hypothesis_test(df: pd.DataFrame) -> dict[str, float | str]:
    if df.empty:
        return {"status": "insufficient_data"}

    day_level = df.groupby("date", as_index=False)["play_minutes"].sum()
    day_level["date"] = pd.to_datetime(day_level["date"])
    day_level["is_weekend"] = day_level["date"].dt.weekday >= 5

    weekday = day_level.loc[~day_level["is_weekend"], "play_minutes"]
    weekend = day_level.loc[day_level["is_weekend"], "play_minutes"]

    if len(weekday) < 2 or len(weekend) < 2:
        return {"status": "insufficient_data"}

    stat, pvalue = stats.ttest_ind(weekday, weekend, equal_var=False)

    return {
        "status": "ok",
        "weekday_mean": float(weekday.mean()),
        "weekend_mean": float(weekend.mean()),
        "t_stat": float(stat),
        "p_value": float(pvalue),
    }


def artist_diversity_score(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0

    shares = (
        df["master_metadata_album_artist_name"]
        .value_counts(normalize=True)
        .clip(lower=0)
    )
    simpson = 1.0 - float(np.sum(np.square(shares)))
    return simpson
