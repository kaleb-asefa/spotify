import { useEffect, useMemo, useState } from "react";

import { getArtistSongAnalytics } from "../api";
import KpiCard from "../components/KpiCard";
import MediaThumb from "../components/MediaThumb";
import SectionCard from "../components/SectionCard";
import { useDashboard } from "../context/DashboardContext";

const KPI_COLORS = ["#ff7a59", "#4ea8de", "#f9c74f", "#43aa8b"];

export default function ArtistSongAnalyticsPage() {
  const { appliedFilters, setApplying } = useDashboard();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!appliedFilters) {
      return;
    }

    let active = true;

    async function load() {
      try {
        setLoading(true);
        setError("");
        const payload = await getArtistSongAnalytics(appliedFilters);
        if (active) {
          setData(payload);
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Unable to load artist and song analytics.");
        }
      } finally {
        if (active) {
          setLoading(false);
          setApplying(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [appliedFilters, setApplying]);

  const featured = data?.featuredTrack;
  const wrapped = data?.wrappedInsights || {};

  const insightCards = useMemo(() => {
    return [
      {
        label: "Late Night Obsession",
        value: wrapped.lateNightTrack?.[0]?.master_metadata_track_name || "N/A",
        meta: wrapped.lateNightTrack?.[0]?.plays ? `${wrapped.lateNightTrack[0].plays} plays` : "",
      },
      {
        label: "Most Replayed Artist",
        value: wrapped.mostReplayedArtist?.[0]?.master_metadata_album_artist_name || "N/A",
        meta: wrapped.mostReplayedArtist?.[0]?.plays ? `${wrapped.mostReplayedArtist[0].plays} plays` : "",
      },
      {
        label: "Weekend Anthem",
        value: wrapped.weekendAnthem?.[0]?.master_metadata_track_name || "N/A",
        meta: wrapped.weekendAnthem?.[0]?.plays ? `${wrapped.weekendAnthem[0].plays} plays` : "",
      },
      {
        label: "Top Artist This Year",
        value: wrapped.topArtistYear?.items?.[0]?.master_metadata_album_artist_name || "N/A",
        meta: wrapped.topArtistYear?.items?.[0]?.plays ? `${wrapped.topArtistYear.items[0].plays} plays` : "",
      },
    ];
  }, [wrapped]);

  if (loading && !data) {
    return <div className="state-panel">Loading artist and song analytics...</div>;
  }

  if (error && !data) {
    return <div className="state-panel error">{error}</div>;
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <h2>Artist & Song Analytics</h2>
        <p className="muted">Spotlight your top artists, albums, and the tracks you return to the most.</p>
      </header>

      {error ? <p className="inline-error">{error}</p> : null}

      <section className="kpi-grid compact">
        <KpiCard
          label="Artist Diversity Score"
          value={(data?.diversityScore || 0).toFixed(3)}
          accent={KPI_COLORS[0]}
        />
      </section>

      <SectionCard title="Featured Track" delay={0.05}>
        {featured ? (
          <div className="featured-track">
            <MediaThumb
              imageUrl={featured.imageUrl}
              altText={featured.track}
              fallbackText={featured.album}
            />
            <div className="featured-meta">
              <h3>{featured.track}</h3>
              <p className="muted">
                {featured.artist} • {featured.album}
              </p>
              <div className="featured-stats">
                <div>
                  <span className="stat-label">Streams</span>
                  <span className="stat-value">{featured.streams.toLocaleString()}</span>
                </div>
                <div>
                  <span className="stat-label">Listening Time</span>
                  <span className="stat-value">{featured.listeningMinutes.toFixed(1)} min</span>
                </div>
                <div>
                  <span className="stat-label">First Play</span>
                  <span className="stat-value">{featured.firstPlay}</span>
                </div>
                <div>
                  <span className="stat-label">Last Play</span>
                  <span className="stat-value">{featured.lastPlay}</span>
                </div>
              </div>
              {featured.externalUrl ? (
                <a className="link-pill" href={featured.externalUrl} target="_blank" rel="noreferrer">
                  Open Album
                </a>
              ) : null}
            </div>
          </div>
        ) : (
          <p>No featured track data available.</p>
        )}
      </SectionCard>

      <section className="chart-grid">
        <SectionCard title="Top Albums Spotlight" delay={0.1}>
          <div className="media-card-grid">
            {(data?.topAlbums || []).map((album) => (
              <article key={`${album.album}-${album.artist}`} className="media-card-item">
                <div className="media-card-top">
                  <MediaThumb
                    imageUrl={album.imageUrl}
                    altText={album.album}
                    fallbackText={album.album}
                  />
                </div>
                <p className="media-card-title">{album.album}</p>
                <p className="media-card-subtitle">{album.artist}</p>
                <p className="media-card-value">{album.playCount.toLocaleString()} plays</p>
                {album.externalUrl ? (
                  <a className="link-pill" href={album.externalUrl} target="_blank" rel="noreferrer">
                    Open Album
                  </a>
                ) : null}
              </article>
            ))}
          </div>
        </SectionCard>
      </section>

      <section className="chart-grid">
        <SectionCard title="Artist Spotlight" delay={0.15}>
          <div className="media-card-grid">
            {(data?.topArtists || []).map((artist, index) => (
              <article key={artist.artist} className="media-card-item">
                <div className="media-card-top">
                  <span className="rank">{index + 1}</span>
                  <MediaThumb
                    imageUrl={artist.imageUrl}
                    altText={artist.artist}
                    fallbackText={artist.artist}
                  />
                </div>
                <p className="media-card-title">{artist.artist}</p>
                <p className="media-card-subtitle">{artist.totalPlays.toLocaleString()} plays</p>
                <p className="media-card-value">Share: {artist.share}%</p>
                {artist.externalUrl ? (
                  <a className="link-pill" href={artist.externalUrl} target="_blank" rel="noreferrer">
                    Open Artist
                  </a>
                ) : null}
              </article>
            ))}
          </div>
        </SectionCard>
      </section>

      <section className="insight-grid">
        {insightCards.map((card) => (
          <div key={card.label} className="insight-card">
            <span className="insight-label">{card.label}</span>
            <span className="insight-value">{card.value}</span>
            <span className="muted">{card.meta}</span>
          </div>
        ))}
      </section>

      <section className="chart-grid two-col">
        <SectionCard title="Top Artists" delay={0.2}>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Artist</th>
                  <th>Plays</th>
                  <th>Hours</th>
                </tr>
              </thead>
              <tbody>
                {(data?.rankings?.topArtists || []).map((row) => (
                  <tr key={row.master_metadata_album_artist_name}>
                    <td>{row.master_metadata_album_artist_name}</td>
                    <td>{row.plays}</td>
                    <td>{row.hours.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>

        <SectionCard title="Top Tracks" delay={0.25}>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Track</th>
                  <th>Artist</th>
                  <th>Plays</th>
                </tr>
              </thead>
              <tbody>
                {(data?.rankings?.topTracks || []).map((row) => (
                  <tr key={`${row.master_metadata_track_name}-${row.master_metadata_album_artist_name}`}>
                    <td>{row.master_metadata_track_name}</td>
                    <td>{row.master_metadata_album_artist_name}</td>
                    <td>{row.plays}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </section>

      <section className="chart-grid two-col">
        <SectionCard title="Top Albums" delay={0.3}>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Album</th>
                  <th>Plays</th>
                  <th>Hours</th>
                </tr>
              </thead>
              <tbody>
                {(data?.rankings?.topAlbums || []).map((row) => (
                  <tr key={row.master_metadata_album_album_name}>
                    <td>{row.master_metadata_album_album_name}</td>
                    <td>{row.plays}</td>
                    <td>{row.hours.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>

        <SectionCard title="Repeated Listening" delay={0.35}>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Track</th>
                  <th>Artist</th>
                  <th>Plays</th>
                </tr>
              </thead>
              <tbody>
                {(data?.rankings?.repeatedTracks || []).map((row) => (
                  <tr key={`${row.master_metadata_track_name}-${row.master_metadata_album_artist_name}`}>
                    <td>{row.master_metadata_track_name}</td>
                    <td>{row.master_metadata_album_artist_name}</td>
                    <td>{row.play_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </section>
    </div>
  );
}
