import { Filter } from "lucide-react";

import { useDashboard } from "../context/DashboardContext";

export default function FilterPanel() {
  const { options, filters, setFilters, applyFilters, applying } = useDashboard();
  const contentTypeOptions = options?.contentTypes || ["Songs", "Podcasts", "Audiobooks"];

  function toggleContentType(name) {
    setFilters((prev) => {
      if (prev.contentTypes.includes(name)) {
        return { ...prev, contentTypes: prev.contentTypes.filter((item) => item !== name) };
      }
      return { ...prev, contentTypes: [...prev.contentTypes, name] };
    });
  }

  return (
    <section className="filter-panel">
      <div className="filter-title">
        <Filter size={18} />
        <h2>Filters</h2>
      </div>

      <div className="filter-grid">
        <label>
          Start date
          <input
            type="date"
            value={filters.startDate}
            onChange={(e) => setFilters((prev) => ({ ...prev, startDate: e.target.value }))}
          />
        </label>
        <label>
          End date
          <input
            type="date"
            value={filters.endDate}
            onChange={(e) => setFilters((prev) => ({ ...prev, endDate: e.target.value }))}
          />
        </label>
        <label>
          Artists
          <select
            multiple
            value={filters.artists}
            onChange={(e) => {
              const values = Array.from(e.target.selectedOptions).map((option) => option.value);
              setFilters((prev) => ({ ...prev, artists: values }));
            }}
          >
            {(options?.artists || []).map((artist) => (
              <option key={artist} value={artist}>
                {artist}
              </option>
            ))}
          </select>
        </label>
        <div className="content-box">
          Content types
          <div className="chips">
            {contentTypeOptions.map((name) => (
              <button
                key={name}
                type="button"
                className={filters.contentTypes.includes(name) ? "chip active" : "chip"}
                onClick={() => toggleContentType(name)}
              >
                {name}
              </button>
            ))}
          </div>
        </div>
      </div>

      <button className="apply-btn" onClick={applyFilters} disabled={applying}>
        {applying ? "Updating..." : "Apply Filters"}
      </button>
    </section>
  );
}
