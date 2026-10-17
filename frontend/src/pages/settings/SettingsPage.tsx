import { useNavigate } from "react-router-dom";
import { clearSession, getUsername } from "../../stores/auth";

export function SettingsPage() {
  const navigate = useNavigate();
  const username = getUsername() ?? "lecturer";

  function logout() {
    clearSession();
    navigate("/login");
  }

  return (
    <div className="page-stub">
      <h1>Settings</h1>
      <p>
        Signed in as <strong>{username}</strong>. JWT auth is active (Phase 6).
      </p>
      <p style={{ marginTop: "1rem" }}>
        <button type="button" className="ghost-btn" onClick={logout}>
          Log out
        </button>
      </p>
    </div>
  );
}
