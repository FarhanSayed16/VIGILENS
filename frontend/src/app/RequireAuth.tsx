import { Navigate, useLocation } from "react-router-dom";
import { isAuthenticated } from "../stores/auth";

type Props = {
  children: React.ReactNode;
};

export function RequireAuth({ children }: Props) {
  const location = useLocation();
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return children;
}
