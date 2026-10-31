import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../../api/client";
import {
  getResultsSummary,
  listEvents,
  listWindows,
  type DeclineEvent,
  type WindowPoint,
} from "../../api/results";
import { getSession, type LectureSession, type SessionSummary } from "../../api/sessions";
import {
  formatElapsed,
  formatModeLabel,
  listTopics,
  type Topic,
} from "../../api/topics";
import { setEventFeedback, type EventFeedback } from "../../api/live";
import { SecondaryCueCharts } from "../../components/results/SecondaryCueCharts";
import { TtoiTimelineChart } from "../../components/results/TtoiTimelineChart";
import "../sessions/sessions.css";
import "./results.css";

function seatBand(o: number | null | undefined, usable: boolean): string {
  if (!usable || o == null) return "unobservable";
  if (o >= 70) return "oriented";
  if (o >= 45) return "mixed";
  return "decline";
}

function seatLabel(id: string): string {
  return id;
}

function qualityLabel(note: string | null | undefined, decline: boolean): string {
  if (note === "insufficient_coverage") return "Camera couldn’t measure";
  if (note) return note.replace(/_/g, " ");
  if (decline) return "Possible drop — check timeline";
  return "Good measurement";
}

function cueLabel(cue: string | null | undefined): string {
  if (!cue) return "—";
  const map: Record<string, string> = {
    target_oriented: "Facing the teaching area",
    head_down: "Looking down",
    hand_raise: "Hand raised",
    mixed: "Mixed postures",
  };
  return map[cue] ?? cue.replace(/_/g, " ");
}

function buildSessionStory(
  summary: SessionSummary | null,
  windows: WindowPoint[],
  events: DeclineEvent[],
): { lead: string; detail: string; mostlyLowCoverage: boolean } {
  const total = summary?.window_count ?? windows.length;
  const low = summary?.insufficient_coverage_windows ?? 0;
  const reliable = Math.max(0, total - low);
  const declines = summary?.event_count ?? events.length;
  const ttoi =
    summary?.mean_ttoi != null ? Math.round(summary.mean_ttoi) : null;
  const mostlyLowCoverage = total > 0 && low / total >= 0.5;

  if (mostlyLowCoverage) {
    return {
      lead: `The camera only measured clearly in ${reliable} of ${total} time blocks.`,
      detail:
        ttoi != null
          ? `In those clear blocks, about ${ttoi}% of the class faced the teaching area. Grey on the chart = “couldn’t measure,” not a bad score.`
          : "Grey on the chart means the camera couldn’t see enough people — not a failing grade.",
      mostlyLowCoverage: true,
    };
  }

  return {
    lead:
      ttoi != null
        ? `About ${ttoi}% of the class faced the teaching area (when the camera could measure).`
        : "Review is ready — see how often the class faced the teaching area.",
    detail: `${reliable} of ${total} time blocks were clear · ${declines} longer drop${declines === 1 ? "" : "s"} detected.`,
    mostlyLowCoverage: false,
  };
}

type ViewMode = "chart" | "table";

