import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
} from "react-router-dom";
// Analysis route kept as thin alias → Console (hub)
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
import { ResultsPage } from "../pages/results/ResultsPage";
import { ExportPage } from "../pages/export/ExportPage";
import { PulseSetupPage } from "../pages/pulse-setup/PulseSetupPage";
import { NotFoundPage } from "../pages/not-found/NotFoundPage";
import { PulsePublicPage } from "../pages/pulse-public/PulsePublicPage";

const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/pulse/:sessionId", element: <PulsePublicPage /> },
  { path: "/privacy", element: <PrivacyPage publicLayout /> },
  {
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [
      { path: "/", element: <Navigate to="/sessions" replace /> },
      { path: "/sessions", element: <SessionsPage /> },
      { path: "/sessions/new", element: <NewSessionPage /> },
      { path: "/sessions/:sessionId", element: <SessionHubPage /> },
      { path: "/sessions/:sessionId/setup", element: <SetupPage /> },
      { path: "/sessions/:sessionId/live", element: <LiveControlsPage /> },
      {
        path: "/sessions/:sessionId/analysis",
        element: <Navigate to=".." relative="path" replace />,
      },
      { path: "/sessions/:sessionId/results", element: <ResultsPage /> },
      { path: "/sessions/:sessionId/export", element: <ExportPage /> },
      { path: "/sessions/:sessionId/pulse", element: <PulseSetupPage /> },
      { path: "/rooms", element: <RoomsPage /> },
      { path: "/rooms/new", element: <RoomEditorPage /> },
      { path: "/rooms/:roomId/edit", element: <RoomEditorPage /> },
      { path: "/settings", element: <SettingsPage /> },
      { path: "/app/privacy", element: <PrivacyPage /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
