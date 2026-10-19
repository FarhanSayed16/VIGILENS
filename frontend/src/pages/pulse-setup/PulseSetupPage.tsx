import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { ApiError } from "../../api/client";
import { pulsePublicUrl } from "../../api/pulse";
import { getSession, type LectureSession } from "../../api/sessions";
import "../sessions/sessions.css";
import "./pulse-setup.css";

export function PulseSetupPage() {
  const { sessionId } = useParams();
  const id = Number(sessionId);

  const [session, setSession] = useState<LectureSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);

  const url = useMemo(
    () => (Number.isFinite(id) && id > 0 ? pulsePublicUrl(id) : ""),
    [id],
  );

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
        if (!cancelled) setSession(s);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError ? err.message : "Could not load session",
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

  async function onCopy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Could not copy — select the link manually.");
    }
  }

  if (loading) return <p>Loading pulse setup…</p>;

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
    <div className="pulse-setup-page">
      <p style={{ margin: "0 0 0.5rem" }}>
        <Link to={`/sessions/${id}`}>← Session hub</Link>
      </p>
      <h1>Pulse QR</h1>
      <p className="pulse-setup-lead">
        Students open this link on their phones — anonymous 1–5 only. No name,
        seat, or roll number. For “{session.title}”.
      </p>

      {error ? <p className="sessions-error">{error}</p> : null}
      {copied ? <p className="pulse-setup-ok">Link copied.</p> : null}

      <div className="pulse-setup-grid">
        <div className="pulse-qr" aria-label="Pulse QR code">
          <QRCodeSVG value={url} size={200} level="M" includeMargin />
        </div>
        <div className="pulse-setup-copy">
          <h2>Class link</h2>
          <p>Project the QR or share the URL. Responses stamp the active topic server-side.</p>
          <div className="pulse-link-row">
            <input type="text" readOnly value={url} aria-label="Pulse URL" />
            <button type="button" className="btn-secondary" onClick={() => void onCopy()}>
              Copy
            </button>
            <a
              className="btn-primary"
              href={url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Open
            </a>
          </div>
          <ol className="pulse-instructions">
            <li>Scan or open the link on a phone</li>
            <li>Tap a score from 1 to 5</li>
            <li>Submit — thank-you screen, no login</li>
          </ol>
        </div>
      </div>

      <div className="privacy-strip">
        Pulse stores only the score, timestamp, and optional topic id. See{" "}
        <Link to="/app/privacy">Privacy</Link>.
      </div>
    </div>
  );
}
