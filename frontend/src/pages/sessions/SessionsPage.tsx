import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";
import { ApiError } from "../../api/client";
import { listRooms, type Room } from "../../api/rooms";
import {
  deleteSession,
  listSessions,
  type LectureSession,
  type SessionStatus,
} from "../../api/sessions";
import "./sessions.css";

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

export function SessionsPage() {
  const [sessions, setSessions] = useState<LectureSession[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [roomFilter, setRoomFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [deletingId, setDeletingId] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [sess, roomList] = await Promise.all([
        listSessions({
          room_config_id: roomFilter ? Number(roomFilter) : undefined,
          status: statusFilter || undefined,
        }),
        listRooms(),
      ]);
      setSessions(sess.items);
      setRooms(roomList);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not load sessions. Is the API and Postgres running?",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload when filters change
  }, [roomFilter, statusFilter]);

  const filtersActive = Boolean(roomFilter || statusFilter);

  const emptyHint = useMemo(() => {
    if (rooms.length === 0) {
      return {
        title: "Create a room first",
        body: "Sessions need a room with seat regions and a teaching target before you record a lecture.",
        primary: { to: "/rooms/new", label: "Create room" },
        secondary: null as { to: string; label: string } | null,
        clearFilters: false,
      };
    }
    if (filtersActive) {
      return {
        title: "No sessions match these filters",
        body: "Try clearing room or status filters, or create a new session.",
        primary: { to: "/sessions/new", label: "New session" },
        secondary: { to: "/rooms", label: "Manage rooms" },
        clearFilters: true,
      };
    }
    return {
      title: "No lectures yet",
      body: "Start a new session, choose a room and source type, then attach video in Setup.",
      primary: { to: "/sessions/new", label: "New session" },
      secondary: { to: "/rooms", label: "Manage rooms" },
      clearFilters: false,
    };
  }, [rooms.length, filtersActive]);

  async function onDelete(id: number, title: string) {
    if (!window.confirm(`Delete session “${title}”? This cannot be undone.`)) {
      return;
    }
    setDeletingId(id);
    try {
      await deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div>
      <div className="sessions-header">
        <div>
          <h1>Sessions</h1>
          <p>
            Lecture units linked to a room. Class-level TTOI analysis comes after
            video setup and the analysis job — not individual attention scores.
          </p>
        </div>
        <Link
          className="btn-primary"
          to="/sessions/new"
          aria-disabled={rooms.length === 0}
          onClick={(e) => {
            if (rooms.length === 0) e.preventDefault();
          }}
          style={rooms.length === 0 ? { opacity: 0.5, pointerEvents: "none" } : undefined}
        >
          <Plus size={16} /> New session
        </Link>
      </div>

      <div className="sessions-filters">
        <label>
          Room
          <select
            value={roomFilter}
            onChange={(e) => setRoomFilter(e.target.value)}
          >
            <option value="">All rooms</option>
            {rooms.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All statuses</option>
            {(
              [
                "draft",
                "ready",
                "analyzing",
                "complete",
                "error",
                "purged_video",
              ] as SessionStatus[]
            ).map((s) => (
              <option key={s} value={s}>
                {s.replace("_", " ")}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? <p className="sessions-error">{error}</p> : null}
      {loading ? <p>Loading sessions…</p> : null}

      {!loading && !error && sessions.length === 0 ? (
        <div className="empty-card">
          <h2>{emptyHint.title}</h2>
          <p>{emptyHint.body}</p>
          <div className="btn-row">
            {emptyHint.clearFilters ? (
              <button
                type="button"
                className="btn-primary"
                onClick={() => {
                  setRoomFilter("");
                  setStatusFilter("");
                }}
              >
                Clear filters
              </button>
            ) : (
              <Link className="btn-primary" to={emptyHint.primary.to}>
                {emptyHint.primary.label}
              </Link>
            )}
            {emptyHint.secondary ? (
              <Link className="btn-secondary" to={emptyHint.secondary.to}>
                {emptyHint.secondary.label}
              </Link>
            ) : null}
          </div>
        </div>
      ) : null}

      {sessions.length > 0 ? (
        <table className="sessions-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Room</th>
              <th>Source</th>
              <th>Status</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.id}>
                <td>
                  <Link to={`/sessions/${s.id}`}>{s.title}</Link>
                </td>
                <td>{s.room_name ?? `Room #${s.room_config_id}`}</td>
                <td>{s.source_type.replace("_", " ")}</td>
                <td>
                  <span className={`status-pill ${s.status}`}>
                    {s.status.replace("_", " ")}
                  </span>
                </td>
                <td>{formatDate(s.created_at)}</td>
                <td>
                  <button
                    type="button"
                    className="btn-danger"
                    disabled={deletingId === s.id}
                    onClick={() => void onDelete(s.id, s.title)}
                  >
                    {deletingId === s.id ? "Deleting…" : "Delete"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}

      <div className="privacy-strip">
        Class-level observable orientation only — not individual attention scores.
      </div>
    </div>
  );
}
