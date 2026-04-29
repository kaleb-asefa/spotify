const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function toQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    query.set(key, value);
  });
  return query.toString();
}

export async function getOptions() {
  const res = await fetch(`${API_BASE}/api/options`);
  if (!res.ok) {
    throw new Error("Failed to fetch dashboard options.");
  }
  return res.json();
}

export async function getDashboard(filters) {
  const query = toQuery(filters);
  const res = await fetch(`${API_BASE}/api/dashboard?${query}`);
  if (!res.ok) {
    throw new Error("Failed to fetch dashboard data.");
  }
  return res.json();
}
