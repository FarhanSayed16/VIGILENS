import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./AppShell";
import { RequireAuth } from "./RequireAuth";
import { LoginPage } from "../pages/login/LoginPage";
import { SessionsPage } from "../pages/sessions/SessionsPage";
import { RoomsPage } from "../pages/rooms/RoomsPage";
import { RoomEditorPage } from "../pages/rooms/RoomEditorPage";
import { PrivacyPage } from "../pages/privacy/PrivacyPage";
import { SettingsPage } from "../pages/settings/SettingsPage";
import { SessionHubPage } from "../pages/session-hub/SessionHubPage";
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
        <Route path="/sessions/:sessionId" element={<SessionHubPage />} />
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
