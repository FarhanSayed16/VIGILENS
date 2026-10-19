import { useState } from "react";
import { NavLink, useParams } from "react-router-dom";
import "./session-subnav.css";

const PRIMARY = [
  { suffix: "", label: "Console", end: true },
  { suffix: "/results", label: "Review", end: false },
  { suffix: "/export", label: "Export", end: false },
  { suffix: "/pulse", label: "Pulse", end: false },
] as const;

const MORE = [
  { suffix: "/setup", label: "Setup" },
  { suffix: "/live", label: "Topics" },
] as const;

type Props = {
  sessionId?: number;
};

export function SessionSubnav({ sessionId }: Props) {
  const params = useParams();
  const id = sessionId ?? Number(params.sessionId);
  const [moreOpen, setMoreOpen] = useState(false);
  if (!Number.isFinite(id) || id <= 0) return null;

  const base = `/sessions/${id}`;

  return (
    <nav className="session-subnav" aria-label="Session sections">
      {PRIMARY.map((link) => {
        const to = `${base}${link.suffix}`;
        return (
          <NavLink
            key={link.label}
            to={to}
            end={link.end}
            className={({ isActive }) =>
              `session-subnav-link${isActive ? " active" : ""}`
            }
          >
            {link.label}
          </NavLink>
        );
      })}
      <div className="session-subnav-more">
        <button
          type="button"
          className={`session-subnav-link more-btn${moreOpen ? " open" : ""}`}
          aria-expanded={moreOpen}
          onClick={() => setMoreOpen((o) => !o)}
        >
          More
        </button>
        {moreOpen ? (
          <div className="session-subnav-more-menu" role="menu">
            {MORE.map((link) => (
              <NavLink
                key={link.label}
                to={`${base}${link.suffix}`}
                role="menuitem"
                className={({ isActive }) =>
                  `session-subnav-link${isActive ? " active" : ""}`
                }
                onClick={() => setMoreOpen(false)}
              >
                {link.label}
              </NavLink>
            ))}
          </div>
        ) : null}
      </div>
    </nav>
  );
}
