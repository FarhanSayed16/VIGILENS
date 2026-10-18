import {
  BookOpen,
  DoorOpen,
  LayoutList,
  LogOut,
  Shield,
} from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { BrandMark } from "../components/domain/BrandMark";
import { PageTransition } from "../components/ui/PageTransition";
import { clearSession, getUsername } from "../stores/auth";
import "../styles/shell.css";

const titles: Record<string, string> = {
  "/": "Sessions",
  "/sessions": "Sessions",
  "/sessions/new": "New session",
  "/rooms": "Rooms",
  "/rooms/new": "Create room",
  "/app/privacy": "Privacy",
  "/settings": "Settings",
};

function titleFor(pathname: string): string {
  if (pathname === "/sessions/new") {
    return "New session";
  }
  if (pathname.startsWith("/sessions/") && pathname !== "/sessions") {
    return "Session hub";
  }
  if (/^\/rooms\/\d+\/edit$/.test(pathname)) {
    return "Edit room";
  }
  return titles[pathname] ?? "VIGILENS";
}

export function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();

  function logout() {
    clearSession();
    navigate("/login");
  }

  const username = getUsername() ?? "lecturer";

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
          <PageTransition key={location.pathname}>
            <Outlet />
          </PageTransition>
        </main>
      </div>
    </div>
  );
}
