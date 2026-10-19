import {
  BookOpen,
  DoorOpen,
  LayoutList,
  LogOut,
  Shield,
} from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { BrandMark } from "../components/domain/BrandMark";
import { SessionSubnav } from "../components/domain/SessionSubnav";
import { PageTransition } from "../components/ui/PageTransition";
import { clearSession, getUsername } from "../stores/auth";
import "../styles/shell.css";

function titleFor(pathname: string): string {
  if (pathname === "/sessions/new") return "New session";
  if (pathname === "/rooms/new") return "Create room";
  if (/^\/rooms\/\d+\/edit$/.test(pathname)) return "Edit room";
  if (pathname === "/rooms") return "Rooms";
  if (pathname === "/app/privacy") return "Privacy";
  if (pathname === "/settings") return "Settings";
  if (pathname === "/sessions" || pathname === "/") return "Sessions";

  const m = pathname.match(/^\/sessions\/(\d+)(\/.*)?$/);
  if (m) {
    const rest = m[2] || "";
    const map: Record<string, string> = {
      "": "Live lecture",
      "/setup": "Setup",
      "/live": "Topics & modes",
      "/analysis": "Live lecture",
      "/results": "Review",
      "/export": "Export",
      "/pulse": "Pulse QR",
    };
    return map[rest] ?? "Session";
  }
  return "VIGILENS";
}

function sessionIdFromPath(pathname: string): number | null {
  const m = pathname.match(/^\/sessions\/(\d+)/);
  if (!m) return null;
  const id = Number(m[1]);
  return Number.isFinite(id) ? id : null;
}

export function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const username = getUsername() ?? "lecturer";
  const sessionId = sessionIdFromPath(location.pathname);
  const showSessionNav =
    sessionId != null && !location.pathname.endsWith("/new");

  function logout() {
    clearSession();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <BrandMark to="/" />
        <nav className="nav" aria-label="Main">
          <NavLink
            to="/sessions"
            className={({ isActive }) =>
              `nav-link${isActive || location.pathname === "/" ? " active" : ""}`
            }
          >
            <LayoutList size={18} strokeWidth={1.75} />
            Sessions
          </NavLink>
          <NavLink
            to="/rooms"
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <DoorOpen size={18} strokeWidth={1.75} />
            Rooms
          </NavLink>
          <NavLink
            to="/app/privacy"
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <Shield size={18} strokeWidth={1.75} />
            Privacy
          </NavLink>
        </nav>
        <div className="sidebar-foot">
          <NavLink
            to="/settings"
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <BookOpen size={18} strokeWidth={1.75} />
            Settings
          </NavLink>
          <button type="button" className="ghost-btn" onClick={logout}>
            <LogOut size={16} strokeWidth={1.75} />
            Logout
          </button>
        </div>
      </aside>

      <div className="shell-main">
        <header className="context-bar">
          <div className="context-title">{titleFor(location.pathname)}</div>
          <div className="context-meta">{username} · lecturer workspace</div>
        </header>
        <main className="stage">
          {showSessionNav ? <SessionSubnav sessionId={sessionId} /> : null}
          <PageTransition key={location.pathname}>
            <Outlet />
          </PageTransition>
        </main>
      </div>
    </div>
  );
}
