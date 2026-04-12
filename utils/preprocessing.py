from __future__ import annotations

import numpy as np
import pandas as pd


def preprocess_listening_data(df: pd.DataFrame, session_gap_minutes: int = 30) -> dict[str, pd.DataFrame]:
    if df.empty:
        empty = pd.DataFrame()
        return {
            "full": empty,
            "songs": empty,
            "podcasts": empty,
            "audiobooks": empty,
        }

    frame = df.copy()

    frame["ts"] = pd.to_datetime(frame["ts"], errors="coerce", utc=True)
    frame = frame.dropna(subset=["ts"]).drop_duplicates().sort_values("ts").reset_index(drop=True)

    frame["ms_played"] = pd.to_numeric(frame.get("ms_played"), errors="coerce").fillna(0.0).clip(lower=0.0)
    frame["play_minutes"] = frame["ms_played"] / 60000.0
    frame["play_hours"] = frame["ms_played"] / 3600000.0

    frame["date"] = frame["ts"].dt.date
    frame["year"] = frame["ts"].dt.year
    frame["month"] = frame["ts"].dt.month
    frame["weekday_name"] = frame["ts"].dt.day_name()
    frame["weekday_num"] = frame["ts"].dt.weekday
    frame["listening_hour"] = frame["ts"].dt.hour

    frame["master_metadata_track_name"] = frame["master_metadata_track_name"].fillna("Unknown Track")
    frame["master_metadata_album_artist_name"] = frame["master_metadata_album_artist_name"].fillna("Unknown Artist")
    frame["master_metadata_album_album_name"] = frame["master_metadata_album_album_name"].fillna("Unknown Album")

    frame["is_podcast"] = (
        frame["episode_name"].notna()
        | frame["episode_show_name"].notna()
        | frame["spotify_episode_uri"].notna()
    )
    frame["is_audiobook"] = (
        frame["audiobook_title"].notna()
        | frame["audiobook_uri"].notna()
        | frame["audiobook_chapter_uri"].notna()
    )
    frame["is_song"] = ~(frame["is_podcast"] | frame["is_audiobook"])

    frame["is_skipped"] = frame["skipped"].fillna(False).astype(bool)
    frame["is_fully_played"] = (~frame["is_skipped"]) & (frame["play_minutes"] >= 2.0)

    frame["shuffle"] = frame["shuffle"].fillna(False).astype(bool)
    frame["offline"] = frame["offline"].fillna(False).astype(bool)
    frame["incognito_mode"] = frame["incognito_mode"].fillna(False).astype(bool)
    frame["platform"] = frame["platform"].fillna("unknown")
    frame["reason_start"] = frame["reason_start"].fillna("unknown")
    frame["reason_end"] = frame["reason_end"].fillna("unknown")

    session_gap = frame["ts"].diff().dt.total_seconds().fillna(0) > (session_gap_minutes * 60)
    frame["session_id"] = session_gap.cumsum() + 1

    songs = frame[frame["is_song"]].copy()
    podcasts = frame[frame["is_podcast"]].copy()
    audiobooks = frame[frame["is_audiobook"]].copy()

    return {
        "full": frame,
        "songs": songs,
        "podcasts": podcasts,
        "audiobooks": audiobooks,
    }


def apply_dashboard_filters(
    df: pd.DataFrame,
    start_date,
    end_date,
    artists: list[str] | None = None,
    content_types: list[str] | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df

    mask = (pd.to_datetime(df["date"]) >= pd.to_datetime(start_date)) & (
        pd.to_datetime(df["date"]) <= pd.to_datetime(end_date)
    )
    filtered = df.loc[mask].copy()

    if artists:
        filtered = filtered[filtered["master_metadata_album_artist_name"].isin(artists)]

    if content_types:
        type_mask = np.zeros(len(filtered), dtype=bool)
        for ctype in content_types:
            if ctype == "Songs":
                type_mask |= filtered["is_song"].to_numpy()
            elif ctype == "Podcasts":
                type_mask |= filtered["is_podcast"].to_numpy()
            elif ctype == "Audiobooks":
                type_mask |= filtered["is_audiobook"].to_numpy()
        filtered = filtered[type_mask]

    return filtered
