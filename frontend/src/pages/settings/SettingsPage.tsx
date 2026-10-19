import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { getApiBaseUrl } from "../../api/client";
import { fetchHealth, type HealthInfo } from "../../api/health";
import { clearSession, getUsername } from "../../stores/auth";
import "../sessions/sessions.css";

export function SettingsPage() {
  const navigate = useNavigate();
  const username = getUsername() ?? "lecturer";
  const [health, setHealth] = useState<HealthInfo | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const data = await fetchHealth();
      if (!cancelled) setHealth(data);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  function logout() {
    clearSession();
    navigate("/login");
  }

  return (
    <div className="sessions-page">
      <header className="sessions-header">
        <div>
          <h1>Settings</h1>
          <p>Account and workspace hints for demos (MVP).</p>
        </div>
      </header>

      <section className="sessions-panel" style={{ maxWidth: 520 }}>
        <h2>Account</h2>
        <p>
          Signed in as <strong>{username}</strong> (lecturer).
        </p>
        <p style={{ marginTop: "0.75rem" }}>
          <button type="button" className="ghost-btn" onClick={logout}>
            Log out
          </button>
        </p>
      </section>

      <section className="sessions-panel" style={{ maxWidth: 520, marginTop: "1rem" }}>
        <h2>Workspace</h2>
        <dl className="settings-dl">
          <dt>API</dt>
          <dd>
            <code>{getApiBaseUrl()}</code>
          </dd>
          <dt>API version</dt>
          <dd>{health?.version ?? "—"}</dd>
          <dt>Analysis worker</dt>
          <dd>
            {health == null
              ? "—"
              : health.use_fake_worker
                ? "Synthetic (USE_FAKE_WORKER=true)"
                : "Real vision (YOLO + MediaPipe)"}
          </dd>
          <dt>App package</dt>
          <dd>0.1.0</dd>
        </dl>
        <p style={{ marginTop: "1rem" }}>
          Thresholds live in <code>configs/default.yaml</code> — see{" "}
          <Link to="/app/privacy">Privacy</Link> for retention defaults.
        </p>
      </section>
    </div>
  );
}
