import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";
import { ApiError } from "../../api/client";
import { listRooms, type Room } from "../../api/rooms";
import "./rooms.css";

export function RoomsPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await listRooms();
        if (!cancelled) setRooms(data);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : "Could not load rooms. Is the API and Postgres running?",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <div className="rooms-header">
        <div>
          <h1>Rooms</h1>
          <p>
            Reusable seat regions and teaching-target ROI. Regions are seats —
            not named students.
          </p>
        </div>
        <Link className="btn-primary" to="/rooms/new">
          <Plus size={16} /> Create room
        </Link>
      </div>

      {error ? <p className="rooms-error">{error}</p> : null}
      {loading ? <p>Loading rooms…</p> : null}

      {!loading && !error && rooms.length === 0 ? (
        <div className="page-stub">
          <p>No rooms yet. Create one and draw seats on a calibration frame.</p>
        </div>
      ) : null}

      {rooms.length > 0 ? (
        <table className="rooms-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Seats</th>
              <th>Target</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rooms.map((r) => (
              <tr key={r.id}>
                <td>{r.name}</td>
                <td>{r.seat_count}</td>
                <td>{r.target_roi ? "Set" : "—"}</td>
                <td>
                  <Link to={`/rooms/${r.id}/edit`}>Edit</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}

      <div className="privacy-strip">
        Class-level geometry only — no student identity is stored with seats.
      </div>
    </div>
  );
}
