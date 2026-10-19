import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Download, Trash2 } from "lucide-react";
import { ApiError } from "../../api/client";
import { downloadSessionExport } from "../../api/export";
import { deleteSessionVideo } from "../../api/media";
import { getSession, type LectureSession } from "../../api/sessions";
import "../sessions/sessions.css";
import "./export.css";

export function ExportPage() {
  const { sessionId } = useParams();
  const id = Number(sessionId);

  const [session, setSession] = useState<LectureSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [showPurge, setShowPurge] = useState(false);
  const [ack, setAck] = useState(false);
  const [purging, setPurging] = useState(false);
  const cancelBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!Number.isFinite(id) || id <= 0) {
      setError("Invalid session id");
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const s = await getSession(id);
        if (!cancelled) setSession(s);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError ? err.message : "Could not load session",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    if (!showPurge) return;
    cancelBtnRef.current?.focus();
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setShowPurge(false);
        setAck(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [showPurge]);

  async function onDownload() {
    setDownloading(true);
    setError(null);
    setOk(null);
    try {
      await downloadSessionExport(id);
      setOk("CSV download started — windows, events, and topics only.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Export failed");
    } finally {
      setDownloading(false);
    }
  }

  async function onConfirmPurge() {
    if (!ack) return;
    setPurging(true);
    setError(null);
    setOk(null);
    try {
      const s = await deleteSessionVideo(id);
      setSession(s);
      setShowPurge(false);
      setAck(false);
      setOk("Video purged from disk. Aggregates and session metadata kept.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Purge failed");
    } finally {
      setPurging(false);
    }
  }

  if (loading) return <p>Loading export…</p>;

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
    <div className="export-page">
      <p style={{ margin: "0 0 0.5rem" }}>
        <Link to={`/sessions/${id}`}>← Session hub</Link>
      </p>
      <h1>Export & retention</h1>
      <p className="export-lead">
        Take class-level aggregates with you. Raw video stays temporary — purge
        removes the file while keeping TTOI windows and events.
      </p>

      {error ? <p className="sessions-error">{error}</p> : null}
      {ok ? <p className="export-ok">{ok}</p> : null}

      <section className="export-panel">
        <h2>Download CSV</h2>
        <p>Includes session metadata, topics, windows, and candidate decline events.</p>
        <ul>
          <li>Included: TTOI, coverage, modes, quality notes, decline depth</li>
          <li>Excluded: video file paths, face data, student identity</li>
        </ul>
        <button
          type="button"
          className="btn-primary"
          disabled={downloading}
          onClick={() => void onDownload()}
          style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}
        >
          <Download size={16} />
          {downloading ? "Preparing…" : "Download CSV"}
        </button>
      </section>

      <section className="export-panel">
        <h2>Purge raw video</h2>
        <p>
          Status:{" "}
          <span className={`status-pill ${session.status}`}>
            {session.status.replace("_", " ")}
          </span>
          {" · "}
          {session.has_video
            ? "Video file is on disk"
            : "No video file (already purged or live source only)"}
        </p>
        <button
          type="button"
          className="btn-secondary"
          disabled={!session.has_video}
          onClick={() => {
            setShowPurge(true);
            setAck(false);
          }}
          style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}
        >
          <Trash2 size={16} />
          Purge video
        </button>
      </section>

      <div className="privacy-strip">
        Analysis may auto-purge video when privacy defaults are on. Aggregates
        remain for reflection. See{" "}
        <Link to="/app/privacy">Privacy</Link>.
      </div>

      {showPurge ? (
        <div
          className="purge-modal-backdrop"
          role="dialog"
          aria-modal="true"
          aria-labelledby="purge-title"
        >
          <div className="purge-modal">
            <h2 id="purge-title">Purge video file?</h2>
            <p>
              This deletes the uploaded file from disk for “{session.title}”.
              Windows, events, topics, and summary stay. This cannot undo the
              file delete.
            </p>
            <label>
              <input
                type="checkbox"
                checked={ack}
                onChange={(e) => setAck(e.target.checked)}
              />
              <span>I understand the raw video will be removed permanently.</span>
            </label>
            <div className="purge-modal-actions">
              <button
                ref={cancelBtnRef}
                type="button"
                className="btn-secondary"
                onClick={() => {
                  setShowPurge(false);
                  setAck(false);
                }}
                disabled={purging}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                disabled={!ack || purging}
                onClick={() => void onConfirmPurge()}
              >
                {purging ? "Purging…" : "Purge video"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
