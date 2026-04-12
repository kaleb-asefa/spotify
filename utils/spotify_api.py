from __future__ import annotations

import base64
import os
from typing import Any

import requests
import streamlit as st


TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1"


def _get_spotify_credentials() -> tuple[str | None, str | None]:
    client_id = None
    client_secret = None

    if hasattr(st, "secrets"):
        client_id = st.secrets.get("SPOTIFY_CLIENT_ID")
        client_secret = st.secrets.get("SPOTIFY_CLIENT_SECRET")

    client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")

    return client_id, client_secret


@st.cache_data(ttl=300, show_spinner=False)
def _get_access_token() -> str | None:
    client_id, client_secret = _get_spotify_credentials()
    if not client_id or not client_secret:
        return None

    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {"grant_type": "client_credentials"}

    try:
        response = requests.post(TOKEN_URL, data=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.RequestException:
        return None


def _api_get(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    token = _get_access_token()
    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def _parse_spotify_uri(uri: str | None) -> tuple[str, str] | None:
    if not uri or not isinstance(uri, str) or not uri.startswith("spotify:"):
        return None
    parts = uri.split(":")
    if len(parts) != 3:
        return None
    return parts[1], parts[2]


@st.cache_data(ttl=3600, show_spinner=False)
def get_track_metadata(track_uri: str | None, track_name: str | None = None, artist_name: str | None = None) -> dict[str, Any]:
    parsed = _parse_spotify_uri(track_uri)
    data = None

    if parsed and parsed[0] == "track":
        data = _api_get(f"/tracks/{parsed[1]}")

    if not data and track_name:
        query = f"track:{track_name}"
        if artist_name:
            query += f" artist:{artist_name}"
        search = _api_get("/search", params={"q": query, "type": "track", "limit": 1})
        items = (search or {}).get("tracks", {}).get("items", [])
        data = items[0] if items else None

    if not data:
        return {
            "name": track_name or "Unknown Track",
            "popularity": None,
            "external_url": None,
            "album_name": None,
            "album_release_date": None,
            "album_image": None,
            "artist_id": None,
            "artist_name": artist_name,
            "track_id": None,
        }

    album_images = data.get("album", {}).get("images", [])
    artists = data.get("artists", [])

    return {
        "name": data.get("name", track_name or "Unknown Track"),
        "popularity": data.get("popularity"),
        "external_url": (data.get("external_urls") or {}).get("spotify"),
        "album_name": (data.get("album") or {}).get("name"),
        "album_release_date": (data.get("album") or {}).get("release_date"),
        "album_image": album_images[0].get("url") if album_images else None,
        "artist_id": artists[0].get("id") if artists else None,
        "artist_name": artists[0].get("name") if artists else artist_name,
        "track_id": data.get("id"),
    }


@st.cache_data(ttl=3600, show_spinner=False)
def get_artist_metadata(artist_name: str) -> dict[str, Any]:
    if not artist_name:
        return {
            "name": "Unknown Artist",
            "genres": [],
            "popularity": None,
            "image": None,
            "external_url": None,
            "artist_id": None,
        }

    search = _api_get("/search", params={"q": f"artist:{artist_name}", "type": "artist", "limit": 1})
    items = (search or {}).get("artists", {}).get("items", [])
    if not items:
        return {
            "name": artist_name,
            "genres": [],
            "popularity": None,
            "image": None,
            "external_url": None,
            "artist_id": None,
        }

    artist = items[0]
    images = artist.get("images", [])
    return {
        "name": artist.get("name", artist_name),
        "genres": artist.get("genres", []),
        "popularity": artist.get("popularity"),
        "image": images[0].get("url") if images else None,
        "external_url": (artist.get("external_urls") or {}).get("spotify"),
        "artist_id": artist.get("id"),
    }


@st.cache_data(ttl=3600, show_spinner=False)
def get_album_metadata(album_name: str, artist_name: str | None = None) -> dict[str, Any]:
    if not album_name:
        return {
            "name": "Unknown Album",
            "release_date": None,
            "image": None,
            "external_url": None,
            "album_id": None,
            "artist_name": artist_name,
        }

    query = f"album:{album_name}"
    if artist_name:
        query += f" artist:{artist_name}"

    search = _api_get("/search", params={"q": query, "type": "album", "limit": 1})
    items = (search or {}).get("albums", {}).get("items", [])
    if not items:
        return {
            "name": album_name,
            "release_date": None,
            "image": None,
            "external_url": None,
            "album_id": None,
            "artist_name": artist_name,
        }

    album = items[0]
    images = album.get("images", [])
    artists = album.get("artists", [])
    return {
        "name": album.get("name", album_name),
        "release_date": album.get("release_date"),
        "image": images[0].get("url") if images else None,
        "external_url": (album.get("external_urls") or {}).get("spotify"),
        "album_id": album.get("id"),
        "artist_name": artists[0].get("name") if artists else artist_name,
    }


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_cover_image(image_url: str | None) -> str | None:
    # Keep image retrieval as a pass-through URL so Streamlit can load images lazily.
    return image_url if image_url else None