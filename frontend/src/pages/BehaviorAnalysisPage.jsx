import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getBehaviorAnalysis } from "../api";
import SectionCard from "../components/SectionCard";
import { useDashboard } from "../context/DashboardContext";

const PIE_COLORS = ["#ff7a59", "#4ea8de", "#f9c74f", "#43aa8b"];

function sliceTop(items, count) {
  return (items || []).slice(0, count);
}

export default function BehaviorAnalysisPage() {
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
        const payload = await getBehaviorAnalysis(appliedFilters);
        if (active) {
          setData(payload);
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Unable to load behavior analysis.");
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

  const startCounts = useMemo(() => sliceTop(data?.startCounts, 12), [data]);
  const endCounts = useMemo(() => sliceTop(data?.endCounts, 12), [data]);
  const skipByReason = useMemo(() => sliceTop(data?.skipByReason, 12), [data]);

  if (loading && !data) {
    return <div className="state-panel">Loading behavior analysis...</div>;
  }

  if (error && !data) {
    return <div className="state-panel error">{error}</div>;
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <h2>Listening Behavior Analysis</h2>
        <p className="muted">Explore skip behavior, device context, and how sessions start or end.</p>
      </header>

      {error ? <p className="inline-error">{error}</p> : null}

      <section className="chart-grid two-col">
        <SectionCard title="How Tracks Start" delay={0.05}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={startCounts}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="reason_start" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" radius={[8, 8, 0, 0]} fill="#ff7a59" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>

        <SectionCard title="Why Tracks End" delay={0.1}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={endCounts}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="reason_end" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" radius={[8, 8, 0, 0]} fill="#4ea8de" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>
      </section>

      <section className="chart-grid two-col">
        <SectionCard title="Skip Rate by End Reason" delay={0.15}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={skipByReason}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="reason_end" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="skip_rate" radius={[8, 8, 0, 0]} fill="#f9c74f" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>

        <SectionCard title="Shuffle vs Skip" delay={0.2}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data?.shuffleCompare || []}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="shuffle" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="skip_rate" radius={[8, 8, 0, 0]} fill="#43aa8b" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>
      </section>

      <section className="chart-grid two-col">
        <SectionCard title="Offline vs Online Listening" delay={0.25}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={data?.offlineShare || []} dataKey="hours" nameKey="offline" outerRadius={90}>
                  {(data?.offlineShare || []).map((entry, index) => (
                    <Cell key={entry.offline} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>

        <SectionCard title="Incognito Mode Usage" delay={0.3}>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data?.incognitoShare || []}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="incognito_mode" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="hours" radius={[8, 8, 0, 0]} fill="#9b5de5" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>
      </section>

      <SectionCard title="Platform Trends" delay={0.35}>
        <div className="chart-box">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={sliceTop(data?.platformUsage, 15)}>
              <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.15)" />
              <XAxis dataKey="platform" hide />
              <YAxis />
              <Tooltip />
              <Bar dataKey="plays" radius={[8, 8, 0, 0]} fill="#ff7a59" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </SectionCard>
    </div>
  );
}
