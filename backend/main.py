from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.spotify_metadata import search_album, search_artist
from models.skip_model import train_skip_prediction_model
from utils.loader import discover_json_files, load_spotify_data
from utils.preprocessing import apply_dashboard_filters, preprocess_listening_data
from utils.stats import (
    artist_diversity_score,
    confidence_interval_mean,
    descriptive_stats,
    weekday_weekend_hypothesis_test,
    zscore_anomaly_days,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

app = FastAPI(title="Spotify Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _to_records(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    subset = frame[columns].copy()

    # Avoid applying numeric fill values to categorical/text columns.
    for col in subset.columns:
        if pd.api.types.is_categorical_dtype(subset[col]):
            subset[col] = subset[col].astype("object")

        if pd.api.types.is_numeric_dtype(subset[col]):
            subset[col] = subset[col].fillna(0)
        else:
            subset[col] = subset[col].fillna("")

    return subset.to_dict(orient="records")


def _with_date_str(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    if frame.empty or column not in frame.columns:
        return frame

    result = frame.copy()
    result[column] = pd.to_datetime(result[column], errors="coerce").dt.date.astype(str)
    return result


@lru_cache(maxsize=1)
def _load_full_frame() -> pd.DataFrame:
    raw = load_spotify_data(DATA_DIR)
    pack = preprocess_listening_data(raw)
    return pack["full"]


def _parse_csv_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _apply_filters(
    start_date: str | None,
    end_date: str | None,
    artists_csv: str | None,
    content_types_csv: str | None,
) -> pd.DataFrame:
    full_df = _load_full_frame()
    if full_df.empty:
        return full_df

    min_date = full_df["date"].min()
    max_date = full_df["date"].max()

    artists = _parse_csv_list(artists_csv)
    content_types = _parse_csv_list(content_types_csv) or ["Songs", "Podcasts", "Audiobooks"]

    return apply_dashboard_filters(
        full_df,
        start_date=start_date or min_date,
        end_date=end_date or max_date,
        artists=artists,
        content_types=content_types,
    )


def _enrich_top_artists(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame

    enriched = frame.copy()
    image_urls: list[str | None] = []
    external_urls: list[str | None] = []

    for artist_name in enriched["artist"].fillna("").tolist():
        metadata = search_artist(str(artist_name))
        image_urls.append(metadata.get("image_url"))
        external_urls.append(metadata.get("external_url"))

    enriched["image_url"] = image_urls
    enriched["external_url"] = external_urls
    return enriched


def _build_favorite_albums(filtered: pd.DataFrame) -> pd.DataFrame:
    if filtered.empty:
        return pd.DataFrame()

    albums = (
        filtered.groupby(["master_metadata_album_album_name", "master_metadata_album_artist_name"], as_index=False)[
            "play_hours"
        ]
        .sum()
        .sort_values("play_hours", ascending=False)
        .head(10)
        .rename(
            columns={
                "master_metadata_album_album_name": "album",
                "master_metadata_album_artist_name": "artist",
            }
        )
    )

    albums = albums.fillna("")
    image_urls: list[str | None] = []
    external_urls: list[str | None] = []

    for row in albums.itertuples(index=False):
        metadata = search_album(str(row.album), str(row.artist))
        image_urls.append(metadata.get("image_url"))
        external_urls.append(metadata.get("external_url"))

    albums["image_url"] = image_urls
    albums["external_url"] = external_urls
    return albums


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/options")
def options() -> dict[str, Any]:
    full_df = _load_full_frame()
    files = discover_json_files(DATA_DIR)

    if full_df.empty:
        return {
            "filesLoaded": len(files),
            "artists": [],
            "dateRange": None,
            "contentTypes": ["Songs", "Podcasts", "Audiobooks"],
        }

    artists = sorted(full_df["master_metadata_album_artist_name"].dropna().unique().tolist())

    return {
        "filesLoaded": len(files),
        "artists": artists,
        "dateRange": {
            "min": str(full_df["date"].min()),
            "max": str(full_df["date"].max()),
        },
        "contentTypes": ["Songs", "Podcasts", "Audiobooks"],
    }


@app.get("/api/dashboard")
def dashboard(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    artists: str | None = Query(default=None),
    content_types: str | None = Query(default=None),
) -> dict[str, Any]:
    filtered = _apply_filters(start_date, end_date, artists, content_types)

    if filtered.empty:
        return {
            "kpis": {
                "totalHours": 0.0,
                "tracksPlayed": 0,
                "uniqueArtists": 0,
                "uniqueAlbums": 0,
                "skipRate": 0.0,
                "shuffleRate": 0.0,
            },
            "charts": {
                "hourly": [],
                "weekday": [],
                "daily": [],
                "topArtists": [],
                "topTracks": [],
                "favoriteAlbums": [],
                "contentMix": [],
                "platformShare": [],
            },
            "meta": {"rows": 0},
        }

    total_hours = float(filtered["play_hours"].sum())
    tracks_played = int(filtered["is_song"].sum())
    unique_artists = int(filtered["master_metadata_album_artist_name"].nunique())
    unique_albums = int(filtered["master_metadata_album_album_name"].nunique())
    skip_rate = float(filtered["is_skipped"].mean() * 100)
    shuffle_rate = float(filtered["shuffle"].mean() * 100)

    hourly = filtered.groupby("listening_hour", as_index=False)["play_hours"].sum().sort_values("listening_hour")
    weekday = filtered.groupby("weekday_name", as_index=False)["play_hours"].sum()
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday["weekday_name"] = pd.Categorical(weekday["weekday_name"], categories=weekday_order, ordered=True)
    weekday = weekday.sort_values("weekday_name")

    daily = filtered.groupby("date", as_index=False)["play_hours"].sum().sort_values("date")
    daily["date"] = daily["date"].astype(str)

    top_artists = (
        filtered.groupby("master_metadata_album_artist_name", as_index=False)["play_hours"]
        .sum()
        .sort_values("play_hours", ascending=False)
        .head(10)
        .rename(columns={"master_metadata_album_artist_name": "artist"})
    )
    top_artists = _enrich_top_artists(top_artists)

    top_tracks = (
        filtered.groupby("master_metadata_track_name", as_index=False)["play_hours"]
        .sum()
        .sort_values("play_hours", ascending=False)
        .head(10)
        .rename(columns={"master_metadata_track_name": "track"})
    )

    favorite_albums = _build_favorite_albums(filtered)

    content_mix = [
        {"name": "Songs", "value": float(filtered["is_song"].sum())},
        {"name": "Podcasts", "value": float(filtered["is_podcast"].sum())},
        {"name": "Audiobooks", "value": float(filtered["is_audiobook"].sum())},
    ]

    platform_share = (
        filtered.groupby("platform", as_index=False)["play_hours"]
        .sum()
        .sort_values("play_hours", ascending=False)
        .head(8)
        .rename(columns={"platform": "name", "play_hours": "value"})
    )

    return {
        "kpis": {
            "totalHours": round(total_hours, 2),
            "tracksPlayed": tracks_played,
            "uniqueArtists": unique_artists,
            "uniqueAlbums": unique_albums,
            "skipRate": round(skip_rate, 2),
            "shuffleRate": round(shuffle_rate, 2),
        },
        "charts": {
            "hourly": _to_records(hourly, ["listening_hour", "play_hours"]),
            "weekday": _to_records(weekday, ["weekday_name", "play_hours"]),
            "daily": _to_records(daily, ["date", "play_hours"]),
            "topArtists": _to_records(top_artists, ["artist", "play_hours", "image_url", "external_url"]),
            "topTracks": _to_records(top_tracks, ["track", "play_hours"]),
            "favoriteAlbums": _to_records(favorite_albums, ["album", "artist", "play_hours", "image_url", "external_url"]),
            "contentMix": content_mix,
            "platformShare": _to_records(platform_share, ["name", "value"]),
        },
        "meta": {"rows": int(len(filtered))},
    }


@app.get("/api/overview")
def overview(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    artists: str | None = Query(default=None),
    content_types: str | None = Query(default=None),
) -> dict[str, Any]:
    filtered = _apply_filters(start_date, end_date, artists, content_types)

    if filtered.empty:
        return {
            "kpis": {
                "totalHours": 0.0,
                "tracksPlayed": 0,
                "uniqueArtists": 0,
                "uniqueAlbums": 0,
                "skipRate": 0.0,
                "shuffleRate": 0.0,
            },
            "highlights": {"mostActiveHour": None, "mostActiveDay": None},
            "charts": {"hourly": [], "weekday": []},
            "meta": {"rows": 0},
        }

    total_hours = float(filtered["play_hours"].sum())
    tracks_played = int(filtered["is_song"].sum())
    unique_artists = int(filtered["master_metadata_album_artist_name"].nunique())
    unique_albums = int(filtered["master_metadata_album_album_name"].nunique())
    skip_rate = float(filtered["is_skipped"].mean() * 100)
    shuffle_rate = float(filtered["shuffle"].mean() * 100)

    hourly = (
        filtered.groupby("listening_hour", as_index=False)["play_hours"]
        .sum()
        .sort_values("listening_hour")
    )
    weekday = filtered.groupby("weekday_name", as_index=False)["play_hours"].sum()
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday["weekday_name"] = pd.Categorical(weekday["weekday_name"], categories=weekday_order, ordered=True)
    weekday = weekday.sort_values("weekday_name")

    most_active_hour = None
    most_active_day = None
    if not hourly.empty:
        most_active_hour = int(hourly.sort_values("play_hours", ascending=False).iloc[0]["listening_hour"])
    if not weekday.empty:
        most_active_day = str(weekday.sort_values("play_hours", ascending=False).iloc[0]["weekday_name"])

    return {
        "kpis": {
            "totalHours": round(total_hours, 2),
            "tracksPlayed": tracks_played,
            "uniqueArtists": unique_artists,
            "uniqueAlbums": unique_albums,
            "skipRate": round(skip_rate, 2),
            "shuffleRate": round(shuffle_rate, 2),
        },
        "highlights": {
            "mostActiveHour": most_active_hour,
            "mostActiveDay": most_active_day,
        },
        "charts": {
            "hourly": _to_records(hourly, ["listening_hour", "play_hours"]),
            "weekday": _to_records(weekday, ["weekday_name", "play_hours"]),
        },
        "meta": {"rows": int(len(filtered))},
    }


@app.get("/api/listening-trends")
def listening_trends(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    artists: str | None = Query(default=None),
    content_types: str | None = Query(default=None),
) -> dict[str, Any]:
    filtered = _apply_filters(start_date, end_date, artists, content_types)

    if filtered.empty:
        return {
            "daily": [],
            "weekly": [],
            "monthly": [],
            "yearly": [],
            "stats": {},
            "meta": {"rows": 0},
        }

    daily = filtered.groupby("date", as_index=False).agg(play_hours=("play_hours", "sum"))
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    daily = daily.sort_values("date")
    daily["rolling_7d"] = daily["play_hours"].rolling(7, min_periods=1).mean()
    daily["cumulative_hours"] = daily["play_hours"].cumsum()

    daily_indexed = daily.set_index("date")
    weekly = daily_indexed["play_hours"].resample("W").sum().reset_index()
    monthly = daily_indexed["play_hours"].resample("M").sum().reset_index()
    yearly = daily_indexed["play_hours"].resample("Y").sum().reset_index()

    daily = _with_date_str(daily, "date")
    weekly = _with_date_str(weekly, "date")
    monthly = _with_date_str(monthly, "date")
    yearly = _with_date_str(yearly, "date")

    return {
        "daily": _to_records(daily, ["date", "play_hours", "rolling_7d", "cumulative_hours"]),
        "weekly": _to_records(weekly, ["date", "play_hours"]),
        "monthly": _to_records(monthly, ["date", "play_hours"]),
        "yearly": _to_records(yearly, ["date", "play_hours"]),
        "stats": descriptive_stats(daily["play_hours"]),
        "meta": {"rows": int(len(filtered))},
    }


@app.get("/api/behavior-analysis")
def behavior_analysis(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    artists: str | None = Query(default=None),
    content_types: str | None = Query(default=None),
) -> dict[str, Any]:
    filtered = _apply_filters(start_date, end_date, artists, content_types)

    if filtered.empty:
        return {
            "startCounts": [],
            "endCounts": [],
            "skipByReason": [],
            "shuffleCompare": [],
            "offlineShare": [],
            "incognitoShare": [],
            "platformUsage": [],
            "meta": {"rows": 0},
        }

    start_counts = filtered["reason_start"].value_counts().reset_index()
    start_counts.columns = ["reason_start", "count"]

    end_counts = filtered["reason_end"].value_counts().reset_index()
    end_counts.columns = ["reason_end", "count"]

    skip_by_reason = (
        filtered.groupby("reason_end", as_index=False)
        .agg(skip_rate=("is_skipped", "mean"), count=("is_skipped", "size"))
        .sort_values("skip_rate", ascending=False)
    )

    shuffle_compare = (
        filtered.groupby("shuffle", as_index=False)
        .agg(
            skip_rate=("is_skipped", "mean"),
            avg_minutes=("play_minutes", "mean"),
            count=("is_skipped", "size"),
        )
    )
    shuffle_compare["shuffle"] = shuffle_compare["shuffle"].map({True: "Shuffle On", False: "Shuffle Off"})

    offline_share = (
        filtered.groupby("offline", as_index=False)
        .agg(hours=("play_hours", "sum"), skip_rate=("is_skipped", "mean"))
    )
    offline_share["offline"] = offline_share["offline"].map({True: "Offline", False: "Online"})

    incognito_share = (
        filtered.groupby("incognito_mode", as_index=False)
        .agg(hours=("play_hours", "sum"), plays=("play_hours", "size"))
    )
    incognito_share["incognito_mode"] = incognito_share["incognito_mode"].map({True: "Incognito", False: "Normal"})

    platform_usage = (
        filtered.groupby("platform", as_index=False)
        .agg(plays=("platform", "size"), hours=("play_hours", "sum"), skip_rate=("is_skipped", "mean"))
        .sort_values("plays", ascending=False)
    )

    return {
        "startCounts": _to_records(start_counts, ["reason_start", "count"]),
        "endCounts": _to_records(end_counts, ["reason_end", "count"]),
        "skipByReason": _to_records(skip_by_reason, ["reason_end", "skip_rate", "count"]),
        "shuffleCompare": _to_records(shuffle_compare, ["shuffle", "skip_rate", "avg_minutes", "count"]),
        "offlineShare": _to_records(offline_share, ["offline", "hours", "skip_rate"]),
        "incognitoShare": _to_records(incognito_share, ["incognito_mode", "hours", "plays"]),
        "platformUsage": _to_records(platform_usage, ["platform", "plays", "hours", "skip_rate"]),
        "meta": {"rows": int(len(filtered))},
    }


@app.get("/api/time-patterns")
def time_patterns(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    artists: str | None = Query(default=None),
    content_types: str | None = Query(default=None),
) -> dict[str, Any]:
    filtered = _apply_filters(start_date, end_date, artists, content_types)

    if filtered.empty:
        return {
            "heatmap": {"x": [], "y": [], "z": []},
            "seasonal": [],
            "dayNight": [],
            "weekSegment": [],
            "hourCurve": [],
            "meta": {"rows": 0},
        }

    heatmap_source = (
        filtered.groupby(["weekday_name", "listening_hour"], as_index=False)["play_minutes"]
        .sum()
    )
    pivot = (
        heatmap_source.pivot(index="weekday_name", columns="listening_hour", values="play_minutes")
        .fillna(0)
    )
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = pivot.reindex(weekday_order)
    pivot = pivot.fillna(0)
    for hour in range(24):
        if hour not in pivot.columns:
            pivot[hour] = 0.0
    pivot = pivot.sort_index(axis=1)

    heatmap = {
        "x": [int(x) for x in pivot.columns.tolist()],
        "y": pivot.index.tolist(),
        "z": pivot.values.tolist(),
    }

    seasonal = (
        filtered.groupby("month", as_index=False)["play_hours"]
        .sum()
        .sort_values("month")
    )

    temp = filtered.copy()
    temp["day_period"] = temp["listening_hour"].apply(lambda h: "Day" if 6 <= h < 18 else "Night")
    day_night = temp.groupby("day_period", as_index=False).agg(hours=("play_hours", "sum"), plays=("play_hours", "size"))

    temp["week_segment"] = temp["weekday_num"].apply(lambda x: "Weekend" if x >= 5 else "Weekday")
    week_segment = temp.groupby("week_segment", as_index=False).agg(
        hours=("play_hours", "sum"), avg_minutes=("play_minutes", "mean")
    )

    hour_curve = (
        filtered.groupby("listening_hour", as_index=False)["play_hours"]
        .sum()
        .sort_values("listening_hour")
    )

    return {
        "heatmap": heatmap,
        "seasonal": _to_records(seasonal, ["month", "play_hours"]),
        "dayNight": _to_records(day_night, ["day_period", "hours", "plays"]),
        "weekSegment": _to_records(week_segment, ["week_segment", "hours", "avg_minutes"]),
        "hourCurve": _to_records(hour_curve, ["listening_hour", "play_hours"]),
        "meta": {"rows": int(len(filtered))},
    }


@app.get("/api/statistical-insights")
def statistical_insights(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    artists: str | None = Query(default=None),
    content_types: str | None = Query(default=None),
    threshold: float = Query(default=2.5, ge=1.0, le=5.0),
) -> dict[str, Any]:
    filtered = _apply_filters(start_date, end_date, artists, content_types)

    if filtered.empty:
        return {
            "daily": [],
            "confidenceInterval": None,
            "anomalies": [],
            "distribution": [],
            "hypothesis": {"status": "insufficient_data"},
            "meta": {"rows": 0},
        }

    daily = filtered.groupby("date", as_index=False)["play_hours"].sum()
    daily = _with_date_str(daily, "date")

    ci = confidence_interval_mean(daily["play_hours"], confidence=0.95)
    anomalies = zscore_anomaly_days(daily, threshold=threshold)
    anomalies = _with_date_str(anomalies, "date")

    return {
        "daily": _to_records(daily, ["date", "play_hours"]),
        "confidenceInterval": {"lower": ci[0], "upper": ci[1]} if ci else None,
        "anomalies": _to_records(anomalies, ["date", "play_hours", "zscore"]),
        "distribution": daily["play_hours"].fillna(0).tolist(),
        "hypothesis": weekday_weekend_hypothesis_test(filtered),
        "meta": {"rows": int(len(filtered))},
    }


@app.get("/api/artist-song-analytics")
def artist_song_analytics(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    artists: str | None = Query(default=None),
    content_types: str | None = Query(default=None),
    top_n: int = Query(default=10, ge=5, le=50),
) -> dict[str, Any]:
    filtered = _apply_filters(start_date, end_date, artists, content_types)

    songs = filtered[filtered["is_song"]].copy()
    if songs.empty:
        return {
            "diversityScore": 0.0,
            "featuredTrack": None,
            "topAlbums": [],
            "topArtists": [],
            "wrappedInsights": {},
            "rankings": {
                "topArtists": [],
                "topTracks": [],
                "topAlbums": [],
                "repeatedTracks": [],
            },
            "meta": {"rows": 0},
        }

    diversity = artist_diversity_score(songs)

    top_track_row = (
        songs.groupby(
            ["master_metadata_track_name", "master_metadata_album_artist_name", "master_metadata_album_album_name"],
            as_index=False,
        )
        .agg(
            streams=("master_metadata_track_name", "count"),
            listening_minutes=("play_minutes", "sum"),
            first_play=("ts", "min"),
            last_play=("ts", "max"),
        )
        .sort_values(["streams", "listening_minutes"], ascending=False)
        .head(1)
    )

    featured_track = None
    if not top_track_row.empty:
        row = top_track_row.iloc[0]
        album_meta = search_album(str(row["master_metadata_album_album_name"]), str(row["master_metadata_album_artist_name"]))
        featured_track = {
            "track": row["master_metadata_track_name"],
            "artist": row["master_metadata_album_artist_name"],
            "album": row["master_metadata_album_album_name"],
            "streams": int(row["streams"]),
            "listeningMinutes": float(row["listening_minutes"]),
            "firstPlay": pd.to_datetime(row["first_play"]).date().isoformat(),
            "lastPlay": pd.to_datetime(row["last_play"]).date().isoformat(),
            "imageUrl": album_meta.get("image_url"),
            "externalUrl": album_meta.get("external_url"),
        }

    top_albums = (
        songs.groupby(["master_metadata_album_album_name", "master_metadata_album_artist_name"], as_index=False)
        .agg(play_count=("master_metadata_track_name", "count"), play_minutes=("play_minutes", "sum"))
        .sort_values(["play_count", "play_minutes"], ascending=False)
        .head(8)
    )
    top_albums_payload: list[dict[str, Any]] = []
    for row in top_albums.itertuples(index=False):
        album_meta = search_album(str(row.master_metadata_album_album_name), str(row.master_metadata_album_artist_name))
        top_albums_payload.append(
            {
                "album": row.master_metadata_album_album_name,
                "artist": row.master_metadata_album_artist_name,
                "playCount": int(row.play_count),
                "playMinutes": float(row.play_minutes),
                "imageUrl": album_meta.get("image_url"),
                "externalUrl": album_meta.get("external_url"),
            }
        )

    top_artists = (
        songs.groupby("master_metadata_album_artist_name", as_index=False)
        .agg(total_plays=("master_metadata_track_name", "count"), total_minutes=("play_minutes", "sum"))
        .sort_values(["total_plays", "total_minutes"], ascending=False)
        .head(5)
    )
    total_plays_all = max(int(songs.shape[0]), 1)
    top_artists_payload: list[dict[str, Any]] = []
    for row in top_artists.itertuples(index=False):
        artist_meta = search_artist(str(row.master_metadata_album_artist_name))
        top_artists_payload.append(
            {
                "artist": row.master_metadata_album_artist_name,
                "totalPlays": int(row.total_plays),
                "totalMinutes": float(row.total_minutes),
                "share": round(100 * row.total_plays / total_plays_all, 2),
                "imageUrl": artist_meta.get("image_url"),
                "externalUrl": artist_meta.get("external_url"),
            }
        )

    songs_local = songs.copy()
    songs_local["hour"] = songs_local["ts"].dt.hour
    songs_local["is_weekend"] = songs_local["ts"].dt.weekday >= 5
    songs_local["year"] = songs_local["ts"].dt.year

    late_night_track = (
        songs_local[songs_local["hour"].between(0, 4)]
        .groupby("master_metadata_track_name", as_index=False)
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

    wrapped_insights = {
        "lateNightTrack": late_night_track.to_dict(orient="records"),
        "mostReplayedArtist": most_replayed_artist.to_dict(orient="records"),
        "weekendAnthem": weekend_anthem.to_dict(orient="records"),
        "topArtistYear": {
            "year": current_year,
            "items": top_artist_year.to_dict(orient="records"),
        },
    }

    ranking_artists = (
        songs.groupby("master_metadata_album_artist_name", as_index=False)
        .agg(plays=("master_metadata_track_name", "count"), hours=("play_hours", "sum"))
        .sort_values("plays", ascending=False)
        .head(top_n)
    )

    ranking_tracks = (
        songs.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"], as_index=False)
        .agg(plays=("master_metadata_track_name", "count"), hours=("play_hours", "sum"))
        .sort_values("plays", ascending=False)
        .head(top_n)
    )

    ranking_albums = (
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

    return {
        "diversityScore": float(diversity),
        "featuredTrack": featured_track,
        "topAlbums": top_albums_payload,
        "topArtists": top_artists_payload,
        "wrappedInsights": wrapped_insights,
        "rankings": {
            "topArtists": _to_records(ranking_artists, ["master_metadata_album_artist_name", "plays", "hours"]),
            "topTracks": _to_records(ranking_tracks, ["master_metadata_track_name", "master_metadata_album_artist_name", "plays", "hours"]),
            "topAlbums": _to_records(ranking_albums, ["master_metadata_album_album_name", "plays", "hours"]),
            "repeatedTracks": _to_records(repeated_tracks, ["master_metadata_track_name", "master_metadata_album_artist_name", "play_count"]),
        },
        "meta": {"rows": int(len(filtered))},
    }


@app.post("/api/skip-model")
def skip_model(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    artists: str | None = Query(default=None),
    content_types: str | None = Query(default=None),
) -> dict[str, Any]:
    filtered = _apply_filters(start_date, end_date, artists, content_types)
    result = train_skip_prediction_model(filtered)

    if result.get("status") != "ok":
        return {"status": result.get("status", "error")}

    return {
        "status": "ok",
        "accuracy": result.get("accuracy"),
        "roc_auc": result.get("roc_auc"),
        "report": result.get("report"),
    }
