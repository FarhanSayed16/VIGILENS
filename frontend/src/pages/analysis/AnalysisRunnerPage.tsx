import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PlayCircle, RotateCcw } from "lucide-react";
import { ApiError } from "../../api/client";
import {
  JOB_STAGES,
  getJob,
  stageIndex,
  startAnalysis,
  type AnalysisJob,
} from "../../api/jobs";
import { getSession, getSessionSummary, type LectureSession, type SessionSummary } from "../../api/sessions";
import "../sessions/sessions.css";
import "./analysis.css";

function sourceReady(s: LectureSession): boolean {
  if (s.source_type === "upload") return s.has_video;
  return Boolean(s.source_url);
}

export function AnalysisRunnerPage() {
  const { sessionId } = useParams();
  const id = Number(sessionId);

  const [session, setSession] = useState<LectureSession | null>(null);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const pollRef = useRef<number | null>(null);

  function stopPoll() {
    if (pollRef.current != null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  async function refreshSession() {
    const [s, sum] = await Promise.all([getSession(id), getSessionSummary(id)]);
    setSession(s);
    setSummary(sum);
    return s;
  }

  useEffect(() => {
    if (!Number.isFinite(id) || id <= 0) {
      setError("Invalid session id");
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        await refreshSession();
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError ? err.message : "Could not load analysis page",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
      stopPoll();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  function beginPoll(jobId: number) {
    stopPoll();
    const tick = async () => {
      try {
        const j = await getJob(jobId);
        setJob(j);
        if (j.status === "done" || j.status === "error" || j.status === "cancelled") {
          stopPoll();
          await refreshSession();
        }
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Job poll failed");
        stopPoll();
      }
    };
    void tick();
    pollRef.current = window.setInterval(() => void tick(), 1000);
  }

  async function onRun(force = false) {
    if (!session || starting) return;
    if (
      force ||
      (job && (job.status === "queued" || job.status === "running"))
    ) {
      if (
        !window.confirm(
          "Start a new analysis? Any unfinished job for this session will be superseded.",
        )
      ) {
        return;
      }
    }
    setStarting(true);
    setError(null);
    try {
      const j = await startAnalysis(id);
      setJob(j);
      await refreshSession();
      beginPoll(j.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start analysis");
    } finally {
      setStarting(false);
    }
  }

  const checks = useMemo(() => {
    if (!session) return [];
    return [
      {
        ok: Boolean(session.room_config_id),
        label: "Room configured",
        detail: session.room_name ?? `Room #${session.room_config_id}`,
      },
      {
        ok: sourceReady(session),
        label: "Source ready",
        detail: sourceReady(session)
          ? session.has_video
            ? `Upload · ${session.video_path ?? "file"}`
            : session.source_url ?? session.source_type
          : "Upload a video or set webcam/phone on Setup",
      },
      {
        ok: session.status !== "analyzing" || Boolean(job),
        label: "Job slot",
        detail:
          session.status === "analyzing"
            ? "Analysis in progress on this session"
            : "Ready to start (one heavy job at a time on this machine)",
      },
    ];
  }, [session, job]);

  const running =
    job?.status === "queued" || job?.status === "running";
  const done = job?.status === "done" || session?.status === "complete";
  const activeStage = stageIndex(job?.stage);

  if (loading) return <p>Loading analysis…</p>;

  if (error && !session) {
    return (
      <div>
        <p className="sessions-error">{error}</p>
        <Link to="/sessions">← Back to sessions</Link>
      </div>
    );
  }

  if (!session) return null;

  return (
    <div className="analysis-page">
      <p style={{ margin: "0 0 0.5rem" }}>
        <Link to={`/sessions/${id}`}>← Session hub</Link>
      </p>

      <header className="analysis-header">
        <div>
          <h1>Run analysis</h1>
          <p>
            Class-level TTOI from the attached source for “{session.title}”.
            Runs the vision worker (YOLO + MediaPipe when enabled) behind the same
            job contract as synthetic CI runs.
          </p>
        </div>
        <span className={`status-pill ${session.status}`}>
          {session.status.replace("_", " ")}
        </span>
      </header>

      {error ? <p className="sessions-error">{error}</p> : null}

      <section className="analysis-panel">
        <h2>Preconditions</h2>
        <ul className="check-list">
          {checks.map((c) => (
            <li key={c.label} className={c.ok ? "ok" : "bad"}>
              <span className="mark">{c.ok ? "✓" : "!"}</span>
              <div>
                <strong>{c.label}</strong>
                <span>{c.detail}</span>
              </div>
            </li>
          ))}
        </ul>
        <div className="analysis-actions">
          <button
            type="button"
            className="btn-primary"
            disabled={starting || running || !sourceReady(session)}
            onClick={() => void onRun(false)}
          >
            <PlayCircle size={18} />
            {starting ? "Starting…" : running ? "Running…" : "Run analysis"}
          </button>
          {(done || job?.status === "error") && (
            <button
              type="button"
              className="btn-secondary"
              disabled={starting || running}
              onClick={() => void onRun(true)}
            >
              <RotateCcw size={16} />
              Re-run
            </button>
          )}
          {!sourceReady(session) ? (
            <Link className="btn-secondary" to={`/sessions/${id}/setup`}>
              Open Setup
            </Link>
          ) : null}
        </div>
      </section>

      <section className="analysis-panel">
        <h2>Progress</h2>
        {!job ? (
          <p className="analysis-muted">No job yet — run analysis when ready.</p>
        ) : (
          <>
            <div className="job-meta">
              <span>Job #{job.id}</span>
              <span className={`status-pill ${job.status}`}>{job.status}</span>
              <span>{Math.round(job.progress_pct)}%</span>
            </div>
            <div
              className="progress-track"
              role="progressbar"
              aria-valuenow={Math.round(job.progress_pct)}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className={`progress-fill${running ? " pulse" : ""}`}
                style={{ width: `${Math.min(100, job.progress_pct)}%` }}
              />
            </div>
            <ol className="stage-list">
              {JOB_STAGES.map((s, i) => {
                const active = activeStage === i;
                const complete =
                  job.status === "done" ||
                  (activeStage >= 0 && i < activeStage) ||
                  (job.progress_pct >= 100 && s.id === "done");
                return (
                  <li
                    key={s.id}
                    className={
                      complete ? "complete" : active ? "active" : undefined
                    }
                  >
                    {s.label}
                  </li>
                );
              })}
            </ol>
            {job.error_message ? (
              <p className="sessions-error">{job.error_message}</p>
            ) : null}
          </>
        )}
      </section>

      {done && summary && (summary.window_count > 0 || session.status === "complete") ? (
        <section className="analysis-panel done-panel">
          <h2>Analysis complete</h2>
          <div className="done-chips">
            <div>
              <span className="label">Mean TTOI</span>
              <strong>
                {summary.mean_ttoi != null ? summary.mean_ttoi.toFixed(1) : "—"}
              </strong>
            </div>
            <div>
              <span className="label">Coverage</span>
              <strong>
                {summary.mean_coverage != null
                  ? `${summary.mean_coverage.toFixed(0)}%`
                  : "—"}
              </strong>
            </div>
            <div>
              <span className="label">Windows</span>
              <strong>{summary.window_count}</strong>
            </div>
            <div>
              <span className="label">Declines</span>
              <strong>{summary.event_count}</strong>
            </div>
          </div>
          <p className="analysis-muted">
            Class-level aggregates are ready. Open Results for the TTOI timeline.
          </p>
          <div className="analysis-actions">
            <Link className="btn-primary" to={`/sessions/${id}/results`}>
              Open Results
            </Link>
            <Link className="btn-secondary" to={`/sessions/${id}`}>
              Session hub
            </Link>
          </div>
        </section>
      ) : null}
    </div>
  );
}