export function ResultsPage() {
  const { sessionId } = useParams();
  const id = Number(sessionId);

  const [session, setSession] = useState<LectureSession | null>(null);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [windows, setWindows] = useState<WindowPoint[]>([]);
  const [events, setEvents] = useState<DeclineEvent[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<ViewMode>("chart");
  const [showSecondary, setShowSecondary] = useState(true);
  const [minCoverage, setMinCoverage] = useState<number | "">("");
  const [selectedWindowId, setSelectedWindowId] = useState<number | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);

  useEffect(() => {
    if (!Number.isFinite(id) || id <= 0) {
      setError("Invalid session id");
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const [s, sum, t] = await Promise.all([
          getSession(id),
          getResultsSummary(id),
          listTopics(id),
        ]);
        if (cancelled) return;
        setSession(s);
        setSummary(sum);
        setTopics(t.items);

        if (sum.window_count > 0 || s.status === "complete") {
          const [w, e] = await Promise.all([listWindows(id), listEvents(id)]);
          if (cancelled) return;
          setWindows(w.items);
          setEvents(e.items);
          if (w.items.length) setSelectedWindowId(w.items[0].id);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError ? err.message : "Could not load results",
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
    if (!session || loading) return;
    let cancelled = false;
    (async () => {
      try {
        const w = await listWindows(
          id,
          minCoverage === "" ? undefined : { min_coverage_pct: Number(minCoverage) },
        );
        if (!cancelled) {
          setWindows(w.items);
          if (
            selectedWindowId != null &&
            !w.items.some((x) => x.id === selectedWindowId)
          ) {
            setSelectedWindowId(w.items[0]?.id ?? null);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError ? err.message : "Could not filter windows",
          );
        }
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [minCoverage, id]);

  const topicById = useMemo(() => {
    const m = new Map<number, Topic>();
    for (const t of topics) m.set(t.id, t);
    return m;
  }, [topics]);

  const selectedWindow = windows.find((w) => w.id === selectedWindowId) ?? null;
  const selectedEvent = events.find((e) => e.id === selectedEventId) ?? null;

  const hasResults = windows.length > 0 || (summary?.window_count ?? 0) > 0;

  const story = useMemo(
    () => buildSessionStory(summary, windows, events),
    [summary, windows, events],
  );

  const totalWindows = summary?.window_count ?? windows.length;
  const lowWindows = summary?.insufficient_coverage_windows ?? 0;
  const reliableWindows = Math.max(0, totalWindows - lowWindows);
  const declines = summary?.event_count ?? events.length;

  if (loading) return <p>Loading results…</p>;

  if (error && !session) {
    return (
      <div>
        <p className="sessions-error">{error}</p>
        <Link to="/sessions">← Back to sessions</Link>
      </div>
    );
  }

  if (!session) return null;

  if (!hasResults) {
    return (
      <div className="results-page">
        <p className="results-back">
          <Link to={`/sessions/${id}`}>← Console</Link>
        </p>
        <div className="empty-results">
          <h2>No review data yet</h2>
          <p>
            Run a live lecture or batch analysis from the Console to see class
            orientation over time, how often the camera could measure, and any
            sustained orientation declines.
          </p>
          <Link className="btn-primary" to={`/sessions/${id}`}>
            Open console
          </Link>
        </div>
        <div className="results-disclaimer">
          Class-level observable orientation — not attention scores, not emotion
          labels, and not student rankings.
        </div>
      </div>
    );
  }

  return (
    <div className="results-page">
      <p className="results-back">
        <Link to={`/sessions/${id}`}>← Console</Link>
      </p>

      <header className="results-header">
        <div>
          <p className="page-kicker">Lecture review</p>
          <h1 className="results-title">{session.title}</h1>
        </div>
        <div className="results-header-actions">
          <span className={`status-pill ${session.status}`}>
            {session.status.replace("_", " ")}
          </span>
          <Link className="btn-secondary" to={`/sessions/${id}`}>
            Re-run from console
          </Link>
        </div>
      </header>

      {error ? <p className="sessions-error">{error}</p> : null}

      <section
        className={`review-story${story.mostlyLowCoverage ? " warn" : ""}`}
        aria-label="Session summary"
      >
        <p className="review-story-kicker">In plain words</p>
        <p className="review-story-lead">{story.lead}</p>
        <p className="review-story-detail">{story.detail}</p>
      </section>

      <ol className="review-guide" aria-label="How to read this page">
        <li>
          <strong>1. Big number</strong>
          <span>How often the class faced the front when we could see them.</span>
        </li>
        <li>
          <strong>2. Chart</strong>
          <span>Teal = measured. Grey = camera couldn’t see enough.</span>
        </li>
        <li>
          <strong>3. Click a block</strong>
          <span>See that half-minute and who was facing the front.</span>
        </li>
      </ol>

      <section className="review-kpi-block" aria-label="Key measures">
        <div className="review-kpi-hero">
          <span className="label">Faced the teaching area</span>
          <span className="value">
            {summary?.mean_ttoi != null
              ? `${Math.round(summary.mean_ttoi)}%`
              : "—"}
          </span>
          <span className="hint">
            Average for clear time blocks only. This is not attention, grades, or
            who was “good.”
          </span>
        </div>
        <div className="review-kpi-evidence">
          <div className="evidence-chip">
            <span className="label">Session length</span>
            <span className="value">
              {summary?.duration_sec != null
                ? formatElapsed(summary.duration_sec)
                : "—"}
            </span>
          </div>
          <div className="evidence-chip">
            <span className="label">Clear time blocks</span>
            <span className="value">
              {reliableWindows}
              <span className="muted"> of {totalWindows}</span>
            </span>
          </div>
          <div className="evidence-chip">
            <span className="label">Camera could measure</span>
            <span className="value">
              {summary?.mean_coverage != null
                ? `${Math.round(summary.mean_coverage)}%`
                : "—"}
            </span>
            <span className="chip-hint">of the session overall</span>
          </div>
          <div className="evidence-chip">
            <span className="label">Longer drops</span>
            <span className="value">{declines}</span>
            <span className="chip-hint">sustained class-level dips</span>
          </div>
        </div>
      </section>

      <div className="results-toolbar">
        <div className="toolbar-filters">
          <label>
            Hide fuzzy blocks below
            <input
              type="number"
              min={0}
              max={100}
              placeholder="off"
              value={minCoverage}
              onChange={(e) => {
                const v = e.target.value;
                setMinCoverage(v === "" ? "" : Number(v));
              }}
            />
            <span className="toolbar-unit">% measure</span>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showSecondary}
              onChange={(e) => setShowSecondary(e.target.checked)}
            />
            Show looking-down &amp; hand-raises
          </label>
        </div>
        <div className="view-toggle" role="group" aria-label="View mode">
          <button
            type="button"
            className={view === "chart" ? "active" : undefined}
            onClick={() => setView("chart")}
          >
            Chart
          </button>
          <button
            type="button"
            className={view === "table" ? "active" : undefined}
            onClick={() => setView("table")}
          >
            Table
          </button>
        </div>
      </div>

      <div className="results-layout">
        <div className="results-main">
          {view === "chart" ? (
            <>
              <div className="chart-card">
                <h2>Facing the front over time</h2>
                <p className="chart-sub">
                  Click any teal segment to open that half-minute on the right.
                </p>
                <div className="chart-legend compact">
                  <span>
                    <i className="swatch ttoi" /> Faced the front
                  </span>
                  <span>
                    <i className="swatch hatch" /> Couldn’t measure
                  </span>
                  <span>
                    <i className="swatch decline" /> Longer drop
                  </span>
                  <span>
                    <i className="swatch topic" /> Topic start
                  </span>
                </div>
                <TtoiTimelineChart
                  windows={windows}
                  events={events}
                  topics={topics}
                  selectedWindowId={selectedWindowId}
                  onSelectWindow={(wid) => {
                    setSelectedWindowId(wid);
                    setSelectedEventId(null);
                  }}
                />
                {topics.length > 0 ? (
                  <div className="topic-strip" aria-label="Topics">
                    {topics.map((t, i) => {
                      const end =
                        t.end_sec ??
                        topics[i + 1]?.start_sec ??
                        summary?.duration_sec ??
                        windows[windows.length - 1]?.end_sec ??
                        t.start_sec + 60;
                      const dur = Math.max(1, end - t.start_sec);
                      const total = Math.max(
                        1,
                        summary?.duration_sec ??
                          windows[windows.length - 1]?.end_sec ??
                          1,
                      );
                      return (
                        <div
                          key={t.id}
                          className="topic-strip-seg"
                          style={{ flexGrow: dur / total, flexBasis: 0 }}
                          title={`${t.label} · ${formatElapsed(t.start_sec)}`}
                        >
                          <span>{t.label}</span>
                        </div>
                      );
                    })}
                  </div>
                ) : null}
              </div>
              {showSecondary ? <SecondaryCueCharts windows={windows} /> : null}
            </>
          ) : (
            <div className="results-table-wrap">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Faced front</th>
                    <th>Clear</th>
                    <th>Mode</th>
                    <th>Topic</th>
                    <th>Measurement</th>
                  </tr>
                </thead>
                <tbody>
                  {windows.map((w) => (
                    <tr
                      key={w.id}
                      className={`${w.id === selectedWindowId ? "selected" : ""}${
                        w.candidate_decline ? " decline" : ""
                      }`}
                      tabIndex={0}
                      role="button"
                      aria-pressed={w.id === selectedWindowId}
                      onClick={() => {
                        setSelectedWindowId(w.id);
                        setSelectedEventId(null);
                      }}
                      onKeyDown={(ev) => {
                        if (ev.key === "Enter" || ev.key === " ") {
                          ev.preventDefault();
                          setSelectedWindowId(w.id);
                          setSelectedEventId(null);
                        }
                      }}
                    >
                      <td>
                        {formatElapsed(w.start_sec)}–{formatElapsed(w.end_sec)}
                      </td>
                      <td>{w.ttoi != null ? `${w.ttoi.toFixed(0)}%` : "—"}</td>
                      <td>
                        {w.coverage_pct != null
                          ? `${w.coverage_pct.toFixed(0)}%`
                          : "—"}
                      </td>
                      <td>{formatModeLabel(w.teaching_mode)}</td>
                      <td>
                        {w.topic_id != null
                          ? topicById.get(w.topic_id)?.label ?? `#${w.topic_id}`
                          : "—"}
                      </td>
                      <td>
                        {w.data_quality_note || w.candidate_decline ? (
                          <span className="quality-pill warn">
                            {qualityLabel(
                              w.data_quality_note,
                              !!w.candidate_decline,
                            )}
                          </span>
                        ) : (
                          <span className="quality-pill ok">Clear</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className={`chart-card declines-card${events.length === 0 ? " empty" : ""}`}>
            <h2>Longer drops in facing the front</h2>
            <p className="chart-sub">
              Spans where the whole class dipped for a while — moments worth a
              quick look. Not boredom scores or individual grades.
            </p>
            {events.length === 0 ? (
              <p className="declines-empty">
                No longer drops in this run. Longer sessions with a clear camera
                view make these easier to spot.
              </p>
            ) : (
              <div className="results-table-wrap nested">
                <table className="results-table events-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Duration</th>
                      <th>Depth</th>
                      <th>Coverage</th>
                      <th>Topic</th>
                      <th>Mode</th>
                    </tr>
                  </thead>
                  <tbody>
                    {events.map((e) => {
                      const dur = Math.max(0, e.end_sec - e.start_sec);
                      return (
                        <tr
                          key={e.id}
                          className={
                            e.id === selectedEventId ? "selected decline" : "decline"
                          }
                          tabIndex={0}
                          role="button"
                          aria-pressed={e.id === selectedEventId}
                          onClick={() => {
                            setSelectedEventId(e.id);
                            setSelectedWindowId(null);
                          }}
                          onKeyDown={(ev) => {
                            if (ev.key === "Enter" || ev.key === " ") {
                              ev.preventDefault();
                              setSelectedEventId(e.id);
                              setSelectedWindowId(null);
                            }
                          }}
                        >
                          <td>
                            {formatElapsed(e.start_sec)}–
                            {formatElapsed(e.end_sec)}
                          </td>
                          <td>{formatElapsed(dur)}</td>
                          <td>{e.depth.toFixed(1)}</td>
                          <td>
                            {e.coverage_pct != null
                              ? `${e.coverage_pct.toFixed(0)}%`
                              : "—"}
                          </td>
                          <td>
                            {e.topic_id != null
                              ? topicById.get(e.topic_id)?.label ??
                                `#${e.topic_id}`
                              : "—"}
                          </td>
                          <td>{formatModeLabel(e.teaching_mode)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        <aside className="window-panel" aria-live="polite">
          <h2>Selected half-minute</h2>
          {selectedEvent && !selectedWindow ? (
            <>
              <p className="window-panel-kicker">Longer drop</p>
              <dl className="window-dl">
                <div>
                  <dt>What happened</dt>
                  <dd>
                    {(selectedEvent.kind ?? "orientation_decline") ===
                    "orientation_decline"
                      ? "Class facing dipped"
                      : (selectedEvent.kind ?? "").replace(/_/g, " ")}
                  </dd>
                </div>
                <div>
                  <dt>When</dt>
                  <dd>
                    {formatElapsed(selectedEvent.start_sec)}–
                    {formatElapsed(selectedEvent.end_sec)}
                  </dd>
                </div>
                <div>
                  <dt>How sharp</dt>
                  <dd>{selectedEvent.depth.toFixed(1)} points below recent</dd>
                </div>
                <div>
                  <dt>Camera clear</dt>
                  <dd>
                    {selectedEvent.coverage_pct != null
                      ? `${selectedEvent.coverage_pct.toFixed(0)}%`
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt>Group</dt>
                  <dd>{selectedEvent.group_label ?? "—"}</dd>
                </div>
                <div>
                  <dt>Seats</dt>
                  <dd>
                    {selectedEvent.seat_ids_json?.length
                      ? selectedEvent.seat_ids_json.map(seatLabel).join(", ")
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt>Note</dt>
                  <dd>{selectedEvent.note ?? "—"}</dd>
                </div>
                <div>
                  <dt>Your mark</dt>
                  <dd>{selectedEvent.lecturer_feedback ?? "—"}</dd>
                </div>
              </dl>
              <div className="feedback-row">
                {(
                  [
                    ["useful", "Useful"],
                    ["false_alarm", "False alarm"],
                    ["insufficient", "Insufficient"],
                  ] as [EventFeedback, string][]
                ).map(([val, label]) => (
                  <button
                    key={val}
                    type="button"
                    className="btn-secondary"
                    onClick={() => {
                      void setEventFeedback(id, selectedEvent.id, val).then(
                        (res) => {
                          setEvents((prev) =>
                            prev.map((e) =>
                              e.id === selectedEvent.id
                                ? {
                                    ...e,
                                    lecturer_feedback: res.lecturer_feedback,
                                  }
                                : e,
                            ),
                          );
                        },
                      );
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </>
          ) : selectedWindow ? (
            <>
              <p className="window-panel-kicker">
                {formatElapsed(selectedWindow.start_sec)}–
                {formatElapsed(selectedWindow.end_sec)}
              </p>
              <dl className="window-dl">
                <div>
                  <dt>Faced the front</dt>
                  <dd>
                    {selectedWindow.ttoi != null
                      ? `${selectedWindow.ttoi.toFixed(0)}%`
                      : "—"}
                    {selectedWindow.ttoi_lo != null &&
                    selectedWindow.ttoi_hi != null
                      ? ` (range ${selectedWindow.ttoi_lo.toFixed(0)}–${selectedWindow.ttoi_hi.toFixed(0)})`
                      : ""}
                  </dd>
                </div>
                <div>
                  <dt>People measured</dt>
                  <dd>
                    {selectedWindow.usable_regions != null &&
                    selectedWindow.expected_regions != null
                      ? `${selectedWindow.usable_regions} of ${selectedWindow.expected_regions} seats`
                      : "—"}
                    {selectedWindow.coverage_pct != null
                      ? ` · ${selectedWindow.coverage_pct.toFixed(0)}% clear`
                      : ""}
                  </dd>
                </div>
                <div>
                  <dt>Teaching mode</dt>
                  <dd>{formatModeLabel(selectedWindow.teaching_mode)}</dd>
                </div>
                <div>
                  <dt>Topic</dt>
                  <dd>
                    {selectedWindow.topic_id != null
                      ? topicById.get(selectedWindow.topic_id)?.label ??
                        `#${selectedWindow.topic_id}`
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt>What we mostly saw</dt>
                  <dd>{cueLabel(selectedWindow.dominant_cue)}</dd>
                </div>
                <div>
                  <dt>Measurement</dt>
                  <dd>
                    {qualityLabel(
                      selectedWindow.data_quality_note,
                      !!selectedWindow.candidate_decline,
                    )}
                  </dd>
                </div>
              </dl>

              {selectedWindow.seat_stats_json &&
              selectedWindow.seat_stats_json.length > 0 ? (
                <div className="window-seats">
                  <h3>Who faced the front</h3>
                  <p className="window-seats-sub">
                    Anonymous faces registered this session. A tile exists only
                    because a face was seen — not a pre-drawn chair.
                  </p>
                  <ul className="review-heat">
                    {selectedWindow.seat_stats_json.map((s) => (
                      <li
                        key={s.seat_id}
                        className={`seat-tile ${seatBand(s.orientation_pct, s.usable)}`}
                      >
                        <span className="seat-id">{seatLabel(s.seat_id)}</span>
                        <span className="seat-o">
                          {s.orientation_pct != null
                            ? Math.round(s.orientation_pct)
                            : "—"}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="detail-empty">No per-seat stats for this window.</p>
              )}
            </>
          ) : (
            <p className="detail-empty">
              Click a teal block on the chart (or a drop in the list) to see that
              half-minute here.
            </p>
          )}
        </aside>
      </div>

      <div className="results-disclaimer">
        Class-level “faced the front” only — not attention, emotion, or student
        rankings. Grey / low measure = weak camera evidence, not a grade. No face
        crops are stored.
      </div>
    </div>
  );
}
