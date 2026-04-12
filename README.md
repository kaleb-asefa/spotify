# Spotify Personal Listening Analytics Dashboard

A complete end-to-end, portfolio-quality data analytics dashboard built with Python and Streamlit using exported Spotify JSON listening history.

## Features

- Robust loading of multiple Spotify JSON files from `data/`
- Dedicated preprocessing pipeline with feature engineering and sessionization
- Executive KPI overview with listening behavior summaries
- Listening trends: daily, weekly, monthly, yearly, rolling average, cumulative analysis
- Artist and track intelligence with diversity scoring and repeated-play discovery
- Behavior analytics from start/end reasons, shuffle, skip, offline, incognito, and platform fields
- Time pattern intelligence including interactive heatmaps and seasonality
- Statistical insights with confidence intervals, anomaly detection, and hypothesis testing
- Machine learning section: skip probability prediction via logistic regression
- Spotify Web API enrichment for album covers, artist images, genres, popularity, release dates, and Spotify links
- Spotify Wrapped style visual sections: Featured Song Obsession, Top Albums Spotlight, Artist Spotlight, and narrative insight cards

## Project Structure

```text
spotify_dashboard/
├── app.py
├── pages/
├── utils/
│   ├── loader.py
│   ├── preprocessing.py
│   ├── plots.py
│   └── stats.py
├── data/
├── models/
├── assets/
├── requirements.txt
└── README.md
```

## Data Input Format

The app expects Spotify export JSON records containing fields such as:

- `ts`
- `ms_played`
- `master_metadata_track_name`
- `master_metadata_album_artist_name`
- `master_metadata_album_album_name`
- `reason_start`
- `reason_end`
- `shuffle`
- `skipped`
- `offline`
- `incognito_mode`

and related podcast/audiobook fields.

## Quickstart

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Place your Spotify JSON export files inside `data/`.
4. (Optional but recommended) add Spotify API credentials.

Create `.streamlit/secrets.toml`:

```toml
SPOTIFY_CLIENT_ID = "your_client_id"
SPOTIFY_CLIENT_SECRET = "your_client_secret"
```

5. Run the app:

```bash
streamlit run app.py
```

## Portfolio Positioning

This project demonstrates:

- data cleaning and data quality handling
- exploratory data analysis and dashboard storytelling
- inferential statistics (CI, z-score anomalies, hypothesis testing)
- machine learning workflow and model interpretation
- production-style modular Python architecture

## Notes

- For best results, include multiple months of listening history.
- The ML section requires enough song rows and both skipped/non-skipped examples.
- Without Spotify credentials, the dashboard still runs using listening-history-only analytics, with image/metadata fallbacks.
