from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.spotify_metadata import search_album, search_artist
from utils.loader import discover_json_files, load_spotify_data
from utils.preprocessing import apply_dashboard_filters, preprocess_listening_data

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
