import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getListeningTrends } from "../api";
import KpiCard from "../components/KpiCard";
import SectionCard from "../components/SectionCard";
import { useDashboard } from "../context/DashboardContext";

const STAT_COLORS = ["#ff7a59", "#f9c74f", "#43aa8b", "#4ea8de", "#9b5de5", "#f15bb5", "#8ecae6", "#ffe066"];

function formatNumber(value) {
  if (typeof value === "number") {
    return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  return value;
}

export default function ListeningTrendsPage() {
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
        const payload = await getListeningTrends(appliedFilters);
        if (active) {
          setData(payload);
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Unable to load listening trends.");
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

  const stats = data?.stats || {};
  const statItems = useMemo(() => {
    if (!stats || Object.keys(stats).length === 0) {
      return [];
    }
    return [
      { label: "Mean", value: `${formatNumber(stats.mean)} h/day` },
      { label: "Median", value: `${formatNumber(stats.median)} h/day` },
      { label: "Variance", value: formatNumber(stats.variance) },
      { label: "Std Dev", value: formatNumber(stats.std_dev) },
      { label: "P25", value: formatNumber(stats.p25) },
      { label: "P50", value: formatNumber(stats.p50) },
      { label: "P75", value: formatNumber(stats.p75) },
      { label: "P90", value: formatNumber(stats.p90) },
    ];
  }, [stats]);

  if (loading && !data) {
    return <div className="state-panel">Loading listening trends...</div>;
  }

  if (error && !data) {
    return <div className="state-panel error">{error}</div>;
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <h2>Listening Trends</h2>
        <p className="muted">Daily momentum, rolling averages, and cumulative growth across your timeline.</p>
      </header>

      {error ? <p className="inline-error">{error}</p> : null}

      <section className="chart-grid">
        <SectionCard title="Daily vs Rolling 7-Day Average" delay={0.05}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={data?.daily || []}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="date" hide />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="play_hours" stroke="#ff7a59" strokeWidth={2} />
                <Line type="monotone" dataKey="rolling_7d" stroke="#4ea8de" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>
      </section>

      <section className="chart-grid two-col">
        <SectionCard title="Weekly Listening" delay={0.1}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data?.weekly || []}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="date" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="play_hours" radius={[8, 8, 0, 0]} fill="#43aa8b" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>

        <SectionCard title="Monthly Listening" delay={0.15}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data?.monthly || []}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="date" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="play_hours" radius={[8, 8, 0, 0]} fill="#f9c74f" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>
      </section>

      <section className="chart-grid two-col">
        <SectionCard title="Yearly Comparison" delay={0.2}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data?.yearly || []}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="play_hours" radius={[8, 8, 0, 0]} fill="#9b5de5" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>

        <SectionCard title="Cumulative Hours" delay={0.25}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={data?.daily || []}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="date" hide />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="cumulative_hours" stroke="#ff7a59" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>
      </section>

      {statItems.length > 0 ? (
        <section className="kpi-grid compact">
          {statItems.map((item, index) => (
            <KpiCard
              key={item.label}
              label={item.label}
              value={item.value}
              accent={STAT_COLORS[index % STAT_COLORS.length]}
            />
          ))}
        </section>
      ) : null}
    </div>
  );
}
