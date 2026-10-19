import { FormEvent, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Camera, Phone, Trash2, Upload } from "lucide-react";
import { ApiError } from "../../api/client";
import {
  DEFAULT_MAX_UPLOAD_MB,
  deleteSessionVideo,
  formatBytes,
  isAllowedVideoFile,
  setSessionSource,
  uploadSessionVideo,
} from "../../api/media";
import { getRoom, type Room } from "../../api/rooms";
import { getSession, type LectureSession, type SourceType } from "../../api/sessions";
import "../sessions/sessions.css";
import "./setup.css";

type Tab = SourceType;

export function SetupPage() {
  const { sessionId } = useParams();
  const id = Number(sessionId);

  const [session, setSession] = useState<LectureSession | null>(null);
  const [room, setRoom] = useState<Room | null>(null);
  const [tab, setTab] = useState<Tab>("upload");
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);

  const [webcamIndex, setWebcamIndex] = useState(0);
  const [webcamBusy, setWebcamBusy] = useState(false);
  const [webcamError, setWebcamError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [phoneUrl, setPhoneUrl] = useState("");
  const [phoneBusy, setPhoneBusy] = useState(false);
  const [phoneTestNote, setPhoneTestNote] = useState<string | null>(null);

  const [purging, setPurging] = useState(false);

  function stopWebcam() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }

  useEffect(() => {
    return () => stopWebcam();
  }, []);

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
        if (cancelled) return;
        setSession(s);
        setTab(s.source_type);
        if (s.source_type === "webcam" && s.source_url?.startsWith("webcam:")) {
          setWebcamIndex(Number(s.source_url.replace("webcam:", "")) || 0);
        }
        if (s.source_type === "phone_rtsp" && s.source_url) {
          setPhoneUrl(s.source_url);
        }
        const r = await getRoom(s.room_config_id);
        if (cancelled) return;
        setRoom(r);
        const defaults = r.camera_defaults;
        if (defaults) {
          if (s.source_type === "upload" && defaults.preferred_source) {
            // keep session choice; only prefill hints
          }
          if (defaults.webcam_index != null && !s.source_url) {
            setWebcamIndex(defaults.webcam_index);
          }
          if (
            defaults.phone_url_example &&
            s.source_type === "phone_rtsp" &&
            !s.source_url
          ) {
            setPhoneUrl(defaults.phone_url_example);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError ? err.message : "Could not load setup",
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

  async function refreshSession() {
    const s = await getSession(id);
    setSession(s);
    return s;
  }

  async function handleFile(file: File | null | undefined) {
    if (!file || uploading) return;
    setError(null);
    setOk(null);
    if (!isAllowedVideoFile(file)) {
      setError("Only MP4 and WebM files are supported.");
      return;
    }
    const maxBytes = DEFAULT_MAX_UPLOAD_MB * 1024 * 1024;
    if (file.size > maxBytes) {
      setError(
        `File is ${formatBytes(file.size)} — over the ${DEFAULT_MAX_UPLOAD_MB} MB limit.`,
      );
      return;
    }
    setUploading(true);
    setProgress(0);
    try {
      const result = await uploadSessionVideo(id, file, (p) =>
        setProgress(p.percent),
      );
      await refreshSession();
      setOk(
        `Uploaded ${result.filename} (${formatBytes(result.size_bytes)}). Session is ready.`,
      );
      setTab("upload");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function onSaveWebcam(e: FormEvent) {
    e.preventDefault();
    setWebcamBusy(true);
    setError(null);
    setOk(null);
    try {
      const s = await setSessionSource(id, {
        source_type: "webcam",
        webcam_index: webcamIndex,
      });
      setSession(s);
      setOk(`Webcam source saved (device index ${webcamIndex}).`);
      setTab("webcam");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save webcam");
    } finally {
      setWebcamBusy(false);
    }
  }

  async function startPreview() {
    setWebcamError(null);
    stopWebcam();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { deviceId: undefined },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch {
      setWebcamError(
        "Could not open a camera in this browser. Check permissions, then save the device index for analysis later.",
      );
    }
  }

  async function onSavePhone(e: FormEvent) {
    e.preventDefault();
    const url = phoneUrl.trim();
    if (!url) {
      setError("Enter a phone stream URL (RTSP or HTTP).");
      return;
    }
    setPhoneBusy(true);
    setError(null);
    setOk(null);
    try {
      const s = await setSessionSource(id, {
        source_type: "phone_rtsp",
        source_url: url,
      });
      setSession(s);
      setOk("Phone stream URL saved. Session is ready for analysis.");
      setTab("phone_rtsp");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save URL");
    } finally {
      setPhoneBusy(false);
    }
  }

  function onTestPhone() {
    const url = phoneUrl.trim();
    setPhoneTestNote(null);
    if (!url) {
      setPhoneTestNote("Enter a URL first.");
      return;
    }
    // Browser cannot open RTSP; give honest UX
    if (url.toLowerCase().startsWith("rtsp://")) {
      setPhoneTestNote(
        "RTSP cannot be previewed in the browser. URL format looks usable — save it; the analysis worker will open the stream.",
      );
      return;
    }
    if (url.toLowerCase().startsWith("http://") || url.toLowerCase().startsWith("https://")) {
      window.open(url, "_blank", "noopener,noreferrer");
      setPhoneTestNote("Opened HTTP URL in a new tab for a quick check.");
      return;
    }
    setPhoneTestNote(
      "Unrecognized scheme — use rtsp://, http://, or https://. You can still save if your capture app uses a custom URL.",
    );
  }

  async function onPurge() {
    if (!session?.has_video) return;
    if (
      !window.confirm(
        "Remove the uploaded video file from disk? Session metadata and any analysis results stay.",
      )
    ) {
      return;
    }
    setPurging(true);
    setError(null);
    setOk(null);
    try {
      const s = await deleteSessionVideo(id);
      setSession(s);
      setOk("Video purged from disk. Session metadata kept.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Purge failed");
    } finally {
      setPurging(false);
    }
  }

  if (loading) return <p>Loading setup…</p>;

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
    <div className="setup-page">
      <p style={{ margin: "0 0 0.5rem" }}>
        <Link to={`/sessions/${id}`}>← Console</Link>
      </p>

      <header className="setup-header">
        <div>
          <p className="page-kicker">Source setup</p>
          <p style={{ margin: "0 0 0.5rem", fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>
            Optional for webcam. Detection runs on the Console after Start
            lecture — this page only wires the camera or upload.
          </p>
          <p>
            Attach video or a live source for “{session.title}”
            {room ? ` · ${room.name}` : ""}. Max upload {DEFAULT_MAX_UPLOAD_MB}{" "}
            MB (MP4 / WebM).
          </p>
          {session.source_type === "webcam" && session.source_url ? (
            <p style={{ marginTop: "0.75rem" }}>
              <Link className="btn-primary" to={`/sessions/${id}`}>
                Webcam already saved — go to Console
              </Link>
            </p>
          ) : null}
        </div>
        <div className="setup-status">
          <span className={`status-pill ${session.status}`}>
            {session.status.replace("_", " ")}
          </span>
          <span>{session.has_video ? "Video on disk" : "No file"}</span>
          {session.source_url ? (
            <span className="setup-url" title={session.source_url}>
              {session.source_url}
            </span>
          ) : null}
        </div>
      </header>

      {error ? <p className="sessions-error">{error}</p> : null}
      {ok ? <p className="setup-ok">{ok}</p> : null}

      <div className="source-tabs" role="tablist">
        {(
          [
            { id: "upload" as Tab, label: "Upload", icon: Upload },
            { id: "webcam" as Tab, label: "Webcam", icon: Camera },
            { id: "phone_rtsp" as Tab, label: "Phone", icon: Phone },
          ] as const
        ).map(({ id: tabId, label, icon: Icon }) => (
          <button
            key={tabId}
            type="button"
            role="tab"
            aria-selected={tab === tabId}
            className={`source-tab${tab === tabId ? " active" : ""}`}
            onClick={() => {
              setTab(tabId);
              if (tabId !== "webcam") stopWebcam();
            }}
          >
            <Icon size={16} strokeWidth={1.75} />
            {label}
          </button>
        ))}
      </div>

      {tab === "upload" ? (
        <section className="setup-panel">
          <div
            className={`dropzone${dragOver ? " over" : ""}${uploading ? " busy" : ""}`}
            onDragEnter={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              void handleFile(e.dataTransfer.files?.[0]);
            }}
          >
            <Upload size={28} strokeWidth={1.5} />
            <strong>Drop an MP4 or WebM here</strong>
            <span>or choose a file — streams to the server under the size cap</span>
            <label className="btn-primary dropzone-btn">
              {uploading ? `Uploading ${progress}%` : "Choose file"}
              <input
                type="file"
                accept="video/mp4,video/webm,.mp4,.webm"
                disabled={uploading}
                hidden
                onChange={(e) => {
                  void handleFile(e.target.files?.[0]);
                  e.target.value = "";
                }}
              />
            </label>
            {uploading ? (
              <div className="progress-track" aria-valuenow={progress} role="progressbar">
                <div className="progress-fill" style={{ width: `${progress}%` }} />
              </div>
            ) : null}
          </div>

          {session.has_video ? (
            <div className="setup-file-meta">
              <div>
                <span className="label">Stored path</span>
                <code>{session.video_path ?? "(set)"}</code>
              </div>
              <button
                type="button"
                className="btn-danger"
                disabled={purging}
                onClick={() => void onPurge()}
                style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}
              >
                <Trash2 size={14} />
                {purging ? "Purging…" : "Purge video"}
              </button>
            </div>
          ) : null}
        </section>
      ) : null}

      {tab === "webcam" ? (
        <section className="setup-panel">
          <form onSubmit={(e) => void onSaveWebcam(e)}>
            <label>
              Device index
              <input
                type="number"
                min={0}
                max={10}
                value={webcamIndex}
                onChange={(e) => setWebcamIndex(Number(e.target.value))}
              />
            </label>
            <p className="setup-hint">
              Browser preview uses the default camera. The saved index is what the
              analysis worker will open later (OpenCV-style).
            </p>
            <div className="setup-actions">
              <button type="button" className="btn-secondary" onClick={() => void startPreview()}>
                Start preview
              </button>
              <button type="button" className="btn-secondary" onClick={stopWebcam}>
                Stop preview
              </button>
              <button type="submit" className="btn-primary" disabled={webcamBusy}>
                {webcamBusy ? "Saving…" : "Save webcam source"}
              </button>
            </div>
          </form>
          {webcamError ? <p className="sessions-error">{webcamError}</p> : null}
          <div className="webcam-frame">
            <video ref={videoRef} playsInline muted />
          </div>
        </section>
      ) : null}

      {tab === "phone_rtsp" ? (
        <section className="setup-panel">
          <form onSubmit={(e) => void onSavePhone(e)}>
            <label>
              Stream URL
              <input
                type="url"
                value={phoneUrl}
                onChange={(e) => setPhoneUrl(e.target.value)}
                placeholder="rtsp://… or http://phone-ip:8080/video"
                autoComplete="off"
              />
            </label>
            <p className="setup-hint">
              Typical apps: IP Webcam, DroidCam. Room default hint:{" "}
              {room?.camera_defaults?.phone_url_example || "none"}
            </p>
            <div className="setup-actions">
              <button type="button" className="btn-secondary" onClick={onTestPhone}>
                Test URL
              </button>
              <button type="submit" className="btn-primary" disabled={phoneBusy}>
                {phoneBusy ? "Saving…" : "Save phone source"}
              </button>
            </div>
          </form>
          {phoneTestNote ? <p className="setup-hint">{phoneTestNote}</p> : null}
        </section>
      ) : null}

      <div className="privacy-strip">
        Raw video is temporary on disk under the upload root. Purge removes the
        file; class-level aggregates stay. No student identity is stored.
      </div>
    </div>
  );
}
