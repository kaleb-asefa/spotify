from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd


EXPECTED_COLUMNS = [
    "ts",
    "platform",
    "ms_played",
    "conn_country",
    "ip_addr",
    "master_metadata_track_name",
    "master_metadata_album_artist_name",
    "master_metadata_album_album_name",
    "spotify_track_uri",
    "episode_name",
    "episode_show_name",
    "spotify_episode_uri",
    "audiobook_title",
    "audiobook_uri",
    "audiobook_chapter_uri",
    "audiobook_chapter_title",
    "reason_start",
    "reason_end",
    "shuffle",
    "skipped",
    "offline",
    "offline_timestamp",
    "incognito_mode",
]


def _safe_records_from_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        raw_text = f.read().strip()

    if not raw_text:
        return []

    try:
        payload = json.loads(raw_text)
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if isinstance(payload, dict):
            return [payload]
    except json.JSONDecodeError:
        pass

    records = []
    for line in raw_text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                records.append(row)
        except json.JSONDecodeError:
            continue
    return records


def discover_json_files(data_dir: str | Path) -> list[Path]:
    base = Path(data_dir)
    if not base.exists():
        return []
    return sorted([p for p in base.rglob("*.json") if p.is_file()])


def load_spotify_data(data_dir: str | Path) -> pd.DataFrame:
    files = discover_json_files(data_dir)
    if not files:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    chunks: list[pd.DataFrame] = []
    for path in files:
        records = _safe_records_from_json(path)
        if not records:
            continue
        chunk = pd.DataFrame.from_records(records)
        chunk["source_file"] = path.name
        chunks.append(chunk)

    if not chunks:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    df = pd.concat(chunks, ignore_index=True, sort=False)

    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    return df
