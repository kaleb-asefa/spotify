import { NavLink, Outlet } from "react-router-dom";

import { useDashboard } from "../context/DashboardContext";
import FilterPanel from "./FilterPanel";

const navLinks = [
  { to: "/", label: "Overview" },
  { to: "/listening-trends", label: "Listening Trends" },
  { to: "/artist-song-analytics", label: "Artist & Song" },
  { to: "/behavior-analysis", label: "Behavior" },
  { to: "/time-pattern-intelligence", label: "Time Patterns" },
  { to: "/statistical-insights", label: "Statistics" },
  { to: "/machine-learning", label: "Machine Learning" },
];

export default function DashboardLayout() {
  const { initializing, optionsError } = useDashboard();

  if (initializing) {
    return <div className="state-panel">Loading your analytics studio...</div>;
  }

  if (optionsError) {
    return <div className="state-panel error">{optionsError}</div>;
  }

  return (
    <div className="page-shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />

      <main className="layout">
        <header className="topbar">
          <div className="brand">
            <p className="eyebrow">Spotify Intelligence Console</p>
            <h1>Spotify Analytics Studio</h1>
            <p className="hero-copy">
              Navigate every layer of your listening history with curated insights, charts, and predictive modeling.
            </p>
          </div>
          <nav className="nav-links" aria-label="Primary">
            {navLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  isActive ? "nav-link active" : "nav-link"
                }
                end={link.to === "/"}
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
        </header>

        <FilterPanel />

        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
