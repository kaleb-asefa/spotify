import { useEffect, useMemo, useState } from "react";
import { Filter, Sparkles } from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getDashboard, getOptions } from "./api";
import KpiCard from "./components/KpiCard";
import SectionCard from "./components/SectionCard";

const KPI_COLORS = ["#ff7a59", "#f9c74f", "#43aa8b", "#4ea8de", "#9b5de5", "#f15bb5"];

function formatNumber(value) {
  if (typeof value === "number") {
    return value.toLocaleString();
  }
  return value;
}

function MediaThumb({ imageUrl, altText, fallbackText }) {
  if (imageUrl) {
    return <img src={imageUrl} alt={altText} className="media-thumb" loading="lazy" />;
  }

  const initial = (fallbackText || "?").trim().charAt(0).toUpperCase() || "?";
  return <div className="media-thumb media-thumb-fallback">{initial}</div>;
}

export default function App() {
  const [options, setOptions] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [selectedArtists, setSelectedArtists] = useState([]);
  const [contentTypes, setContentTypes] = useState(["Songs", "Podcasts", "Audiobooks"]);
  const [mediaView, setMediaView] = useState("artists");

  useEffect(() => {
    async function bootstrap() {
      try {
        setLoading(true);
        const optionPayload = await getOptions();
        setOptions(optionPayload);

        if (optionPayload?.dateRange) {
          setStartDate(optionPayload.dateRange.min);
          setEndDate(optionPayload.dateRange.max);

          const firstData = await getDashboard({
            start_date: optionPayload.dateRange.min,
            end_date: optionPayload.dateRange.max,
            content_types: "Songs,Podcasts,Audiobooks",
          });
          setData(firstData);
        }
      } catch (err) {
        setError(err.message || "Unable to load dashboard.");
      } finally {
        setLoading(false);
      }
    }

    bootstrap();
  }, []);

  async function applyFilters() {
    try {
      setLoading(true);
      setError("");
      const payload = await getDashboard({
        start_date: startDate,
        end_date: endDate,
        artists: selectedArtists.join(","),
        content_types: contentTypes.join(","),
      });
      setData(payload);
    } catch (err) {
      setError(err.message || "Unable to update dashboard.");
    } finally {
      setLoading(false);
    }
  }

  function toggleContentType(name) {
    setContentTypes((prev) => {
      if (prev.includes(name)) {
        return prev.filter((item) => item !== name);
      }
      return [...prev, name];
    });
  }

  const kpis = data?.kpis;
  const charts = data?.charts;

  const mediaViewConfig = {
    artists: {
      label: "Artists",
      items: charts?.topArtists || [],
      getKey: (item, idx) => `${item.artist}-${idx}`,
      getTitle: (item) => item.artist || "Unknown Artist",
      getSubtitle: () => "Top Artist",
      getValue: (item) => `${item.play_hours.toFixed(1)}h`,
      getImage: (item) => item.image_url,
      getFallback: (item) => item.artist,
    },
    albums: {
      label: "Albums",
      items: charts?.favoriteAlbums || [],
      getKey: (item, idx) => `${item.album}-${item.artist}-${idx}`,
      getTitle: (item) => item.album || "Unknown Album",
      getSubtitle: (item) => item.artist || "Unknown Artist",
      getValue: (item) => `${item.play_hours.toFixed(1)}h`,
      getImage: (item) => item.image_url,
      getFallback: (item) => item.album,
    },
    tracks: {
      label: "Tracks",
      items: charts?.topTracks || [],
      getKey: (item, idx) => `${item.track}-${idx}`,
      getTitle: (item) => item.track || "Unknown Track",
      getSubtitle: () => "Top Track",
      getValue: (item) => `${item.play_hours.toFixed(1)}h`,
      getImage: () => null,
      getFallback: (item) => item.track,
    },
  };

  const activeMedia = mediaViewConfig[mediaView];

  const kpiItems = useMemo(() => {
    if (!kpis) {
      return [];
    }
    return [
      { label: "Total Listening Hours", value: kpis.totalHours.toFixed(1) },
      { label: "Tracks Played", value: formatNumber(kpis.tracksPlayed) },
      { label: "Unique Artists", value: formatNumber(kpis.uniqueArtists) },
      { label: "Unique Albums", value: formatNumber(kpis.uniqueAlbums) },
      { label: "Skip Rate", value: `${kpis.skipRate.toFixed(1)}%` },
      { label: "Shuffle Rate", value: `${kpis.shuffleRate.toFixed(1)}%` },
    ];
  }, [kpis]);

  if (loading && !data) {
    return <div className="state-panel">Loading your analytics studio...</div>;
  }

  if (error && !data) {
    return <div className="state-panel error">{error}</div>;
  }

  return (
    <div className="page-shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />

      <main className="layout">
        <header className="hero">
          <div>
            <p className="eyebrow">Spotify Intelligence Console</p>
            <h1>Your listening identity, reimagined as a modern analytics studio.</h1>
            <p className="hero-copy">
              Explore behavior, peaks, artists, and platform usage through a high-fidelity React dashboard backed by your Python analytics API.
            </p>
          </div>
          <div className="hero-pill">
            <Sparkles size={18} />
            <span>{options?.filesLoaded || 0} files loaded</span>
          </div>
        </header>

        <section className="filter-panel">
          <div className="filter-title">
            <Filter size={18} />
            <h2>Filters</h2>
          </div>

          <div className="filter-grid">
            <label>
              Start date
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </label>
            <label>
              End date
              <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </label>
            <label>
              Artists
              <select
                multiple
                value={selectedArtists}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions).map((option) => option.value);
                  setSelectedArtists(values);
                }}
              >
                {(options?.artists || []).map((artist) => (
                  <option key={artist} value={artist}>
                    {artist}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <button className="apply-btn" onClick={applyFilters} disabled={loading}>
            {loading ? "Updating..." : "Apply Filters"}
          </button>
          {error ? <p className="inline-error">{error}</p> : null}
        </section>

        <section className="kpi-grid">
          {kpiItems.map((item, index) => (
            <KpiCard
              key={item.label}
              label={item.label}
              value={item.value}
              accent={KPI_COLORS[index % KPI_COLORS.length]}
            />
          ))}
        </section>

        <section className="chart-grid two-col">
          <SectionCard title="Daily Listening Timeline" delay={0.05}>
            <div className="chart-box">
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={charts?.daily || []}>
                  <defs>
                    <linearGradient id="dailyGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ff7a59" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#ff7a59" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                  <XAxis dataKey="date" hide />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="play_hours" stroke="#ff7a59" fill="url(#dailyGradient)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>

          <SectionCard title="Hourly Rhythm" delay={0.1}>
            <div className="chart-box">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={charts?.hourly || []}>
                  <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                  <XAxis dataKey="listening_hour" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="play_hours" radius={[8, 8, 0, 0]} fill="#4ea8de" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>
        </section>

        <section className="chart-grid">
          <SectionCard title="Top Library Explorer" delay={0.15}>
            <div className="view-bar" role="tablist" aria-label="media toggle">
              {Object.entries(mediaViewConfig).map(([key, config]) => (
                <button
                  key={key}
                  className={`view-pill ${mediaView === key ? "active" : ""}`}
                  onClick={() => setMediaView(key)}
                  role="tab"
                  aria-selected={mediaView === key}
                >
                  {config.label}
                </button>
              ))}
            </div>

            <div className="media-card-grid">
              {activeMedia.items.map((item, idx) => (
                <article key={activeMedia.getKey(item, idx)} className="media-card-item">
                  <div className="media-card-top">
                    <span className="rank">{idx + 1}</span>
                    <MediaThumb
                      imageUrl={activeMedia.getImage(item)}
                      altText={activeMedia.getTitle(item)}
                      fallbackText={activeMedia.getFallback(item)}
                    />
                  </div>
                  <p className="media-card-title">{activeMedia.getTitle(item)}</p>
                  <p className="media-card-subtitle">{activeMedia.getSubtitle(item)}</p>
                  <p className="media-card-value">{activeMedia.getValue(item)}</p>
                </article>
              ))}
            </div>
          </SectionCard>
        </section>
      </main>
    </div>
  );
}
