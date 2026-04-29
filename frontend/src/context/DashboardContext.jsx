import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { getOptions } from "../api";

const DashboardContext = createContext(null);

const DEFAULT_CONTENT_TYPES = ["Songs", "Podcasts", "Audiobooks"];

export function DashboardProvider({ children }) {
  const [options, setOptions] = useState(null);
  const [filters, setFilters] = useState({
    startDate: "",
    endDate: "",
    artists: [],
    contentTypes: DEFAULT_CONTENT_TYPES,
  });
  const [appliedFilters, setAppliedFilters] = useState(null);
  const [initializing, setInitializing] = useState(true);
  const [optionsError, setOptionsError] = useState("");
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      try {
        setInitializing(true);
        const optionPayload = await getOptions();
        if (!active) {
          return;
        }

        const contentTypes = optionPayload?.contentTypes || DEFAULT_CONTENT_TYPES;
        const dateRange = optionPayload?.dateRange || {};
        const nextFilters = {
          startDate: dateRange.min || "",
          endDate: dateRange.max || "",
          artists: [],
          contentTypes,
        };

        setOptions(optionPayload);
        setFilters(nextFilters);
        setAppliedFilters(nextFilters);
        setOptionsError("");
      } catch (err) {
        if (!active) {
          return;
        }
        setOptionsError(err.message || "Unable to load dashboard options.");
      } finally {
        if (active) {
          setInitializing(false);
        }
      }
    }

    bootstrap();

    return () => {
      active = false;
    };
  }, []);

  function applyFilters() {
    setApplying(true);
    setAppliedFilters({ ...filters });
  }

  const value = useMemo(
    () => ({
      options,
      filters,
      setFilters,
      appliedFilters,
      applyFilters,
      initializing,
      optionsError,
      applying,
      setApplying,
    }),
    [
      options,
      filters,
      appliedFilters,
      initializing,
      optionsError,
      applying,
    ]
  );

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>;
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboard must be used within DashboardProvider");
  }
  return context;
}
