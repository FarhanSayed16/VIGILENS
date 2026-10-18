import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./AppShell";
import { RequireAuth } from "./RequireAuth";
import { LoginPage } from "../pages/login/LoginPage";
import { SessionsPage } from "../pages/sessions/SessionsPage";
import { NewSessionPage } from "../pages/sessions/NewSessionPage";
import { RoomsPage } from "../pages/rooms/RoomsPage";
import { RoomEditorPage } from "../pages/rooms/RoomEditorPage";
import { PrivacyPage } from "../pages/privacy/PrivacyPage";
import { SettingsPage } from "../pages/settings/SettingsPage";
import { SessionHubPage } from "../pages/session-hub/SessionHubPage";
import { LiveControlsPage } from "../pages/live/LiveControlsPage";
import { SetupPage } from "../pages/setup/SetupPage";
import { AnalysisRunnerPage } from "../pages/analysis/AnalysisRunnerPage";
import { ResultsPage } from "../pages/results/ResultsPage";
import { ExportPage } from "../pages/export/ExportPage";
import { PulseSetupPage } from "../pages/pulse-setup/PulseSetupPage";
import { NotFoundPage } from "../pages/not-found/NotFoundPage";
import { PulsePublicPage } from "../pages/pulse-public/PulsePublicPage";

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/pulse/:sessionId" element={<PulsePublicPage />} />
      <Route path="/privacy" element={<PrivacyPage publicLayout />} />

      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Navigate to="/sessions" replace />} />
        <Route path="/sessions" element={<SessionsPage />} />
        <Route path="/sessions/new" element={<NewSessionPage />} />
        <Route path="/sessions/:sessionId" element={<SessionHubPage />} />
        <Route path="/sessions/:sessionId/setup" element={<SetupPage />} />
        <Route path="/sessions/:sessionId/live" element={<LiveControlsPage />} />
        <Route
          path="/sessions/:sessionId/analysis"
          element={<AnalysisRunnerPage />}
        />
        <Route
          path="/sessions/:sessionId/results"
          element={<ResultsPage />}
        />
        <Route path="/sessions/:sessionId/export" element={<ExportPage />} />
        <Route path="/sessions/:sessionId/pulse" element={<PulseSetupPage />} />
        <Route path="/rooms" element={<RoomsPage />} />
        <Route path="/rooms/new" element={<RoomEditorPage />} />
        <Route path="/rooms/:roomId/edit" element={<RoomEditorPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/app/privacy" element={<PrivacyPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
