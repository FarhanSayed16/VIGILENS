import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../../api/client";
import { submitPulse } from "../../api/pulse";
import { BrandMark } from "../../components/domain/BrandMark";
import { PageTransition } from "../../components/ui/PageTransition";
import "./pulse-public.css";

const SCORES = [1, 2, 3, 4, 5] as const;

export function PulsePublicPage() {
  const { sessionId } = useParams();
  const id = Number(sessionId);

  const [score, setScore] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const invalid = !Number.isFinite(id) || id <= 0;

  async function onSubmit() {
    if (score == null || submitting || invalid) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitPulse(id, score);
      setDone(true);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not submit — check your connection.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="pulse-public-page">
      <PageTransition>
        <div className="pulse-public-sheet">
          <BrandMark to="" />
          <h1>Quick pulse</h1>

          {invalid ? (
            <p className="pulse-public-lead">This pulse link is invalid.</p>
          ) : done ? (
            <>
              <p className="pulse-thanks">Thank you</p>
              <p className="pulse-thanks-sub">
                Your anonymous score was recorded. No name or seat was asked.
              </p>
            </>
          ) : (
            <>
              <p className="pulse-public-lead">
                How clear was this part of class? Tap 1–5. Anonymous — no name,
                seat, or roll number.
              </p>
              {error ? <p className="pulse-public-error">{error}</p> : null}
              <div className="pulse-score-grid" role="group" aria-label="Score 1 to 5">
                {SCORES.map((n) => (
                  <button
                    key={n}
                    type="button"
                    className={`pulse-score-btn${score === n ? " selected" : ""}`}
                    onClick={() => setScore(n)}
                    aria-pressed={score === n}
                  >
                    {n}
                  </button>
                ))}
              </div>
              <button
                type="button"
                className="btn-primary"
                disabled={score == null || submitting}
                onClick={() => void onSubmit()}
              >
                {submitting ? "Sending…" : "Submit"}
              </button>
            </>
          )}

          <p className="pulse-public-foot">
            <Link to="/privacy">Privacy notice</Link>
          </p>
        </div>
      </PageTransition>
    </div>
  );
}
