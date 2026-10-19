import { FormEvent, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import {
  AlertCircle,
  Aperture,
  Eye,
  EyeOff,
  Lock,
  ShieldCheck,
  User,
} from "lucide-react";
import { loginRequest } from "../../api/auth";
import { ApiError } from "../../api/client";
import { PageTransition } from "../../components/ui/PageTransition";
import { isAuthenticated, setSession } from "../../stores/auth";
import "./login.css";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const from =
    (location.state as { from?: string } | null)?.from || "/sessions";
  const [username, setUsername] = useState("lecturer");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (isAuthenticated()) {
    return <Navigate to={from} replace />;
  }

  function handleAutoFill() {
    setUsername("lecturer");
    setPassword("change_me");
    setError(null);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!username.trim() || !password) {
      setError("Please enter your username and password.");
      return;
    }
    setLoading(true);
    try {
      const token = await loginRequest(username.trim(), password);
      setSession(token.access_token, token.username);
      navigate(from, { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || "Invalid username or password.");
      } else if (err instanceof TypeError) {
        setError("Unable to reach server. Please ensure the backend is running.");
      } else {
        setError("Authentication failed. Please verify your credentials.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <PageTransition>
        <div className="login-card">
          {/* Brand & Heading */}
          <div className="login-header">
            <div className="login-brand">
              <span className="login-brand-icon" aria-hidden="true">
                <Aperture size={20} strokeWidth={2} />
              </span>
              <div>
                <h1 className="login-brand-name">VIGILENS</h1>
                <p className="login-brand-tag">A Clearer Lens on Learning</p>
              </div>
            </div>
            <p className="login-description">
              Lecturer workspace for class-level teaching-target orientation
              trends — not mood or attention scoring.
            </p>
          </div>

          {/* Login Form */}
          <form className="login-form" onSubmit={onSubmit}>
            <div className="form-field">
              <label htmlFor="login-username">Username</label>
              <div className="input-container">
                <User size={16} className="input-icon" aria-hidden="true" />
                <input
                  id="login-username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  placeholder="lecturer"
                  disabled={loading}
                  required
                />
              </div>
            </div>

            <div className="form-field">
              <div className="field-header">
                <label htmlFor="login-password">Password</label>
              </div>
              <div className="input-container">
                <Lock size={16} className="input-icon" aria-hidden="true" />
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  placeholder="Enter password"
                  disabled={loading}
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Subtle credential hint */}
            <div className="login-helper">
              <span className="helper-text">
                Default: <code>lecturer</code> / <code>change_me</code>
              </span>
              <button
                type="button"
                className="autofill-btn"
                onClick={handleAutoFill}
              >
                Auto-fill
              </button>
            </div>

            {error && (
              <div className="login-error-alert" role="alert">
                <AlertCircle size={15} className="error-alert-icon" />
                <span>{error}</span>
              </div>
            )}

            <button type="submit" className="login-submit" disabled={loading}>
              {loading ? (
                <span className="submit-loading">
                  <span className="submit-spinner" />
                  Signing in…
                </span>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          {/* Privacy Footnote */}
          <div className="login-footer">
            <div className="privacy-note">
              <ShieldCheck size={14} className="privacy-icon" />
              <span>
                Zero biometric storage ·{" "}
                <Link to="/privacy" className="privacy-link">
                  Privacy notice
                </Link>
              </span>
            </div>
          </div>
        </div>
      </PageTransition>
    </div>
  );
}
