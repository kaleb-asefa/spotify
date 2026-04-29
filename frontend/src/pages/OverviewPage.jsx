import { useEffect, useMemo, useState } from "react";
import { Sparkles } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getOverview } from "../api";
import KpiCard from "../components/KpiCard";
import SectionCard from "../components/SectionCard";
import { useDashboard } from "../context/DashboardContext";

const KPI_COLORS = ["#ff7a59", "#f9c74f", "#43aa8b", "#4ea8de", "#9b5de5", "#f15bb5"];

function formatNumber(value) {
  if (typeof value === "number") {
    return value.toLocaleString();
  }
  return value;
}

export default function OverviewPage() {
  const { appliedFilters, setApplying, options } = useDashboard();
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
        const payload = await getOverview(appliedFilters);
        if (active) {
          setData(payload);
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Unable to load overview insights.");
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

  const kpis = data?.kpis;
  const charts = data?.charts;
  const highlights = data?.highlights;
  const activeHourLabel = Number.isFinite(highlights?.mostActiveHour)
    ? String(highlights.mostActiveHour).padStart(2, "0")
    : "--";
  const activeDayLabel = highlights?.mostActiveDay || "--";

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
    return <div className="state-panel">Loading overview...</div>;
  }

  if (error && !data) {
    return <div className="state-panel error">{error}</div>;
  }

  return (
    <div className="page-stack">
      <section className="hero">
        <div>
          <p className="eyebrow">Executive Overview</p>
          <h2>Your listening identity, summarized at a glance.</h2>
          <p className="hero-copy">
            Track your totals, peak moments, and engagement signals across every listening session.
          </p>
        </div>
        <div className="hero-pill">
          <Sparkles size={18} />
          <span>{options?.filesLoaded || 0} files loaded</span>
        </div>
      </section>

      {error ? <p className="inline-error">{error}</p> : null}

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
        <SectionCard title="Listening by Hour" delay={0.05}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={charts?.hourly || []}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="listening_hour" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="play_hours" radius={[8, 8, 0, 0]} fill="#ff7a59" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>

        <SectionCard title="Listening by Weekday" delay={0.1}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={charts?.weekday || []}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="weekday_name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="play_hours" radius={[8, 8, 0, 0]} fill="#4ea8de" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>
      </section>

      <SectionCard title="Summary Insights" delay={0.15}>
        <div className="content-box">
          <p>
            Peak engagement happens around {activeHourLabel}:00 and is strongest on {activeDayLabel}. You logged{" "}
            {kpis ? kpis.totalHours.toFixed(1) : "--"} total hours with shuffle used{" "}
            {kpis ? `${kpis.shuffleRate.toFixed(1)}%` : "--"} of the time.
          </p>
          <p className="muted">Rows in current filter: {data?.meta?.rows ?? 0}</p>
        </div>
      </SectionCard>
    </div>
  );
}
