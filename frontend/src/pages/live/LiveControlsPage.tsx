import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Flag, Layers } from "lucide-react";
import { ApiError } from "../../api/client";
import { getSession, type LectureSession } from "../../api/sessions";
import {
  TEACHING_MODES,
  createTopic,
  formatElapsed,
  formatModeLabel,
  listModes,
  listTopics,
  setMode,
  type ModeChange,
  type TeachingMode,
  type Topic,
} from "../../api/topics";
import "../sessions/sessions.css";
import "./live.css";

function clockStartIso(session: LectureSession): string {
  return session.started_at ?? session.created_at;
}

export function LiveControlsPage() {
  const { sessionId } = useParams();
  const id = Number(sessionId);

  const [session, setSession] = useState<LectureSession | null>(null);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [modes, setModes] = useState<ModeChange[]>([]);
  const [currentMode, setCurrentMode] = useState<TeachingMode | null>(null);
  const [label, setLabel] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingTopic, setSavingTopic] = useState(false);
  const [savingMode, setSavingMode] = useState(false);

  async function refreshMarkers(sessionRow?: LectureSession | null) {
    const [t, m] = await Promise.all([listTopics(id), listModes(id)]);
    setTopics(t.items);
    setModes(m.items);
    setCurrentMode(
      m.current_mode ??
        (sessionRow?.current_mode as TeachingMode | null) ??
        null,
    );
  }

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
        await refreshMarkers(s);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError ? err.message : "Could not load live controls",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!session) return;
    const tick = () => {
      const start = new Date(clockStartIso(session)).getTime();
      setElapsed(Math.max(0, (Date.now() - start) / 1000));
    };
    tick();
    const handle = window.setInterval(tick, 1000);
    return () => window.clearInterval(handle);
  }, [session]);

  const activeTopic = useMemo(() => {
    const open = [...topics]
      .filter((t) => t.end_sec == null || t.end_sec >= elapsed)
      .filter((t) => t.start_sec <= elapsed)
      .sort((a, b) => b.start_sec - a.start_sec);
    return open[0] ?? topics[topics.length - 1] ?? null;
  }, [topics, elapsed]);

  async function onAddTopic(e: FormEvent) {
    e.preventDefault();
    const trimmed = label.trim();
    if (!trimmed || savingTopic) return;
    setSavingTopic(true);
    setError(null);
    try {
      await createTopic(id, { label: trimmed, start_sec: elapsed });
      setLabel("");
      const s = await getSession(id);
      setSession(s);
      await refreshMarkers(s);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add topic");
    } finally {
      setSavingTopic(false);
    }
  }

  async function onMode(mode: TeachingMode) {
    if (savingMode || mode === currentMode) return;
    setSavingMode(true);
    setError(null);
    try {
      await setMode(id, { mode, start_sec: elapsed });
      const s = await getSession(id);
      setSession(s);
      await refreshMarkers(s);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not set mode");
    } finally {
      setSavingMode(false);
    }
  }

  if (loading) {
    return <p>Loading live controls…</p>;
  }

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
    <div className="live-page">
      <p style={{ margin: "0 0 0.5rem" }}>
        <Link to={`/sessions/${id}`}>← Session hub</Link>
      </p>

      <header className="live-header">
        <div>
          <h1>Live markers</h1>
          <p>
            Timestamp topics and teaching modes for “{session.title}”. No audio
            required — these markers become timeline context later.
          </p>
        </div>
        <div className="live-clock" aria-live="polite">
          <span className="live-clock-label">Elapsed</span>
          <span className="live-clock-value">{formatElapsed(elapsed)}</span>
        </div>
      </header>

      {error ? <p className="sessions-error">{error}</p> : null}

      <div className="live-status">
        <div>
          <span className="label">Active topic</span>
          <strong>{activeTopic?.label ?? "None yet"}</strong>
        </div>
        <div>
          <span className="label">Current mode</span>
          <strong>{formatModeLabel(currentMode)}</strong>
        </div>
      </div>

      <section className="live-panel">
        <div className="live-panel-title">
          <Flag size={18} strokeWidth={1.75} />
          <h2>New topic</h2>
        </div>
        <form className="topic-form" onSubmit={(e) => void onAddTopic(e)}>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="e.g. Intro to Bayes, Worked example…"
            maxLength={255}
            autoComplete="off"
            disabled={savingTopic}
          />
          <button
            type="submit"
            className="btn-primary topic-submit"
            disabled={savingTopic || !label.trim()}
          >
            {savingTopic ? "Saving…" : "Add topic"}
          </button>
        </form>
      </section>

      <section className="live-panel">
        <div className="live-panel-title">
          <Layers size={18} strokeWidth={1.75} />
          <h2>Teaching mode</h2>
        </div>
        <div className="mode-switcher" role="group" aria-label="Teaching mode">
          {TEACHING_MODES.map((m) => (
            <button
              key={m.value}
              type="button"
              className={`mode-btn${currentMode === m.value ? " active" : ""}`}
              disabled={savingMode}
              onClick={() => void onMode(m.value)}
            >
              <strong>{m.label}</strong>
              <span>{m.hint}</span>
            </button>
          ))}
        </div>
      </section>

      <div className="live-lists">
        <section className="live-panel">
          <h2>Topics ({topics.length})</h2>
          {topics.length === 0 ? (
            <p className="live-empty">No topics yet — add one above.</p>
          ) : (
            <ul className="marker-list">
              {[...topics].reverse().map((t) => (
                <li key={t.id}>
                  <span className="marker-time">
                    {formatElapsed(t.start_sec)}
                    {t.end_sec != null ? ` – ${formatElapsed(t.end_sec)}` : ""}
                  </span>
                  <span className="marker-label">{t.label}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="live-panel">
          <h2>Mode changes ({modes.length})</h2>
          {modes.length === 0 ? (
            <p className="live-empty">No mode changes yet — tap a mode above.</p>
          ) : (
            <ul className="marker-list">
              {[...modes].reverse().map((m) => (
                <li key={m.id}>
                  <span className="marker-time">
                    {formatElapsed(m.start_sec)}
                  </span>
                  <span className="marker-label">{formatModeLabel(m.mode)}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
