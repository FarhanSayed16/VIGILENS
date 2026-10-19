import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link, useBlocker, useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../../api/client";
import {
  createRoom,
  detectCalibration,
  getRoom,
  suggestCalibration,
  updateRoom,
  type BoxRegion,
  type CameraDefaults,
  type CameraPlacement,
} from "../../api/rooms";
import {
  SeatRegionCanvas,
  type DrawTool,
} from "../../components/domain/SeatRegionCanvas";
import "./rooms.css";

const PLACEMENTS: {
  id: CameraPlacement;
  title: string;
  body: string;
}[] = [
  {
    id: "back_of_room",
    title: "Behind the class",
    body: "Camera at the back, looking toward the board. Most common lecture setup.",
  },
  {
    id: "facing_class",
    title: "Facing the students",
    body: "Camera looks at faces (usual test). Only people become seats — no board box. Looking at the camera = toward the board.",
  },
  {
    id: "left_side",
    title: "Left side of room",
    body: "Camera on the left wall looking across the rows toward the right.",
  },
  {
    id: "right_side",
    title: "Right side of room",
    body: "Camera on the right wall looking across the rows toward the left.",
  },
];

export function RoomEditorPage() {
  const { roomId } = useParams();
  const isNew = !roomId || roomId === "new";
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [seats, setSeats] = useState<BoxRegion[]>([]);
  const [target, setTarget] = useState<BoxRegion | null>(null);
  const [camera, setCamera] = useState<CameraDefaults>({
    preferred_source: "webcam",
    webcam_index: 0,
    placement: "back_of_room",
  });
  const [tool, setTool] = useState<DrawTool>("click_target");
  const [selectedSeatId, setSelectedSeatId] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [frameFile, setFrameFile] = useState<File | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(!isNew);
  const [mode, setMode] = useState<"quick" | "advanced">("quick");
  const [step, setStep] = useState(1);
  const [placement, setPlacement] = useState<CameraPlacement>("back_of_room");
  const [rows, setRows] = useState(3);
  const [cols, setCols] = useState(4);
  const [busy, setBusy] = useState(false);
  const [camOpen, setCamOpen] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const blocker = useBlocker(dirty);

  function stopCamera() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCamOpen(false);
  }

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  useEffect(() => {
    if (!camOpen || !streamRef.current) return;
    const el = videoRef.current;
    if (!el) return;
    el.srcObject = streamRef.current;
    void el.play().catch(() => {
      setError("Camera opened but playback failed — try again or upload a photo.");
    });
  }, [camOpen]);

  useEffect(() => {
    if (blocker.state === "blocked") {
      const ok = window.confirm("You have unsaved changes. Leave this page?");
      if (ok) blocker.proceed();
      else blocker.reset();
    }
  }, [blocker]);

  useEffect(() => {
    if (isNew) return;
    const id = Number(roomId);
    if (!Number.isFinite(id)) {
      setError("Invalid room id");
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const room = await getRoom(id);
        if (cancelled) return;
        setName(room.name);
        setSeats((room.seat_regions as BoxRegion[]) ?? []);
        setTarget((room.target_roi as BoxRegion | null) ?? null);
        setCamera(
          room.camera_defaults ?? {
            preferred_source: "webcam",
            webcam_index: 0,
          },
        );
        const p = room.camera_defaults?.placement as CameraPlacement | undefined;
        if (p && PLACEMENTS.some((x) => x.id === p)) setPlacement(p);
        setDirty(false);
        setMode(room.seat_regions?.length ? "advanced" : "quick");
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load room");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isNew, roomId]);

  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  const selectedSeat = useMemo(
    () => seats.find((s) => s.id === selectedSeatId) ?? null,
    [seats, selectedSeatId],
  );

  function markDirty() {
    setDirty(true);
  }

  function setFrame(file: File | null) {
    if (!file) return;
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    setImageUrl(URL.createObjectURL(file));
    setFrameFile(file);
    markDirty();
  }

  function deleteSelectedSeat() {
    if (!selectedSeatId) return;
    setSeats((prev) => prev.filter((s) => s.id !== selectedSeatId));
    setSelectedSeatId(null);
    markDirty();
  }

  function undoLastSeat() {
    setSeats((prev) => prev.slice(0, -1));
    markDirty();
  }

  const towardCamera = placement === "facing_class";

  async function applyGrid() {
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const res = await suggestCalibration({ placement, rows, cols });
      setSeats(res.seat_regions);
      setTarget(res.target_roi ?? null);
      setCamera((c) => ({
        ...c,
        placement,
        facing_mode: res.facing_mode || (towardCamera ? "toward_camera" : "toward_board"),
      }));
      setInfo(res.hint);
      setTool(towardCamera ? "select" : "click_target");
      setStep(towardCamera ? 2 : 3);
      markDirty();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Suggest failed");
    } finally {
      setBusy(false);
    }
  }

  async function applyDetect() {
    if (!frameFile) {
      setError("Capture or upload a frame first (step 1).");
      return;
    }
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const res = await detectCalibration(frameFile, { placement, rows, cols });
      setSeats(res.seat_regions);
      setTarget(res.target_roi ?? null);
      setCamera((c) => ({
        ...c,
        placement,
        facing_mode: res.facing_mode || (towardCamera ? "toward_camera" : "toward_board"),
      }));
      setInfo(
        res.message ||
          (res.people_found > 0
            ? towardCamera
              ? `Detected ${res.people_found} person(s) as seats only — no board box.`
              : `Detected ${res.people_found} people as seats. Tap the board if the amber box is wrong.`
            : res.hint),
      );
      setTool(towardCamera ? "select" : "click_target");
      setStep(towardCamera ? 2 : 3);
      markDirty();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Detect failed");
    } finally {
      setBusy(false);
    }
  }

  async function openCamera() {
    setError(null);
    setBusy(true);
    setStep(1);
    stopCamera();
    try {
      let videoConstraint: MediaTrackConstraints = {
        width: { ideal: 1280 },
        height: { ideal: 720 },
      };
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const cams = devices.filter((d) => d.kind === "videoinput");
        const idx = camera.webcam_index ?? 0;
        const pick = cams[Math.max(0, Math.min(idx, cams.length - 1))];
        if (pick?.deviceId) {
          videoConstraint = {
            ...videoConstraint,
            deviceId: { ideal: pick.deviceId },
          };
        }
      } catch {
        /* default camera */
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: videoConstraint,
        audio: false,
      });
      streamRef.current = stream;
      setCamOpen(true);
    } catch (err) {
      setCamOpen(false);
      setError(
        err instanceof Error
          ? err.message
          : "Could not access camera — allow permission or upload a photo.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function captureFromPreview() {
    const video = videoRef.current;
    if (!video || !streamRef.current) {
      setError("Camera is not open.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await new Promise((r) => setTimeout(r, 100));
      const w = video.videoWidth || 1280;
      const h = video.videoHeight || 720;
      if (w < 2 || h < 2) {
        throw new Error("Camera not ready yet — wait a moment and capture again.");
      }
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Canvas unavailable");
      ctx.drawImage(video, 0, 0, w, h);
      const blob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob(
          (b) => (b ? resolve(b) : reject(new Error("Capture failed"))),
          "image/jpeg",
          0.92,
        );
      });
      const file = new File([blob], "calibration_webcam.jpg", {
        type: "image/jpeg",
      });
      setFrame(file);
      stopCamera();
      setStep(2);
      setInfo("Frame captured — pick camera viewpoint below, then detect seats.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Capture failed");
    } finally {
      setBusy(false);
    }
  }

  async function onSave(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!name.trim()) {
      setError("Room name is required.");
      return;
    }
    if (seats.length === 0) {
      setError("Add at least one seat (Quick setup or Advanced draw).");
      return;
    }
    const facingMode =
      camera.facing_mode ||
      (placement === "facing_class" ? "toward_camera" : "toward_board");
    if (facingMode !== "toward_camera" && !target) {
      setError("Mark the board/screen (amber target) — required unless facing students.");
      return;
    }
    setSaving(true);
    const payload = {
      name: name.trim(),
      seat_regions: seats,
      target_roi: facingMode === "toward_camera" ? null : target,
      camera_defaults: { ...camera, placement, facing_mode: facingMode },
    };
    try {
      if (isNew) {
        const created = await createRoom(payload);
        setDirty(false);
        navigate(`/rooms/${created.id}/edit`, { replace: true });
      } else {
        await updateRoom(Number(roomId), payload);
        setDirty(false);
        navigate("/rooms");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p>Loading room…</p>;

  return (
    <div>
      <div className="rooms-header">
        <div>
          <h1>{isNew ? "Create room" : "Edit room"}</h1>
          <p>
            Quick calibration: three steps — frame, camera viewpoint, seats +
            board. Advanced drawing is optional.
          </p>
        </div>
        <Link to="/rooms">Cancel</Link>
      </div>

      {error ? <p className="rooms-error">{error}</p> : null}
      {info ? <p className="rooms-info">{info}</p> : null}

      <div className="mode-toggle" role="group" aria-label="Editor mode">
        <button
          type="button"
          className={mode === "quick" ? "active" : ""}
          onClick={() => {
            setMode("quick");
            setTool("click_target");
          }}
        >
          Quick setup
        </button>
        <button
          type="button"
          className={mode === "advanced" ? "active" : ""}
          onClick={() => {
            setMode("advanced");
            setTool("seat");
          }}
        >
          Advanced draw
        </button>
      </div>

      <form onSubmit={onSave}>
        <div className="editor-layout">
          <div>
            {mode === "quick" ? (
              <div className="quick-steps">
                <div className={`quick-step current`}>
                  <h2>1 · Get a frame</h2>
                  <p>
                    Open the camera for a live preview, then capture a still — or
                    upload a photo from this camera’s view.
                  </p>
                  <div className="tool-row">
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={busy}
                      onClick={() => void openCamera()}
                    >
                      {camOpen ? "Restart camera" : "Open camera"}
                    </button>
                    <label className="ghost-btn" style={{ cursor: "pointer" }}>
                      Upload photo
                      <input
                        type="file"
                        accept="image/*"
                        hidden
                        onChange={(e) => {
                          const f = e.target.files?.[0] ?? null;
                          if (f) {
                            stopCamera();
                            setFrame(f);
                            setStep(2);
                            setInfo("Photo loaded — continue with viewpoint below.");
                          }
                        }}
                      />
                    </label>
                  </div>

                  {camOpen ? (
                    <div className="cam-preview-panel" aria-label="Live camera preview">
                      <div className="cam-preview-frame">
                        <video
                          ref={videoRef}
                          className="cam-preview-video"
                          playsInline
                          muted
                          autoPlay
                        />
                        <span className="cam-live-badge">Live</span>
                      </div>
                      <div className="tool-row cam-preview-actions">
                        <button
                          type="button"
                          className="btn-primary"
                          disabled={busy}
                          onClick={() => void captureFromPreview()}
                        >
                          {busy ? "Capturing…" : "Capture this frame"}
                        </button>
                        <button
                          type="button"
                          className="ghost-btn"
                          onClick={() => stopCamera()}
                        >
                          Close camera
                        </button>
                      </div>
                      <p className="hint">
                        Sit where a student would sit, aim the camera, then
                        capture. The still appears on the calibration frame below.
                      </p>
                    </div>
                  ) : null}

                  {!camOpen && imageUrl ? (
                    <p className="frame-ready-banner">
                      Frame ready — scroll to the image below if needed, then
                      choose viewpoint in step 2.
                      <button
                        type="button"
                        className="ghost-btn"
                        style={{ marginLeft: "0.5rem" }}
                        onClick={() => void openCamera()}
                      >
                        Retake
                      </button>
                    </p>
                  ) : null}

                  <p className="hint" style={{ marginTop: "0.75rem" }}>
                    Calibration frame (captured still)
                  </p>
                  <SeatRegionCanvas
                    imageUrl={imageUrl}
                    seats={seats}
                    target={towardCamera ? null : target}
                    tool={towardCamera ? "select" : "click_target"}
                    selectedSeatId={selectedSeatId}
                    onSeatsChange={(next) => {
                      setSeats(next);
                      markDirty();
                    }}
                    onTargetChange={(next) => {
                      setTarget(next);
                      markDirty();
                    }}
                    onSelectSeat={setSelectedSeatId}
                  />
                  {towardCamera && seats.length > 0 ? (
                    <p className="rooms-info" style={{ marginTop: "0.75rem" }}>
                      Toward-camera mode: teal boxes are people/seats only. No board
                      is drawn — looking at the camera counts as oriented toward the board.
                    </p>
                  ) : null}
                </div>

                {!camOpen ? (
                  <div
                    className={`quick-step${step >= 2 ? " current" : ""}${
                      !imageUrl ? " muted-step" : ""
                    }`}
                  >
                    <h2>2 · Where is the camera?</h2>
                    <p>
                      {imageUrl
                        ? "Pick the viewpoint that matches this room. Seats and board zones are suggested from that."
                        : "Capture or upload a frame in step 1 first."}
                    </p>
                    {imageUrl ? (
                      <>
                        <div className="placement-grid">
                          {PLACEMENTS.map((p) => (
                            <button
                              key={p.id}
                              type="button"
                              className={`placement-card${
                                placement === p.id ? " selected" : ""
                              }`}
                              onClick={() => {
                                setPlacement(p.id);
                                if (p.id === "facing_class") {
                                  setTarget(null);
                                  setCamera((c) => ({
                                    ...c,
                                    placement: p.id,
                                    facing_mode: "toward_camera",
                                  }));
                                  setTool("select");
                                } else {
                                  setCamera((c) => ({
                                    ...c,
                                    placement: p.id,
                                    facing_mode: "toward_board",
                                  }));
                                  setTool("click_target");
                                }
                                markDirty();
                              }}
                            >
                              <strong>{p.title}</strong>
                              <span>{p.body}</span>
                            </button>
                          ))}
                        </div>
                        <div className="grid-size-row">
                          <label>
                            Rows
                            <input
                              type="number"
                              min={1}
                              max={12}
                              value={rows}
                              onChange={(e) =>
                                setRows(Number(e.target.value) || 1)
                              }
                            />
                          </label>
                          <label>
                            Columns
                            <input
                              type="number"
                              min={1}
                              max={12}
                              value={cols}
                              onChange={(e) =>
                                setCols(Number(e.target.value) || 1)
                              }
                            />
                          </label>
                        </div>
                        <div className="tool-row">
                          <button
                            type="button"
                            className="btn-primary"
                            disabled={busy || !imageUrl}
                            onClick={() => void applyDetect()}
                          >
                            {busy ? "Detecting…" : "Detect people → seats"}
                          </button>
                          <button
                            type="button"
                            className="ghost-btn"
                            disabled={busy}
                            onClick={() => void applyGrid()}
                          >
                            Use seat grid only
                          </button>
                        </div>
                      </>
                    ) : null}
                  </div>
                ) : null}

                {!camOpen && imageUrl && !towardCamera ? (
                  <div className={`quick-step${step >= 3 ? " current" : ""}`}>
                    <h2>3 · Confirm the board</h2>
                    <p>
                      Tap the board or screen on the frame above (amber box).
                      Then save the room.
                    </p>
                  </div>
                ) : null}
                {!camOpen && imageUrl && towardCamera && seats.length > 0 ? (
                  <div className="quick-step current">
                    <h2>3 · Save</h2>
                    <p>
                      Seats are set from people. No board step needed for this
                      viewpoint — save the room when ready.
                    </p>
                  </div>
                ) : null}
              </div>
            ) : (
              <>
                <div className="tool-row">
                  <button
                    type="button"
                    className={tool === "select" ? "active" : ""}
                    onClick={() => setTool("select")}
                  >
                    Select
                  </button>
                  <button
                    type="button"
                    className={tool === "seat" ? "active" : ""}
                    onClick={() => setTool("seat")}
                  >
                    Draw seat
                  </button>
                  <button
                    type="button"
                    className={tool === "target" ? "active" : ""}
                    onClick={() => setTool("target")}
                  >
                    Draw target
                  </button>
                  <button
                    type="button"
                    onClick={undoLastSeat}
                    disabled={!seats.length}
                  >
                    Undo last seat
                  </button>
                  <label className="ghost-btn" style={{ cursor: "pointer" }}>
                    Upload frame
                    <input
                      type="file"
                      accept="image/*"
                      hidden
                      onChange={(e) => setFrame(e.target.files?.[0] ?? null)}
                    />
                  </label>
                </div>
                <p className="hint">
                  Drag on the frame to draw. Amber dashed box = teaching target.
                  Teal = seats.
                </p>
                <SeatRegionCanvas
                  imageUrl={imageUrl}
                  seats={seats}
                  target={target}
                  tool={tool}
                  selectedSeatId={selectedSeatId}
                  onSeatsChange={(next) => {
                    setSeats(next);
                    markDirty();
                  }}
                  onTargetChange={(next) => {
                    setTarget(next);
                    markDirty();
                  }}
                  onSelectSeat={setSelectedSeatId}
                />
              </>
            )}
          </div>

          <aside className="editor-panel">
            <h2>Room details</h2>
            <label>
              Name
              <input
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  markDirty();
                }}
                placeholder="Lecture Hall A"
                required
              />
            </label>
            <label>
              Preferred source
              <select
                value={camera.preferred_source ?? "webcam"}
                onChange={(e) => {
                  setCamera({
                    ...camera,
                    preferred_source: e.target
                      .value as CameraDefaults["preferred_source"],
                  });
                  markDirty();
                }}
              >
                <option value="upload">Upload</option>
                <option value="webcam">Webcam</option>
                <option value="phone_rtsp">Phone stream</option>
              </select>
            </label>
            <label>
              Webcam index
              <input
                type="number"
                min={0}
                max={10}
                value={camera.webcam_index ?? 0}
                onChange={(e) => {
                  setCamera({ ...camera, webcam_index: Number(e.target.value) });
                  markDirty();
                }}
              />
            </label>

            <h2>Seats ({seats.length})</h2>
            <ul className="seat-list">
              {seats.map((s) => (
                <li
                  key={s.id}
                  className={selectedSeatId === s.id ? "selected" : ""}
                  onClick={() => setSelectedSeatId(s.id)}
                >
                  <span>{s.label ?? s.id}</span>
                </li>
              ))}
            </ul>
            {selectedSeat ? (
              <div className="editor-actions">
                <button type="button" className="ghost-btn" onClick={deleteSelectedSeat}>
                  Delete selected seat
                </button>
              </div>
            ) : null}

            <div className="editor-actions">
              <button type="submit" className="btn-primary" disabled={saving}>
                {saving ? "Saving…" : "Save room"}
              </button>
              <Link className="ghost-btn" to="/rooms">
                Back to list
              </Link>
            </div>
            {dirty ? <p className="hint">Unsaved changes</p> : null}
            {!towardCamera && !target ? (
              <p className="hint">Board target required before analysis.</p>
            ) : null}
            {towardCamera ? (
              <p className="hint">Toward-camera: board box not used.</p>
            ) : null}
          </aside>
        </div>
      </form>
    </div>
  );
}
