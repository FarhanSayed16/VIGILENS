import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "../../api/client";
import { listRooms, type Room } from "../../api/rooms";
import { createSession, type SourceType } from "../../api/sessions";
import "./sessions.css";

const STEPS = ["Title & room", "Source", "Privacy"] as const;

const SOURCES: { id: SourceType; title: string; blurb: string }[] = [
  {
    id: "webcam",
    title: "Webcam",
    blurb: "Laptop camera — opens straight on the Lecture Console.",
  },
  {
    id: "upload",
    title: "Upload",
    blurb: "MP4/WebM after class (optional Setup to attach the file).",
  },
  {
    id: "phone_rtsp",
    title: "Phone stream",
    blurb: "IP Webcam / DroidCam / RTSP URL.",
  },
];

export function NewSessionPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [title, setTitle] = useState("");
  const [roomId, setRoomId] = useState<number | "">("");
  const [sourceType, setSourceType] = useState<SourceType>("webcam");
  const [sourceUrl, setSourceUrl] = useState("");
  const [privacyOk, setPrivacyOk] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await listRooms();
        if (!cancelled) {
          setRooms(data);
          if (data.length === 1) setRoomId(data[0].id);
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(
            err instanceof ApiError ? err.message : "Could not load rooms",
          );
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  function canNext(): boolean {
    if (step === 0) {
      return title.trim().length > 0 && roomId !== "";
    }
    if (step === 1) {
      if (sourceType === "phone_rtsp") {
        return sourceUrl.trim().length > 0;
      }
      return true;
    }
    return privacyOk;
  }

  async function onCreate() {
    if (!canNext() || roomId === "") return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const room = rooms.find((r) => r.id === Number(roomId));
      const webcamIdx =
        room?.camera_defaults?.webcam_index != null
          ? Number(room.camera_defaults.webcam_index)
          : 0;
      const session = await createSession({
        title: title.trim(),
        room_config_id: Number(roomId),
        source_type: sourceType,
        source_url:
          sourceType === "phone_rtsp"
            ? sourceUrl.trim()
            : sourceType === "webcam"
              ? `webcam:${webcamIdx}`
              : null,
      });
      // Webcam / phone → Console (Start lecture). Upload still needs Setup for the file.
      if (sourceType === "upload") {
        navigate(`/sessions/${session.id}/setup`);
      } else {
        navigate(`/sessions/${session.id}`);
      }
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : "Create failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <div className="wizard">
        <p className="sessions-error">{loadError}</p>
        <Link to="/sessions">← Back</Link>
      </div>
    );
  }

  if (rooms.length === 0) {
    return (
      <div className="empty-card">
        <h2>No rooms available</h2>
        <p>Create a room with seats and a teaching target before starting a session.</p>
        <div className="btn-row">
          <Link className="btn-primary" to="/rooms/new">
            Create room
          </Link>
          <Link className="btn-secondary" to="/sessions">
            Cancel
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="wizard">
      <h1>New session</h1>
      <p style={{ color: "var(--text-secondary)", marginTop: "0.5rem" }}>
        Pick a room, then go to the Lecture Console. Webcam is the default —
        Setup is only needed for file upload or a different camera.
      </p>

      <ol className="wizard-steps">
        {STEPS.map((label, i) => (
          <li key={label} className={i === step ? "active" : ""}>
            {i + 1}. {label}
          </li>
        ))}
      </ol>

      <div className="wizard-panel">
        {step === 0 ? (
          <>
            <label>
              Session title
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Week 3 — Normalization"
                autoFocus
              />
            </label>
            <label>
              Room
              <select
                value={roomId}
                onChange={(e) =>
                  setRoomId(e.target.value ? Number(e.target.value) : "")
                }
              >
                <option value="">Select a room…</option>
                {rooms.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} ({r.seat_count} seats)
                  </option>
                ))}
              </select>
            </label>
          </>
        ) : null}

        {step === 1 ? (
          <>
            <div className="source-grid">
              {SOURCES.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  className={`source-card${sourceType === s.id ? " selected" : ""}`}
                  onClick={() => setSourceType(s.id)}
                >
                  <strong>{s.title}</strong>
                  <span>{s.blurb}</span>
                </button>
              ))}
            </div>
            {sourceType === "phone_rtsp" ? (
              <label>
                Stream URL
                <input
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                  placeholder="http://192.168.x.x:8080/video or rtsp://…"
                />
              </label>
            ) : sourceType === "webcam" ? (
              <p style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>
                Webcam index 0 is attached automatically (or the room’s saved
                index). You land on the Console — press Start lecture. Change
                camera later under More → Setup if needed.
              </p>
            ) : (
              <p style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>
                Next you will upload the lecture file on Setup.
              </p>
            )}
          </>
        ) : null}

        {step === 2 ? (
          <>
            <div className="privacy-banner">
              <strong>Privacy notice.</strong> Video is processed locally for
              class-level orientation trends (TTOI). Raw video is purged after
              analysis by default. No face recognition, no student names, no
              grading use. Students and institution have already consented for
              this pilot.
            </div>
            <label style={{ flexDirection: "row", alignItems: "flex-start", gap: "0.75rem" }}>
              <input
                type="checkbox"
                checked={privacyOk}
                onChange={(e) => setPrivacyOk(e.target.checked)}
                style={{ marginTop: "0.25rem" }}
              />
              <span>
                I understand this session stores class-level aggregates and will
                not be used to identify or grade students.
              </span>
            </label>
          </>
        ) : null}

        {submitError ? <p className="sessions-error">{submitError}</p> : null}

        <div className="wizard-actions">
          {step === 0 ? (
            <Link className="btn-secondary" to="/sessions">
              Cancel
            </Link>
          ) : (
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setStep((s) => s - 1)}
            >
              Back
            </button>
          )}

          {step < 2 ? (
            <button
              type="button"
              className="btn-primary"
              disabled={!canNext()}
              onClick={() => setStep((s) => s + 1)}
            >
              Continue
            </button>
          ) : (
            <button
              type="button"
              className="btn-primary"
              disabled={!canNext() || submitting}
              onClick={() => void onCreate()}
            >
              {submitting
                ? "Creating…"
                : sourceType === "upload"
                  ? "Create & open Setup"
                  : "Create & open Console"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
