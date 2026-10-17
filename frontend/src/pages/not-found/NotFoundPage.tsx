import { Link } from "react-router-dom";
import { PageTransition } from "../../components/ui/PageTransition";

export function NotFoundPage() {
  return (
    <div className="login-page">
      <PageTransition>
        <div className="login-sheet">
          <h1>Page not found</h1>
          <p className="login-lead">
            That route is not part of the VIGILENS lecturer workspace.
          </p>
          <Link to="/sessions">Go to sessions</Link>
        </div>
      </PageTransition>
    </div>
  );
}
