import { Link, useParams } from "react-router-dom";
import { AnalysisPanel } from "../../components/domain/AnalysisPanel";
import { useAnalysisSession } from "../../hooks/useAnalysisSession";
import "../sessions/sessions.css";
import "./analysis.css";

export function AnalysisRunnerPage() {
  const { sessionId } = useParams();
  const id = Number(sessionId);
  const a = useAnalysisSession(id);

  if (a.loading) return <p>Loading analysis…</p>;

  if (a.error && !a.session) {
    return (
      <div>
        <p className="sessions-error">{a.error}</p>
        <Link to="/sessions">← Back to sessions</Link>
      </div>
    );
  }

  if (!a.session) return null;

  return (
    <div className="analysis-page">
      <p style={{ margin: "0 0 0.5rem" }}>
        <Link to={`/sessions/${id}`}>← Console</Link>
      </p>

      <header className="analysis-header">
        <div>
          <p className="page-kicker">{a.session.title}</p>
          <p>
            Start or resume class-level orientation analysis for this lecture.
          </p>
        </div>
        <span className={`status-pill ${a.session.status}`}>
          {a.session.status.replace("_", " ")}
        </span>
      </header>

      <AnalysisPanel
        session={a.session}
        summary={a.summary}
        job={a.job}
        fakeWorker={a.fakeWorker}
        starting={a.starting}
        recovering={a.recovering}
        stuckOrphan={a.stuckOrphan}
        error={a.error}
        onRun={(force) => void a.onRun(force)}
        onRecover={() => void a.onRecover()}
      />
    </div>
  );
}
