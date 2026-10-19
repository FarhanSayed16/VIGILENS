import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  Camera,
  ChevronDown,
  ChevronUp,
  FileDown,
  QrCode,
  Radio,
  Trash2,
} from "lucide-react";
import { ApiError } from "../../api/client";
import { LectureCockpit } from "../../components/domain/LectureCockpit";
import { AnalysisPanel } from "../../components/domain/AnalysisPanel";
import { useAnalysisSession } from "../../hooks/useAnalysisSession";
import { useLiveSession } from "../../hooks/useLiveSession";
import { setSecondarySource } from "../../api/live";
import { deleteSession, getSessionSummary, type SessionSummary } from "../../api/sessions";
import {
  formatElapsed,
  formatModeLabel,
  listModes,
  listTopics,
  type ModeChange,
  type Topic,
} from "../../api/topics";
import "../sessions/sessions.css";
import "../analysis/analysis.css";

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export function SessionHubPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const id = Number(sessionId);
  const live = useLiveSession(id);
  const batch = useAnalysisSession(id);

  const [topics, setTopics] = useState<Topic[]>([]);
  const [modes, setModes] = useState<ModeChange[]>([]);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [moreOpen, setMoreOpen] = useState(false);
  const [batchOpen, setBatchOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [secondaryDraft, setSecondaryDraft] = useState("");

  useEffect(() => {
    if (!Number.isFinite(id) || id <= 0) return;
    let cancelled = false;
    (async () => {
      try {
        const [t, m, sum] = await Promise.all([
          listTopics(id),
          listModes(id),
          getSessionSummary(id),
        ]);
        if (!cancelled) {
          setTopics(t.items);
          setModes(m.items);
          setSummary(sum);
        }
      } catch {
        /* non-blocking */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id, live.live?.status]);

  useEffect(() => {
    if (live.session?.secondary_source_url) {
      setSecondaryDraft(live.session.secondary_source_url);
    }
  }, [live.session?.secondary_source_url]);

  async function onDelete() {
    if (!live.session) return;
    if (
      !window.confirm(
        `Delete “${live.session.title}” and all derived rows? This cannot be undone.`,
      )
    ) {
      return;
    }
    setDeleting(true);
    try {
      await deleteSession(live.session.id);
      navigate("/sessions");
    } catch (err) {
      setLocalError(err instanceof ApiError ? err.message : "Delete failed");
      setDeleting(false);
    }
  }

  async function onSaveSecondary() {
    try {
      await setSecondarySource(id, secondaryDraft.trim() || null);
      await live.refresh();
    } catch (err) {
      setLocalError(
        err instanceof ApiError ? err.message : "Could not save secondary source",
      );
    }
  }

  if (live.loading) {
    return <p>Loading console…</p>;
  }

  if (live.error && !live.session) {
    return (
      <div>
        <p className="sessions-error">{live.error}</p>
        <Link to="/sessions">← Back to sessions</Link>
      </div>
    );
  }

  if (!live.session) {
    return null;
  }

  const session = live.session;

  return (
    <div className="console-page">
      <div className="hub-header">
        <p style={{ margin: "0 0 0.5rem" }}>
          <Link to="/sessions">← Sessions</Link>
        </p>
        <p className="page-kicker">{session.title}</p>
        <div className="hub-meta">
          <span className={`status-pill ${session.status}`}>
            {session.status.replace("_", " ")}
          </span>
          <span>{session.room_name ?? `Room #${session.room_config_id}`}</span>
          <span>Source: {session.source_type.replace("_", " ")}</span>
          <span>Mode: {formatModeLabel(session.current_mode)}</span>
          <span>Created {formatDate(session.created_at)}</span>
        </div>
      </div>

      {localError ? <p className="sessions-error">{localError}</p> : null}

      <div className="hub-chips">
        <div className="hub-chip">
          <span className="label">Faced the front</span>
          <span className="value">
            {summary?.mean_ttoi != null
              ? summary.mean_ttoi.toFixed(1)
              : live.live?.ttoi != null
                ? Math.round(live.live.ttoi)
                : "—"}
          </span>
        </div>
        <div className="hub-chip">
          <span className="label">Camera clear</span>
          <span className="value">
            {summary?.mean_coverage != null
              ? `${summary.mean_coverage.toFixed(0)}%`
              : live.live?.coverage_pct != null
                ? `${Math.round(live.live.coverage_pct)}%`
                : "—"}
          </span>
        </div>
        <div className="hub-chip">
          <span className="label">Longer drops</span>
          <span className="value">{summary?.event_count ?? 0}</span>
        </div>
        <div className="hub-chip">
          <span className="label">Topics</span>
          <span className="value">{topics.length}</span>
        </div>
      </div>

      {session.status === "error" ? (
        <p className="sessions-error" style={{ marginBottom: "0.75rem" }}>
          Last live run failed (often a worker crash). Click{" "}
          <strong>Start lecture</strong> again after the API reload — or check
          the backend terminal for the traceback.
        </p>
      ) : null}

      <section className="console-analysis analysis-panel">
        <h2>Live lecture</h2>
        <p className="analysis-lede">
          Preview is your webcam with seat boxes. Start begins detection; Stop
          opens Review. This shows who faces the teaching area — not attention.
        </p>
        <LectureCockpit
          session={session}
          live={live.live}
          starting={live.starting}
          stopping={live.stopping}
          error={live.error}
          onStart={() => void live.onStart()}
          onStop={() => void live.onStop()}
          secondaryLabel={session.secondary_source_url ?? null}
        />
      </section>

      <details className="dual-cam-details">
        <summary>Secondary camera (optional display)</summary>
        <p className="panel-hint">
          Situational awareness only — metrics always use the primary source /
          room geometry. Example: <code>webcam:1</code> or an RTSP URL.
        </p>
        <div className="dual-cam-row">
          <input
            type="text"
            value={secondaryDraft}
            onChange={(e) => setSecondaryDraft(e.target.value)}
            placeholder="webcam:1 or rtsp://…"
          />
          <button type="button" className="btn-secondary" onClick={() => void onSaveSecondary()}>
            Save secondary
          </button>
        </div>
      </details>

      <div className="hub-markers">
        <section className="hub-marker-panel">
          <h2>Topics</h2>
          {topics.length === 0 ? (
            <p className="hub-marker-empty">
              No topics yet.{" "}
              <Link to={`/sessions/${id}/live`}>Add on Topics</Link>
            </p>
          ) : (
            <ul>
              {topics.map((t) => (
                <li key={t.id}>
                  <span>
                    {formatElapsed(t.start_sec)}
                    {t.end_sec != null ? `–${formatElapsed(t.end_sec)}` : ""}
                  </span>
                  {t.label}
                </li>
              ))}
            </ul>
          )}
        </section>
        <section className="hub-marker-panel">
          <h2>Mode timeline</h2>
          {modes.length === 0 ? (
            <p className="hub-marker-empty">
              No mode changes yet.{" "}
              <Link to={`/sessions/${id}/live`}>Set on Topics</Link>
            </p>
          ) : (
            <ul>
              {modes.map((m) => (
                <li key={m.id}>
                  <span>{formatElapsed(m.start_sec)}</span>
                  {formatModeLabel(m.mode)}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <div className="privacy-strip">
        Anonymous seats and temporary groups only — no face memory, no student
        names. The main measure is how often the class faced the teaching area.
      </div>

      <button
        type="button"
        className="more-tools-toggle"
        onClick={() => setBatchOpen((o) => !o)}
      >
        {batchOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        Offline batch analysis
      </button>
      {batchOpen && batch.session ? (
        <section className="console-analysis analysis-panel">
          <AnalysisPanel
            session={batch.session}
            summary={batch.summary}
            job={batch.job}
            fakeWorker={batch.fakeWorker}
            starting={batch.starting}
            recovering={batch.recovering}
            stuckOrphan={batch.stuckOrphan}
            error={batch.error}
            onRun={(force) => void batch.onRun(force)}
            onRecover={() => void batch.onRecover()}
            compact
          />
        </section>
      ) : null}

      <button
        type="button"
        className="more-tools-toggle"
        onClick={() => setMoreOpen((o) => !o)}
      >
        {moreOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        More tools
      </button>

      {moreOpen ? (
        <div className="hub-actions">
          <Link className="hub-tile" to={`/sessions/${id}/setup`}>
            <Camera size={20} strokeWidth={1.75} />
            <strong>Setup source</strong>
            <span>Webcam / upload / phone</span>
          </Link>
          <Link className="hub-tile" to={`/sessions/${id}/live`}>
            <Radio size={20} strokeWidth={1.75} />
            <strong>Topics & modes</strong>
            <span>Mark lecture segments</span>
          </Link>
          <Link className="hub-tile" to={`/sessions/${id}/export`}>
            <FileDown size={20} strokeWidth={1.75} />
            <strong>Export</strong>
            <span>CSV + video purge</span>
          </Link>
          <Link className="hub-tile" to={`/sessions/${id}/pulse`}>
            <QrCode size={20} strokeWidth={1.75} />
            <strong>Pulse QR</strong>
            <span>Anonymous 1–5 feedback</span>
          </Link>
        </div>
      ) : null}

      <div className="hub-danger-zone">
        <button
          type="button"
          className="btn-danger"
          disabled={deleting}
          onClick={() => void onDelete()}
          style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}
        >
          <Trash2 size={16} />
          {deleting ? "Deleting…" : "Delete session"}
        </button>
      </div>
    </div>
  );
}
