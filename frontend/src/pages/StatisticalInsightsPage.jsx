import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getStatisticalInsights } from "../api";
import SectionCard from "../components/SectionCard";
import { useDashboard } from "../context/DashboardContext";

function buildHistogram(values, bins = 20) {
  if (!values || values.length === 0) {
    return [];
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    return [{ range: `${min.toFixed(1)}-${max.toFixed(1)}`, count: values.length }];
  }
  const step = (max - min) / bins;
  const counts = Array.from({ length: bins }, () => 0);
  values.forEach((value) => {
    const idx = Math.min(Math.floor((value - min) / step), bins - 1);
    counts[idx] += 1;
  });
  return counts.map((count, index) => {
    const start = min + index * step;
    const end = start + step;
    return {
      range: `${start.toFixed(1)}-${end.toFixed(1)}`,
      count,
    };
  });
}

export default function StatisticalInsightsPage() {
  const { appliedFilters, setApplying } = useDashboard();
  const [data, setData] = useState(null);
  const [threshold, setThreshold] = useState(2.5);
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
        const payload = await getStatisticalInsights(appliedFilters, threshold);
        if (active) {
          setData(payload);
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Unable to load statistical insights.");
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
  }, [appliedFilters, threshold, setApplying]);

  const histogram = useMemo(() => buildHistogram(data?.distribution || []), [data]);
  const hypothesis = data?.hypothesis || {};

  if (loading && !data) {
    return <div className="state-panel">Loading statistical insights...</div>;
  }

  if (error && !data) {
    return <div className="state-panel error">{error}</div>;
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <h2>Statistical Insight Section</h2>
        <p className="muted">Confidence intervals, anomaly detection, and hypothesis testing.</p>
      </header>

      {error ? <p className="inline-error">{error}</p> : null}

      <SectionCard title="Confidence Interval" delay={0.05}>
        <p>
          {data?.confidenceInterval
            ? `95% CI for average daily hours: ${data.confidenceInterval.lower.toFixed(2)} to ${data.confidenceInterval.upper.toFixed(2)}.`
            : "Not enough daily samples for confidence interval estimation."}
        </p>
      </SectionCard>

      <SectionCard title="Anomaly Threshold" delay={0.1}>
        <div className="slider-row">
          <span>Threshold: {threshold.toFixed(1)}</span>
          <input
            type="range"
            min="1.5"
            max="4.0"
            step="0.1"
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
          />
        </div>
      </SectionCard>

      <section className="chart-grid two-col">
        <SectionCard title="Outlier Listening Days" delay={0.15}>
          {(data?.anomalies || []).length === 0 ? (
            <p>No anomaly days detected at the current threshold.</p>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Hours</th>
                    <th>Z-Score</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.anomalies || []).map((row) => (
                    <tr key={row.date}>
                      <td>{row.date}</td>
                      <td>{row.play_hours.toFixed(2)}</td>
                      <td>{row.zscore.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>

        <SectionCard title="Distribution of Daily Hours" delay={0.2}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={histogram}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="range" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" radius={[8, 8, 0, 0]} fill="#ff7a59" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>
      </section>

      <SectionCard title="Weekday vs Weekend Hypothesis Test" delay={0.25}>
        {hypothesis.status !== "ok" ? (
          <p>Insufficient data for hypothesis testing.</p>
        ) : (
          <div className="content-box">
            <p>
              Weekday mean: {hypothesis.weekday_mean.toFixed(2)} min/day | Weekend mean: {hypothesis.weekend_mean.toFixed(2)} min/day
            </p>
            <p>
              t-statistic: {hypothesis.t_stat.toFixed(3)} | p-value: {hypothesis.p_value.toFixed(4)}
            </p>
            <p>
              {hypothesis.p_value < 0.05
                ? "Result is statistically significant at alpha=0.05. Weekday and weekend listening differ."
                : "Result is not statistically significant at alpha=0.05. No strong evidence of a difference."}
            </p>
          </div>
        )}
      </SectionCard>
    </div>
  );
}
