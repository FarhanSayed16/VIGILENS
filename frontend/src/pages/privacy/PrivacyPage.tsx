import { Link } from "react-router-dom";
import { BrandMark } from "../../components/domain/BrandMark";
import { PageTransition } from "../../components/ui/PageTransition";

type Props = {
  publicLayout?: boolean;
};

export function PrivacyPage({ publicLayout = false }: Props) {
  const body = (
    <div className="page-stub">
      {!publicLayout ? <h1>Privacy</h1> : null}
      {publicLayout ? (
        <div style={{ marginBottom: "1.5rem" }}>
          <BrandMark to="/login" />
        </div>
      ) : null}
      {publicLayout ? <h1>Privacy notice</h1> : null}
      <p>
        VIGILENS processes consented classroom video locally to produce
        class-level teaching-target orientation (TTOI) timelines.
      </p>
      <ul>
        <li>No face recognition or student identity matching</li>
        <li>No grading, attendance penalties, or discipline rankings</li>
        <li>Raw video purged after analysis by default</li>
        <li>Aggregates only — no permanent per-student histories</li>
        <li>Institutional and student consents already obtained for this project</li>
      </ul>
      <p>
        This is a teaching-reflection tool, not a surveillance or emotion AI
        product. Sample or public clips may be used for demos when classroom
        video is unavailable.
      </p>
      <p>
        Contact (project): your course supervisor / institutional research
        office — replace this placeholder before public deployment.
      </p>
      {publicLayout ? (
        <p>
          <Link to="/login">← Back to login</Link>
        </p>
      ) : null}
    </div>
  );

  if (publicLayout) {
    return (
      <div className="login-page">
        <PageTransition>
          <div className="login-sheet" style={{ width: "min(560px, 100%)" }}>
            {body}
          </div>
        </PageTransition>
      </div>
    );
  }

  return body;
}
