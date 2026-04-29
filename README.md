# Spotify Analytics Studio (React + Python API)

A modern split-stack Spotify analytics project with:

- React frontend (Vite) for advanced UI and chart-rich interaction
- FastAPI backend for loading, filtering, and aggregating Spotify history data
- Shared Python analytics utilities reused from the original project

## Architecture

```text
spotify_dashboard/
├── backend/
│   └── main.py                 # FastAPI analytics API
├── frontend/
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       ├── styles.css
│       └── components/
├── data/                       # Place Spotify JSON exports here
├── utils/                      # Reused preprocessing/loading utilities
├── app.py                      # Legacy Streamlit app (optional)
├── requirements.txt
└── README.md
```

## API Endpoints

- `GET /health`
- `GET /api/options`
- `GET /api/dashboard?start_date=...&end_date=...&artists=...&content_types=...`

`artists` and `content_types` are comma-separated values.

## Data Input

Place one or more Spotify JSON history exports in `data/`.

Expected fields include common Spotify export keys such as:

- `ts`
- `ms_played`
- `master_metadata_track_name`
- `master_metadata_album_artist_name`
- `master_metadata_album_album_name`
- `reason_start`
- `reason_end`
- `shuffle`
- `skipped`

## Quickstart

### 1) Start the Python backend

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### 2) Start the React frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173` and calls the backend at `http://127.0.0.1:8000` by default.

## Spotify Images (Artists + Albums)

The backend enriches `topArtists` and `favoriteAlbums` with image URLs.

- Primary source: Spotify Web API (requires credentials)
- Fallback source: Deezer public search API (no credentials required)

Set these environment variables before starting the backend:

```bash
export SPOTIFY_CLIENT_ID=your_client_id
export SPOTIFY_CLIENT_SECRET=your_client_secret
```

If credentials are not set, the backend uses Deezer as fallback. If neither provider returns a match, the frontend renders fallback placeholders.

## Optional Frontend Environment Variable

If your backend is hosted elsewhere, set:

```bash
VITE_API_BASE_URL=http://your-api-host:8000
```

## Notes

- CORS is enabled in the backend for local development.
- The original Streamlit app is kept for reference in `app.py`.
