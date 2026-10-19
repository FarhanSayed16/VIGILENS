import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PlayCircle, RotateCcw, Wrench } from "lucide-react";
import {
  JOB_STAGES,
  isJobActive,
  stageIndex,
  type AnalysisJob,
} from "../../api/jobs";
import type { LectureSession, SessionSummary } from "../../api/sessions";
import { formatElapsed } from "../../api/topics";
import "../../pages/analysis/analysis.css";

function sourceReady(s: LectureSession): boolean {
  if (s.source_type === "upload") return s.has_video;
  return Boolean(s.source_url);
}

function elapsedSince(iso: string | null | undefined): number {
  if (!iso) return 0;
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return 0;
  return Math.max(0, (Date.now() - t) / 1000);
}

/** Rough remaining time from progress rate; null if not estimable. */
function estimateRemainingSec(
  createdAt: string,
  progressPct: number,
): number | null {
  if (progressPct < 3) return null;
  const elapsed = elapsedSince(createdAt);
  if (elapsed < 2) return null;
  const rate = progressPct / elapsed;
  if (rate <= 0) return null;
  return Math.max(0, (100 - progressPct) / rate);
}

type Props = {
  session: LectureSession;
  summary: SessionSummary | null;
  job: AnalysisJob | null;
  fakeWorker: boolean | null;
  starting: boolean;
  recovering: boolean;
  stuckOrphan: boolean;
  error: string | null;
  onRun: (force: boolean) => void;
  onRecover: () => void;
  /** Compact layout for Console embed */
  compact?: boolean;
};

export function AnalysisPanel({
  session,
  summary,
  job,
  fakeWorker,
  starting,
  recovering,
  stuckOrphan,
  error,
  onRun,
  onRecover,
  compact = false,
}: Props) {
  const running = isJobActive(job);
  const done = job?.status === "done" || session.status === "complete";
  const activeStage = stageIndex(job?.stage);
  const id = session.id;
  const [, setTick] = useState(0);

  useEffect(() => {
    if (!running || !job) return;
    const timer = window.setInterval(() => setTick((n) => n + 1), 1000);
    return () => window.clearInterval(timer);
  }, [running, job?.id]);

  const checks = [
    {
      ok: Boolean(session.room_config_id),
      label: "Room",
      detail: session.room_name ?? `Room #${session.room_config_id}`,
    },
    {
      ok: sourceReady(session),
      label: "Source",
      detail: sourceReady(session)
        ? session.has_video
          ? `Upload · ${session.video_path ?? "file"}`
          : session.source_url ?? session.source_type
        : "Set webcam / upload on Setup",
    },
    {
      ok: !stuckOrphan,
      label: "Job",
      detail: running
        ? `Running job #${job?.id}`
        : stuckOrphan
          ? "Stuck analyzing — recover to continue"
          : job?.status === "error"
            ? `Last job errored (#${job.id})`
            : "Ready",
    },
  ];

  const elapsedSec = job && running ? elapsedSince(job.created_at) : 0;
  const remainingSec =
    job && running
      ? estimateRemainingSec(job.created_at, job.progress_pct)
      : null;
  const stageLabel =
    JOB_STAGES.find((s) => s.id === job?.stage)?.label ??
    (job?.stage === "queued" ? "Queued" : job?.stage ?? "…");

  return (
    <div className={`analysis-embed${compact ? " compact" : ""}`}>
      {!compact ? (
        <p className="analysis-lede">
          Class-level “faced the front” — not mood or individual grades.{" "}
          {fakeWorker === true
            ? "Synthetic worker (USE_FAKE_WORKER=true)."
            : fakeWorker === false
              ? "Real vision (YOLO + MediaPipe)."
              : null}
        </p>
      ) : (
        <p className="analysis-lede">
          Facing the teaching area — not emotion or attention scores.
          {fakeWorker === true
            ? " · Synthetic worker"
            : fakeWorker === false
              ? " · Real vision"
              : ""}
        </p>
      )}

      {error ? <p className="sessions-error">{error}</p> : null}

      <ul className="check-list status-strip">
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

      {running && job ? (
        <div className="live-strip" aria-live="polite">
          <div className="live-strip-main">
            <span className="live-dot" aria-hidden />
            <div>
              <strong>Analysis running</strong>
              <span className="live-strip-meta">
                Job #{job.id} · {stageLabel} · {Math.round(job.progress_pct)}%
              </span>
            </div>
          </div>
          <div className="live-strip-timers">
            <div>
              <span className="label">Elapsed</span>
              <span className="value">{formatElapsed(elapsedSec)}</span>
            </div>
            <div>
              <span className="label">Est. left</span>
              <span className="value">
                {remainingSec != null ? formatElapsed(remainingSec) : "—"}
              </span>
            </div>
          </div>
          <p className="live-strip-privacy">
            Live progress only — windows commit when the job finishes. No face
            crops or evidence frames are stored.
          </p>
        </div>
      ) : null}

      <div className="analysis-actions">
        {stuckOrphan ? (
          <button
            type="button"
            className="btn-primary"
            disabled={recovering}
            onClick={() => onRecover()}
          >
            <Wrench size={18} />
            {recovering ? "Recovering…" : "Recover stuck job"}
          </button>
        ) : (
          <button
            type="button"
            className="btn-primary"
            disabled={
              starting || running || !sourceReady(session) || stuckOrphan
            }
            onClick={() => onRun(false)}
          >
            <PlayCircle size={18} />
            {starting
              ? "Starting…"
              : running
                ? "Running…"
                : "Start analysis"}
          </button>
        )}
        {(done || job?.status === "error" || stuckOrphan) && !running ? (
          <button
            type="button"
            className="btn-secondary"
            disabled={starting || recovering || !sourceReady(session)}
            onClick={() => onRun(true)}
          >
            <RotateCcw size={16} />
            Re-run
          </button>
        ) : null}
        {!sourceReady(session) ? (
          <Link className="btn-secondary" to={`/sessions/${id}/setup`}>
            Open Setup
          </Link>
        ) : null}
        {done ? (
          <Link className="btn-secondary" to={`/sessions/${id}/results`}>
            View review
          </Link>
        ) : null}
      </div>

      <div className="analysis-panel progress-block">
        <h2>Progress</h2>
        {!job ? (
          <p className="analysis-muted">No job yet — start analysis when ready.</p>
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
      </div>

      {done && summary && (summary.window_count > 0 || session.status === "complete") ? (
        <div className="done-chips" style={{ marginTop: "1rem" }}>
          <div>
            <span className="label">Faced the front</span>
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
            <span className="label">Declines</span>
            <strong>{summary.event_count}</strong>
          </div>
        </div>
      ) : null}
    </div>
  );
}
