import { useEffect, useState } from "react";

import { trainSkipModel } from "../api";
import SectionCard from "../components/SectionCard";
import { useDashboard } from "../context/DashboardContext";

function toReportRows(report) {
  if (!report) {
    return [];
  }
  return Object.entries(report)
    .filter(([, metrics]) => metrics && typeof metrics === "object")
    .map(([label, metrics]) => ({
      label,
      precision: metrics.precision,
      recall: metrics.recall,
      f1Score: metrics["f1-score"],
      support: metrics.support,
    }));
}

export default function MachineLearningPage() {
  const { appliedFilters, setApplying } = useDashboard();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [training, setTraining] = useState(false);

  useEffect(() => {
    setApplying(false);
  }, [setApplying]);

  async function handleTrain() {
    if (!appliedFilters) {
      return;
    }

    try {
      setTraining(true);
      setError("");
      const payload = await trainSkipModel(appliedFilters);
      setResult(payload);
    } catch (err) {
      setError(err.message || "Unable to train skip prediction model.");
    } finally {
      setTraining(false);
    }
  }

  const rows = toReportRows(result?.report);

  return (
    <div className="page-stack">
      <header className="page-header">
        <h2>Machine Learning</h2>
        <p className="muted">Train a logistic regression model to estimate skip probability.</p>
      </header>

      {error ? <p className="inline-error">{error}</p> : null}

      <SectionCard title="Model Overview" delay={0.05}>
        <p>
          This section trains a logistic regression model using play duration, listening hour, platform, start/end
          context, shuffle, offline, and incognito signals.
        </p>
        <button className="apply-btn" onClick={handleTrain} disabled={training}>
          {training ? "Training..." : "Train Skip Prediction Model"}
        </button>
      </SectionCard>

      {result?.status === "insufficient_data" ? (
        <SectionCard title="Model Status" delay={0.1}>
          <p>Not enough balanced song data to train a robust classifier.</p>
        </SectionCard>
      ) : null}

      {result?.status === "ok" ? (
        <section className="chart-grid two-col">
          <SectionCard title="Model Metrics" delay={0.15}>
            <div className="metric-grid">
              <div>
                <span className="stat-label">Accuracy</span>
                <span className="stat-value">{result.accuracy.toFixed(3)}</span>
              </div>
              <div>
                <span className="stat-label">ROC AUC</span>
                <span className="stat-value">{result.roc_auc.toFixed(3)}</span>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Classification Report" delay={0.2}>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Label</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1</th>
                    <th>Support</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.label}>
                      <td>{row.label}</td>
                      <td>{row.precision.toFixed(2)}</td>
                      <td>{row.recall.toFixed(2)}</td>
                      <td>{row.f1Score.toFixed(2)}</td>
                      <td>{row.support}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>
        </section>
      ) : null}
    </div>
  );
}
