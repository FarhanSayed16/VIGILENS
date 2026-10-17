import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { loginRequest } from "../../api/auth";
import { ApiError } from "../../api/client";
import { BrandMark } from "../../components/domain/BrandMark";
import { PageTransition } from "../../components/ui/PageTransition";
import { isAuthenticated, setSession } from "../../stores/auth";
import "./login.css";

export function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("lecturer");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (isAuthenticated()) {
    return <Navigate to="/sessions" replace />;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!username.trim() || !password) {
      setError("Enter username and password.");
      return;
    }
    setLoading(true);
    try {
      const token = await loginRequest(username.trim(), password);
      setSession(token.access_token, token.username);
      navigate("/sessions");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || "Invalid username or password.");
      } else if (err instanceof TypeError) {
        setError("Cannot reach API. Is the backend running on port 8000?");
      } else {
        setError("Sign-in failed.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <PageTransition>
        <div className="login-sheet">
          <BrandMark to={null} />
          <p className="login-lead">
            Lecturer workspace for class-level teaching-target orientation
            trends — not mood or attention scoring.
          </p>
          <form className="login-form" onSubmit={onSubmit}>
            <label>
              Username
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                disabled={loading}
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                placeholder="From .env LECTURER_PASSWORD"
                disabled={loading}
              />
            </label>
            {error ? <p className="login-error">{error}</p> : null}
            <button type="submit" className="login-submit" disabled={loading}>
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <p className="login-foot">
            <Link to="/privacy">Privacy notice</Link>
            {" · "}
            Default: <code>lecturer</code> / <code>change_me</code>
          </p>
        </div>
      </PageTransition>
    </div>
  );
}
