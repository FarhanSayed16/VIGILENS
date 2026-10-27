import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Play, Square } from "lucide-react";
import type { LectureSession } from "../../api/sessions";
import { fetchLivePreviewBlob, pushCameraFrame, type LiveState } from "../../api/live";
import { shouldUsePhoneCamera } from "../../lib/phoneCamera";
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
  const phoneStreamRef = useRef<MediaStream | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [phoneReady, setPhoneReady] = useState(false);
  const [phoneFacing, setPhoneFacing] = useState<"user" | "environment">("user");
  const [workerPreviewUrl, setWorkerPreviewUrl] = useState<string | null>(null);
  const [, setTick] = useState(0);
  const isLive = live?.running === true || session.status === "live";
  const usePhoneCam = shouldUsePhoneCamera(session.source_type, session.source_url);
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

  async function openPhoneCamera(facing: "user" | "environment" = phoneFacing) {
    setPreviewError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setPhoneReady(false);
      setPreviewError(
        "This page is not a secure connection, so the phone will not ask for the camera. Open https:// and the PC’s address, then accept the certificate warning.",
      );
      return false;
    }
    phoneStreamRef.current?.getTracks().forEach((tr) => tr.stop());
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode: facing,
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      });
      phoneStreamRef.current = stream;
      const video = videoRef.current;
      if (video) {
        video.srcObject = stream;
        await video.play().catch(() => undefined);
      }
      setPhoneReady(true);
      return true;
    } catch {
      setPhoneReady(false);
      setPreviewError(
        "Camera permission was blocked. Tap Allow camera and choose Allow. If no prompt appears, use the https:// address and accept the certificate warning.",
      );
      return false;
    }
  }

  useEffect(() => {
    if (!usePhoneCam) return;
    void openPhoneCamera(phoneFacing);
    return () => {
      phoneStreamRef.current?.getTracks().forEach((tr) => tr.stop());
      phoneStreamRef.current = null;
    };
    // Re-ask only when the session or facing direction changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [usePhoneCam, session.id, phoneFacing]);

  useEffect(() => {
    if (!usePhoneCam || !phoneReady || (!isLive && !starting)) return;
    let stopped = false;
    let busy = false;
    const canvas = document.createElement("canvas");
    const tick = async () => {
      if (stopped || busy) return;
      const video = videoRef.current;
      if (!video || video.readyState < 2) return;
      const vw = video.videoWidth || 640;
      const vh = video.videoHeight || 480;
      const w = Math.min(960, vw);
      const h = Math.max(1, Math.round(w * (vh / vw)));
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(video, 0, 0, w, h);
      busy = true;
      const blob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob((b) => resolve(b), "image/jpeg", 0.72),
      );
      if (blob && !stopped) {
        try {
          await pushCameraFrame(session.id, blob);
        } catch {
          /* next tick */
        }
      }
      busy = false;
    };
    const id = window.setInterval(() => void tick(), 140);
    return () => {
      stopped = true;
      window.clearInterval(id);
    };
  }, [usePhoneCam, phoneReady, isLive, starting, session.id]);

  // Preview BEFORE live only. On Windows the browser exclusive-locks the cam;
  // OpenCV (worker) then often gets black frames → "0 detected". Release on Start.
  useEffect(() => {
    const v = videoRef.current;
    if (usePhoneCam) return;
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
  }, [session.source_type, session.id, workerOwnsCamera, usePhoneCam]);

  // Draw seat ROI boxes on preview (geometry guide — not YOLO face boxes)
  useEffect(() => {
    const video = videoRef.current;
    const canvas = overlayRef.current;
    if (!video || !canvas || (session.source_type !== "webcam" && !usePhoneCam)) return;

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
    session.source_type,
    usePhoneCam,
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
                if (usePhoneCam) {
                  void (async () => {
                    const ok = phoneReady || (await openPhoneCamera(phoneFacing));
                    if (!ok) return;
                    onStart({ browserCamera: true });
                  })();
                  return;
                }
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
                ? `Seeing ${persons} face(s)${
                    inSeats != null ? `, ${inSeats} registered` : ""
                  }.`
                : "No face yet — look at the camera and hold still.")}
          <Link to={`/rooms/${session.room_config_id}/edit`}>Room camera</Link>
        </div>
      ) : null}

      <div className={`cockpit-grid${secondaryLabel ? " dual" : ""}`}>
        <div className="cockpit-preview-col">
          <div className="preview-pane">
            <header>
              <strong>Primary camera</strong>
              <span>
                {usePhoneCam
                  ? "This phone"
                  : session.source_type.replace("_", " ")}
                {!usePhoneCam && session.source_url ? ` · ${session.source_url}` : ""}
              </span>
            </header>
            {usePhoneCam ? (
              <div className="preview-stack">
                <video
                  ref={videoRef}
                  playsInline
                  muted
                  autoPlay
                  className={
                    workerPreviewUrl
                      ? "preview-video phone-capture-only"
                      : "preview-video"
                  }
                />
                {workerPreviewUrl ? (
                  <img
                    src={workerPreviewUrl}
                    alt="Live face boxes from this phone"
                    className="preview-video worker-jpeg"
                  />
                ) : null}
                <canvas ref={overlayRef} className="preview-overlay" aria-hidden />
                <div className="phone-cam-actions">
                  {!phoneReady ? (
                    <button
                      type="button"
                      className="btn-primary"
                      onClick={() => void openPhoneCamera(phoneFacing)}
                    >
                      Allow camera
                    </button>
                  ) : null}
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() =>
                      setPhoneFacing((f) => (f === "user" ? "environment" : "user"))
                    }
                  >
                    {phoneFacing === "user" ? "Use back camera" : "Use front camera"}
                  </button>
                </div>
              </div>
            ) : session.source_type === "webcam" && !workerOwnsCamera ? (
              <div className="preview-stack">
                <video ref={videoRef} playsInline muted className="preview-video" />
                <canvas ref={overlayRef} className="preview-overlay" aria-hidden />
              </div>
            ) : workerOwnsCamera && workerPreviewUrl ? (
              <div className="preview-stack">
                <img
                  src={workerPreviewUrl}
                  alt="Live face boxes from the camera"
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
                  owner). A face box appears once a face is in view. It locks
                  after the face holds still.
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
              {usePhoneCam
                ? "This phone is the camera. Allow the prompt, then Start lecture. Frames are sent to the computer for analysis — no names are stored."
                : isLive
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
              {inSeats != null ? ` · ${inSeats} registered` : ""}
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
            Shows who faces the teaching area — not attention or grades. A box
            appears only after a face with both eyes holds still. Good light helps.
          </p>
        </aside>
      </div>

      <div className="cockpit-lower">
        <section className="seat-map-panel" aria-label="Seat orientation map">
          <h3>Who faces the front</h3>
          <p className="panel-sub">
            Green = facing · amber = mixed · red = looking away · grey = face
            locked but not clear right now. Empty chairs are not shown.
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
