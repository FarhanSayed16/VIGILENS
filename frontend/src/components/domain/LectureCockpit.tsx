import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Play, Square } from "lucide-react";
import type { LectureSession } from "../../api/sessions";
import { fetchLivePreviewBlob, type LiveState } from "../../api/live";
import { getRoom, type BoxRegion } from "../../api/rooms";
import { formatElapsed } from "../../api/topics";
import "./lecture-cockpit.css";

type SeatBand = "oriented" | "mixed" | "decline" | "unobservable";

function bandForSeat(o: number | null | undefined, usable: boolean): SeatBand {
  if (!usable || o == null) return "unobservable";
  if (o >= 70) return "oriented";
  if (o >= 45) return "mixed";
  return "decline";
}

function seatDisplayId(id: string): string {
  if (/^v\d+$/i.test(id)) return `Extra ${id.slice(1)}`;
  return id;
}

type Props = {
  session: LectureSession;
  live: LiveState | null;
  starting: boolean;
  stopping: boolean;
  error: string | null;
  onStart: () => void;
  onStop: () => void;
  secondaryLabel?: string | null;
};

export function LectureCockpit({
  session,
  live,
  starting,
  stopping,
  error,
  onStart,
  onStop,
  secondaryLabel,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [workerPreviewUrl, setWorkerPreviewUrl] = useState<string | null>(null);
  const [seatBoxes, setSeatBoxes] = useState<BoxRegion[]>([]);
  const [, setTick] = useState(0);
  const isLive = live?.running === true || session.status === "live";
  // Release cam as soon as Start is clicked (before API returns) so the worker can open it.
  const workerOwnsCamera =
    session.source_type === "webcam" && (isLive || starting);

  useEffect(() => {
    if (!isLive) return;
    const t = window.setInterval(() => setTick((n) => n + 1), 250);
    return () => window.clearInterval(t);
  }, [isLive]);

  // Poll latest worker JPEG; never pile up fetches (avoids laggy backlog)
  useEffect(() => {
    if (!isLive) {
      setWorkerPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      return;
    }
    let cancelled = false;
    let currentUrl: string | null = null;
    let busy = false;
    const tick = async () => {
      if (cancelled || busy) return;
      busy = true;
      try {
        const blob = await fetchLivePreviewBlob(session.id);
        if (cancelled || !blob || blob.size < 32) return;
        const next = URL.createObjectURL(blob);
        if (currentUrl) URL.revokeObjectURL(currentUrl);
        currentUrl = next;
        setWorkerPreviewUrl(next);
      } catch {
        /* keep last frame */
      } finally {
        busy = false;
      }
    };
    void tick();
    const id = window.setInterval(() => void tick(), 90);
    return () => {
      cancelled = true;
      window.clearInterval(id);
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [isLive, session.id]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const room = await getRoom(session.room_config_id);
        if (!cancelled) {
          setSeatBoxes(
            (room.seat_regions || []).filter(
              (r): r is BoxRegion => r.type === "box",
            ),
          );
        }
      } catch {
        /* optional overlay */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [session.room_config_id]);

  // Preview BEFORE live only. On Windows the browser exclusive-locks the cam;
  // OpenCV (worker) then often gets black frames → "0 detected". Release on Start.
  useEffect(() => {
    const v = videoRef.current;
    if (session.source_type !== "webcam" || workerOwnsCamera) {
      if (v?.srcObject) {
        (v.srcObject as MediaStream).getTracks().forEach((tr) => tr.stop());
        v.srcObject = null;
      }
      return;
    }
    let stream: MediaStream | null = null;
    let cancelled = false;
    (async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user" },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((tr) => tr.stop());
          return;
        }
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play().catch(() => undefined);
        }
        setPreviewError(null);
      } catch {
        setPreviewError("Could not open browser camera preview.");
      }
    })();
    return () => {
      cancelled = true;
      stream?.getTracks().forEach((tr) => tr.stop());
    };
  }, [session.source_type, session.id, workerOwnsCamera]);

  // Draw seat ROI boxes on preview (geometry guide — not YOLO face boxes)
  useEffect(() => {
    const video = videoRef.current;
    const canvas = overlayRef.current;
    if (!video || !canvas || session.source_type !== "webcam") return;

    let raf = 0;
    const draw = () => {
      const w = video.clientWidth;
      const h = video.clientHeight;
      if (w > 0 && h > 0) {
        if (canvas.width !== w || canvas.height !== h) {
          canvas.width = w;
          canvas.height = h;
        }
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.clearRect(0, 0, w, h);
          // object-fit: cover style mapping approx — use contain math
          const vw = video.videoWidth || w;
          const vh = video.videoHeight || h;
          const scale = Math.min(w / vw, h / vh);
          const dw = vw * scale;
          const dh = vh * scale;
          const ox = (w - dw) / 2;
          const oy = (h - dh) / 2;
          for (const box of seatBoxes) {
            const seatLive = live?.per_seat?.find((s) => s.seat_id === box.id);
            const band = seatLive
              ? bandForSeat(seatLive.orientation_pct, seatLive.usable)
              : "unobservable";
            const color =
              band === "oriented"
                ? "rgba(15,118,110,0.9)"
                : band === "mixed"
                  ? "rgba(194,120,3,0.9)"
                  : band === "decline"
                    ? "rgba(185,28,28,0.9)"
                    : "rgba(148,163,184,0.85)";
            ctx.strokeStyle = color;
            ctx.lineWidth = 2.5;
            ctx.strokeRect(ox + box.x * dw, oy + box.y * dh, box.w * dw, box.h * dh);
            ctx.fillStyle = color;
            ctx.font = "600 12px system-ui,sans-serif";
            ctx.fillText(box.id, ox + box.x * dw + 4, oy + box.y * dh + 14);
          }
          // Detection badge
          const n = live?.persons_detected;
          if (n != null) {
            ctx.fillStyle = n > 0 ? "rgba(15,118,110,0.92)" : "rgba(185,28,28,0.9)";
            const label = n > 0 ? `${n} detected` : "0 detected";
            ctx.fillRect(8, 8, ctx.measureText(label).width + 16, 22);
            ctx.fillStyle = "#fff";
            ctx.fillText(label, 16, 23);
          }
        }
      }
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [
    seatBoxes,
    session.source_type,
    live?.per_seat,
    live?.persons_detected,
  ]);

  // Wall-clock only (fixes 30s jump from Redis elapsed)
  const elapsed =
    session.started_at && isLive
      ? Math.max(0, (Date.now() - Date.parse(session.started_at)) / 1000)
      : live?.elapsed_sec ?? 0;
  const windowSec = live?.window_seconds ?? 30;
  const nextWindow =
    isLive && windowSec > 0 ? Math.max(0, windowSec - (elapsed % windowSec)) : null;

  const seats = live?.per_seat ?? [];
  const groups = live?.groups ?? [];
  const alerts = live?.alerts ?? [];
  const ttoi = live?.ttoi;
  const coverage = live?.coverage_pct;
  const persons = live?.persons_detected;
  const inSeats = live?.persons_in_seats;

  return (
    <div className="lecture-cockpit">
      <div className="cockpit-toolbar">
        <div className="cockpit-timer" aria-live="polite">
          <span className="label">Session clock</span>
          <span className="value">{formatElapsed(elapsed)}</span>
          {isLive ? <span className="live-badge">Live</span> : null}
          {nextWindow != null ? (
            <span className="window-eta">
              Next metrics in {Math.ceil(nextWindow)}s
            </span>
          ) : null}
        </div>
        <div className="cockpit-actions">
          {!isLive ? (
            <button
              type="button"
              className="btn-primary"
              disabled={starting}
              onClick={() => {
                // Stop getUserMedia immediately (don't wait for React effect)
                const v = videoRef.current;
                if (v?.srcObject) {
                  (v.srcObject as MediaStream).getTracks().forEach((tr) => tr.stop());
                  v.srcObject = null;
                }
                onStart();
              }}
            >
              <Play size={18} />
              {starting ? "Starting…" : "Start lecture"}
            </button>
          ) : (
            <button
              type="button"
              className="btn-danger"
              disabled={stopping}
              onClick={() => onStop()}
            >
              <Square size={16} />
              {stopping ? "Stopping…" : "Stop lecture"}
            </button>
          )}
          {session.status === "complete" || live?.status === "complete" ? (
            <Link className="btn-secondary" to={`/sessions/${session.id}/results`}>
              View review
            </Link>
          ) : null}
        </div>
      </div>

      {error ? <p className="sessions-error">{error}</p> : null}

      {isLive ? (
        <div
          className={`detect-banner${
            persons != null && persons > 0 ? " ok" : persons === 0 ? " bad" : ""
          }`}
        >
          {live?.detection_hint ||
            (persons == null
              ? "Camera starting… seat colors update every ~30s; people count updates sooner."
              : persons > 0
                ? `Seeing ${persons} person(s)${
                    inSeats != null ? `, ${inSeats} in drawn seats` : ""
                  }.`
                : "Seeing 0 people — check lighting and that Setup used the same webcam.")}
          <Link to={`/rooms/${session.room_config_id}/edit`}>Adjust seat boxes</Link>
        </div>
      ) : null}

      <div className={`cockpit-grid${secondaryLabel ? " dual" : ""}`}>
        <div className="cockpit-preview-col">
          <div className="preview-pane">
            <header>
              <strong>Primary camera</strong>
              <span>
                {session.source_type.replace("_", " ")}
                {session.source_url ? ` · ${session.source_url}` : ""}
              </span>
            </header>
            {session.source_type === "webcam" && !workerOwnsCamera ? (
              <div className="preview-stack">
                <video ref={videoRef} playsInline muted className="preview-video" />
                <canvas ref={overlayRef} className="preview-overlay" aria-hidden />
              </div>
            ) : workerOwnsCamera && workerPreviewUrl ? (
              <div className="preview-stack">
                <img
                  src={workerPreviewUrl}
                  alt="Worker camera preview with seat and person overlays"
                  className="preview-video worker-jpeg"
                />
              </div>
            ) : workerOwnsCamera ? (
              <div className="preview-placeholder live-worker">
                <strong>
                  {starting && !isLive
                    ? "Handing camera to analysis…"
                    : "Starting worker preview…"}
                </strong>
                <span>
                  Frames come from the analysis worker (Windows allows one camera
                  owner). Seat boxes and person outlines appear once detection
                  runs.
                </span>
                {live?.detection_hint &&
                /loading|opening worker/i.test(live.detection_hint) ? (
                  <span className="detect-pill">Loading vision model…</span>
                ) : persons != null ? (
                  <span className={`detect-pill${persons > 0 ? " ok" : " bad"}`}>
                    {persons > 0
                      ? `${persons} person(s) detected — preview arriving…`
                      : "0 detected — face the camera; first Start can take ~10s"}
                  </span>
                ) : (
                  <span className="detect-pill">Starting vision…</span>
                )}
              </div>
            ) : isLive && workerPreviewUrl ? (
              <div className="preview-stack">
                <img
                  src={workerPreviewUrl}
                  alt="Worker camera preview"
                  className="preview-video worker-jpeg"
                />
              </div>
            ) : (
              <div className="preview-placeholder">
                {isLive
                  ? "Worker is sampling the session source — preview arrives shortly."
                  : "Upload / RTSP sessions use the worker camera — Start lecture to analyze."}
              </div>
            )}
            {previewError ? <p className="preview-err">{previewError}</p> : null}
            <p className="preview-note">
              {isLive
                ? "Live camera with seat boxes and people highlights — anonymous, not face identity."
                : "Align yourself inside the seat outline, then Start lecture. During live you’ll see the worker feed."}
            </p>
          </div>
          {secondaryLabel ? (
            <div className="preview-pane secondary">
              <header>
                <strong>Secondary camera</strong>
                <span>{secondaryLabel}</span>
              </header>
              <div className="preview-placeholder">
                Situational view only — metrics use the primary geometry camera.
              </div>
            </div>
          ) : null}
        </div>

        <aside className="cockpit-metrics">
          <div className="gauge">
            <span className="label">Faced the front</span>
            <span className="value">
              {ttoi != null ? `${Math.round(ttoi)}%` : "—"}
            </span>
          </div>
          <div className="gauge">
            <span className="label">Camera clear</span>
            <span className="value">
              {coverage != null ? `${Math.round(coverage)}%` : "—"}
            </span>
          </div>
          <div className="gauge">
            <span className="label">People in view</span>
            <span className="value">
              {persons != null ? persons : "—"}
              {inSeats != null ? ` · ${inSeats} tracked` : ""}
            </span>
          </div>
          <div className="gauge">
            <span className="label">Seats measured</span>
            <span className="value">
              {live?.usable_seats != null ? live.usable_seats : "—"}
              {live?.expected_seats != null ? ` / ${live.expected_seats}` : ""}
            </span>
          </div>
          <p className="honesty">
            Shows who faces the teaching area — not attention or grades. Drawn
            seats plus “Extra” for people outside those boxes. Good light helps.
          </p>
        </aside>
      </div>

      <div className="cockpit-lower">
        <section className="seat-map-panel" aria-label="Seat orientation map">
          <h3>Who faces the front</h3>
          <p className="panel-sub">
            Green = facing · amber = mixed · red = looking away · grey = can’t
            see. “Extra” = someone outside your drawn seat boxes.
          </p>
          {seats.length === 0 ? (
            <div className="seat-map-empty">
              {isLive
                ? `Waiting for first ${windowSec}s block… people count above updates sooner.`
                : "Start lecture — seat colors appear after each half-minute."}
            </div>
          ) : (
            <ul className="seat-map-grid">
              {seats.map((s) => {
                const band = bandForSeat(s.orientation_pct, s.usable);
                const inGroup = groups.find((g) => g.seat_ids.includes(s.seat_id));
                const label = seatDisplayId(s.seat_id);
                return (
                  <li
                    key={s.seat_id}
                    className={`seat-tile ${band}${inGroup ? " in-group" : ""}`}
                    title={`${label}${inGroup ? ` · ${inGroup.label}` : ""}`}
                  >
                    <span className="seat-id">{label}</span>
                    <span className="seat-o">
                      {s.orientation_pct != null
                        ? `${Math.round(s.orientation_pct)}`
                        : "—"}
                    </span>
                    {inGroup ? (
                      <span className="seat-group">{inGroup.label}</span>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          )}
          {groups.length > 0 ? (
            <ul className="group-list">
              {groups.map((g) => (
                <li key={g.label}>
                  <strong>{g.label}</strong>
                  <span>
                    {g.orientation_pct != null
                      ? `${Math.round(g.orientation_pct)}%`
                      : "—"}{" "}
                    · {g.seat_ids.map(seatDisplayId).join(", ")}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
        </section>

        <section className="event-feed" aria-label="Live events">
          <h3>What changed</h3>
          {alerts.length === 0 ? (
            <p className="panel-sub">
              Longer drops and group patterns show here as each half-minute finishes.
            </p>
          ) : (
            <ul>
              {alerts.map((a, i) => (
                <li key={`${a.kind}-${a.start_sec}-${i}`} className={a.kind}>
                  <strong>
                    {a.kind === "decline_cluster"
                      ? "Cluster looking away"
                      : a.kind === "orientation_decline"
                        ? "Class facing dipped"
                        : a.kind.replace(/_/g, " ")}
                  </strong>
                  <span>
                    {formatElapsed(a.start_sec)}
                    {a.end_sec != null ? `–${formatElapsed(a.end_sec)}` : ""}
                    {a.message ? ` · ${a.message}` : ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
