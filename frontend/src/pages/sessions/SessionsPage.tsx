import { Link } from "react-router-dom";
import { Plus } from "lucide-react";

export function SessionsPage() {
  return (
    <div className="page-stub">
      <h1>Sessions</h1>
      <p>
        Past lectures and new session entry. Full list and wizard arrive in
        Phase 8.
      </p>
      <span className="stub-badge">
        <Plus size={14} /> Phase 8 — sessions API + UI
      </span>
      <p style={{ marginTop: "1.5rem" }}>
        <Link to="/sessions/demo">Open demo session hub →</Link>
      </p>
      <div className="privacy-strip">
        Class-level observable orientation only — not individual attention
        scores.
      </div>
    </div>
  );
}
