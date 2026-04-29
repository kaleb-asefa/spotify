import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import DashboardLayout from "./components/DashboardLayout";
import { DashboardProvider } from "./context/DashboardContext";
import ArtistSongAnalyticsPage from "./pages/ArtistSongAnalyticsPage";
import BehaviorAnalysisPage from "./pages/BehaviorAnalysisPage";
import ListeningTrendsPage from "./pages/ListeningTrendsPage";
import MachineLearningPage from "./pages/MachineLearningPage";
import OverviewPage from "./pages/OverviewPage";
import StatisticalInsightsPage from "./pages/StatisticalInsightsPage";
import TimePatternIntelligencePage from "./pages/TimePatternIntelligencePage";

export default function App() {
  return (
    <BrowserRouter>
      <DashboardProvider>
        <Routes>
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<OverviewPage />} />
            <Route path="listening-trends" element={<ListeningTrendsPage />} />
            <Route path="artist-song-analytics" element={<ArtistSongAnalyticsPage />} />
            <Route path="behavior-analysis" element={<BehaviorAnalysisPage />} />
            <Route path="time-pattern-intelligence" element={<TimePatternIntelligencePage />} />
            <Route path="statistical-insights" element={<StatisticalInsightsPage />} />
            <Route path="machine-learning" element={<MachineLearningPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </DashboardProvider>
    </BrowserRouter>
  );
}
