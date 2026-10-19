import { Component, type ErrorInfo, type ReactNode } from "react";
import { Link } from "react-router-dom";

type Props = { children: ReactNode };
type State = { error: Error | null };

/** Catches render errors so Results/charts cannot blank the whole shell. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("VIGILENS UI error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: "2rem", maxWidth: 480, margin: "4rem auto" }}>
          <h1 style={{ fontSize: "1.25rem", marginBottom: "0.5rem" }}>
            Something went wrong
          </h1>
          <p style={{ color: "var(--text-muted, #5a6b7d)", marginBottom: "1rem" }}>
            {this.state.error.message || "Unexpected UI error."} Try reloading, or
            return to sessions.
          </p>
          <p style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <button
              type="button"
              className="btn-primary"
              onClick={() => this.setState({ error: null })}
            >
              Try again
            </button>
            <Link className="btn-secondary" to="/sessions">
              Sessions
            </Link>
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}
