import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useBlocker, useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../../api/client";
import {
  createRoom,
  getRoom,
  updateRoom,
  type BoxRegion,
  type CameraDefaults,
} from "../../api/rooms";
import {
  SeatRegionCanvas,
  type DrawTool,
} from "../../components/domain/SeatRegionCanvas";
import "./rooms.css";

export function RoomEditorPage() {
  const { roomId } = useParams();
  const isNew = !roomId || roomId === "new";
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [seats, setSeats] = useState<BoxRegion[]>([]);
  const [target, setTarget] = useState<BoxRegion | null>(null);
  const [camera, setCamera] = useState<CameraDefaults>({
    preferred_source: "upload",
    webcam_index: 0,
  });
  const [tool, setTool] = useState<DrawTool>("seat");
  const [selectedSeatId, setSelectedSeatId] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!isNew);

  const blocker = useBlocker(dirty);

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
        setCamera(room.camera_defaults ?? { preferred_source: "upload", webcam_index: 0 });
        setDirty(false);
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

  function onFile(file: File | null) {
    if (!file) return;
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    setImageUrl(URL.createObjectURL(file));
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

  async function onSave(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!name.trim()) {
      setError("Room name is required.");
      return;
    }
    setSaving(true);
    const payload = {
      name: name.trim(),
      seat_regions: seats,
      target_roi: target,
      camera_defaults: camera,
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
            Draw seat boxes and a teaching-target zone on a calibration frame.
            Coordinates are normalized 0–1.
          </p>
        </div>
        <Link to="/rooms">Cancel</Link>
      </div>

      {error ? <p className="rooms-error">{error}</p> : null}

      <form onSubmit={onSave}>
        <div className="editor-layout">
          <div>
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
              <button type="button" onClick={undoLastSeat} disabled={!seats.length}>
                Undo last seat
              </button>
              <label className="ghost-btn" style={{ cursor: "pointer" }}>
                Upload frame
                <input
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={(e) => onFile(e.target.files?.[0] ?? null)}
                />
              </label>
            </div>
            <p className="hint">
              Drag on the frame to draw. Amber dashed box = teaching target
              (board/screen). Teal boxes = seats.
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
                value={camera.preferred_source ?? "upload"}
                onChange={(e) => {
                  setCamera({
                    ...camera,
                    preferred_source: e.target.value as CameraDefaults["preferred_source"],
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
          </aside>
        </div>
      </form>
    </div>
  );
}
