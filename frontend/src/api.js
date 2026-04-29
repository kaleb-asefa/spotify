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

function toFilterParams(filters) {
  return {
    start_date: filters?.startDate,
    end_date: filters?.endDate,
    artists: filters?.artists?.join(","),
    content_types: filters?.contentTypes?.join(","),
  };
}

async function fetchJson(path, options) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    throw new Error("Request failed.");
  }
  return res.json();
}

export async function getOptions() {
  return fetchJson("/api/options");
}

export async function getDashboard(filters) {
  const query = toQuery(toFilterParams(filters));
  return fetchJson(`/api/dashboard?${query}`);
}

export async function getOverview(filters) {
  const query = toQuery(toFilterParams(filters));
  return fetchJson(`/api/overview?${query}`);
}

export async function getListeningTrends(filters) {
  const query = toQuery(toFilterParams(filters));
  return fetchJson(`/api/listening-trends?${query}`);
}

export async function getBehaviorAnalysis(filters) {
  const query = toQuery(toFilterParams(filters));
  return fetchJson(`/api/behavior-analysis?${query}`);
}

export async function getTimePatterns(filters) {
  const query = toQuery(toFilterParams(filters));
  return fetchJson(`/api/time-patterns?${query}`);
}

export async function getStatisticalInsights(filters, threshold = 2.5) {
  const query = toQuery({ ...toFilterParams(filters), threshold });
  return fetchJson(`/api/statistical-insights?${query}`);
}

export async function getArtistSongAnalytics(filters, topN = 10) {
  const query = toQuery({ ...toFilterParams(filters), top_n: topN });
  return fetchJson(`/api/artist-song-analytics?${query}`);
}

export async function trainSkipModel(filters) {
  const query = toQuery(toFilterParams(filters));
  return fetchJson(`/api/skip-model?${query}`, { method: "POST" });
}
