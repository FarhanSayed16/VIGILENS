import { Link, useParams } from "react-router-dom";

export function SessionHubPage() {
  const { sessionId } = useParams();

  return (
    <div className="page-stub">
      <h1>Session hub</h1>
      <p>
        Mission control for lecture <strong>{sessionId}</strong>. Setup,
        analysis, results, and export routes expand in Phases 8–14.
      </p>
      <span className="stub-badge">Placeholder · Phase 8+</span>
      <p style={{ marginTop: "1.5rem" }}>
        <Link to="/sessions">← Back to sessions</Link>
      </p>
      <div className="privacy-strip">
        Observable class-level orientation trends — not a measure of learning,
        interest, or individual performance.
      </div>
    </div>
  );
}
