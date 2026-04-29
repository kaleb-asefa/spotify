from __future__ import annotations

import base64
import os
import time
from functools import lru_cache
from typing import Any

import requests

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1"
DEEZER_API_BASE_URL = "https://api.deezer.com"

_token_cache: dict[str, Any] = {"token": None, "expires_at": 0.0}


def _get_spotify_credentials() -> tuple[str | None, str | None]:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    return client_id, client_secret


def _get_access_token() -> str | None:
    client_id, client_secret = _get_spotify_credentials()
    if not client_id or not client_secret:
        return None

    now = time.time()
    token = _token_cache.get("token")
    expires_at = float(_token_cache.get("expires_at") or 0.0)
    if token and now < (expires_at - 30):
        return token

    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {"grant_type": "client_credentials"}

    try:
        response = requests.post(TOKEN_URL, data=payload, headers=headers, timeout=15)
        response.raise_for_status()
        body = response.json()
    except requests.RequestException:
        return None

    access_token = body.get("access_token")
    expires_in = int(body.get("expires_in", 3600))
    if not access_token:
        return None

    _token_cache["token"] = access_token
    _token_cache["expires_at"] = now + expires_in
    return access_token


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


def _deezer_get(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        response = requests.get(f"{DEEZER_API_BASE_URL}{endpoint}", params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


@lru_cache(maxsize=512)
def search_artist(artist_name: str) -> dict[str, str | None]:
    if not artist_name:
        return {"image_url": None, "external_url": None}

    search = _api_get("/search", params={"q": f"artist:{artist_name}", "type": "artist", "limit": 1})
    items = (search or {}).get("artists", {}).get("items", [])
    if not items:
        deezer = _deezer_get("/search/artist", params={"q": f'artist:"{artist_name}"'})
        deezer_items = (deezer or {}).get("data", [])
        if not deezer_items:
            return {"image_url": None, "external_url": None}

        artist = deezer_items[0]
        return {
            "image_url": artist.get("picture_xl") or artist.get("picture_big") or artist.get("picture_medium"),
            "external_url": artist.get("link"),
        }

    artist = items[0]
    images = artist.get("images", [])
    return {
        "image_url": images[0].get("url") if images else None,
        "external_url": (artist.get("external_urls") or {}).get("spotify"),
    }


@lru_cache(maxsize=512)
def search_album(album_name: str, artist_name: str) -> dict[str, str | None]:
    if not album_name:
        return {"image_url": None, "external_url": None}

    query = f"album:{album_name}"
    if artist_name:
        query += f" artist:{artist_name}"

    search = _api_get("/search", params={"q": query, "type": "album", "limit": 1})
    items = (search or {}).get("albums", {}).get("items", [])
    if not items:
        deezer_query = f'album:"{album_name}"'
        if artist_name:
            deezer_query += f' artist:"{artist_name}"'

        deezer = _deezer_get("/search/album", params={"q": deezer_query})
        deezer_items = (deezer or {}).get("data", [])
        if not deezer_items:
            return {"image_url": None, "external_url": None}

        album = deezer_items[0]
        return {
            "image_url": album.get("cover_xl") or album.get("cover_big") or album.get("cover_medium"),
            "external_url": album.get("link"),
        }

    album = items[0]
    images = album.get("images", [])
    return {
        "image_url": images[0].get("url") if images else None,
        "external_url": (album.get("external_urls") or {}).get("spotify"),
    }
