import { useParams } from "react-router-dom";
import { BrandMark } from "../../components/domain/BrandMark";
import { PageTransition } from "../../components/ui/PageTransition";

export function PulsePublicPage() {
  const { sessionId } = useParams();

  return (
    <div className="login-page">
      <PageTransition>
        <div className="login-sheet">
          <BrandMark to="" />
          <h1 style={{ fontSize: "1.25rem", marginTop: "1rem" }}>
            Anonymous pulse
          </h1>
          <p className="login-lead">
            Session <strong>{sessionId}</strong> — rate 1–5. No name, seat, or
            roll number. Full submit UI arrives in Phase 14.
          </p>
          <span className="stub-badge">Public route · Phase 14</span>
        </div>
      </PageTransition>
    </div>
  );
}
