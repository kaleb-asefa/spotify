import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
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

import { getTimePatterns } from "../api";
import SectionCard from "../components/SectionCard";
import { useDashboard } from "../context/DashboardContext";

function HeatmapGrid({ heatmap }) {
  const hours = heatmap?.x || [];
  const days = heatmap?.y || [];
  const values = heatmap?.z || [];
  const maxValue = useMemo(() => {
    const flat = values.flat();
    return flat.length ? Math.max(...flat) : 0;
  }, [values]);

  function cellColor(value) {
    if (!maxValue) {
      return "rgba(78, 168, 222, 0.18)";
    }
    const alpha = 0.15 + (value / maxValue) * 0.75;
    return `rgba(78, 168, 222, ${alpha.toFixed(2)})`;
  }

  return (
    <div
      className="heatmap-grid"
      style={{ gridTemplateColumns: `5rem repeat(${hours.length}, minmax(1.4rem, 1fr))` }}
    >
      <div className="heatmap-label" />
      {hours.map((hour) => (
        <div key={`h-${hour}`} className="heatmap-header">
          {hour}
        </div>
      ))}
      {days.map((day, rowIndex) => (
        <div key={day} className="heatmap-row">
          <div className="heatmap-label">{day}</div>
          {hours.map((hour, colIndex) => {
            const value = values[rowIndex]?.[colIndex] || 0;
            return (
              <div
                key={`${day}-${hour}`}
                className="heatmap-cell"
                style={{ background: cellColor(value) }}
                title={`${day} ${hour}:00 - ${value.toFixed(1)} min`}
              />
            );
          })}
        </div>
      ))}
    </div>
  );
}

export default function TimePatternIntelligencePage() {
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
        const payload = await getTimePatterns(appliedFilters);
        if (active) {
          setData(payload);
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Unable to load time pattern insights.");
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

  if (loading && !data) {
    return <div className="state-panel">Loading time patterns...</div>;
  }

  if (error && !data) {
    return <div className="state-panel error">{error}</div>;
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <h2>Time Pattern Intelligence</h2>
        <p className="muted">Discover seasonality, day-part shifts, and hourly rhythms in your listening.</p>
      </header>

      {error ? <p className="inline-error">{error}</p> : null}

      <SectionCard title="Listening Heatmap: Hour x Weekday" delay={0.05}>
        <HeatmapGrid heatmap={data?.heatmap} />
      </SectionCard>

      <section className="chart-grid two-col">
        <SectionCard title="Monthly Seasonality" delay={0.1}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={data?.seasonal || []}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="play_hours" stroke="#ff7a59" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>

        <SectionCard title="Night vs Day" delay={0.15}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data?.dayNight || []}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="day_period" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="hours" radius={[8, 8, 0, 0]} fill="#4ea8de" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>
      </section>

      <section className="chart-grid two-col">
        <SectionCard title="Weekday vs Weekend" delay={0.2}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data?.weekSegment || []}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="week_segment" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="hours" radius={[8, 8, 0, 0]} fill="#43aa8b" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>

        <SectionCard title="Hour-of-Day Curve" delay={0.25}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={data?.hourCurve || []}>
                <defs>
                  <linearGradient id="hourCurveGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#9b5de5" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#9b5de5" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="listening_hour" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="play_hours" stroke="#9b5de5" fill="url(#hourCurveGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>
      </section>
    </div>
  );
}
