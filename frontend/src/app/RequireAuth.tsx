import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { AUTH_CHANGED_EVENT, isAuthenticated } from "../stores/auth";

type Props = {
  children: React.ReactNode;
};

export function RequireAuth({ children }: Props) {
  const location = useLocation();
  const [, setAuthTick] = useState(0);

  useEffect(() => {
    const onAuth = () => setAuthTick((n) => n + 1);
    window.addEventListener(AUTH_CHANGED_EVENT, onAuth);
    return () => window.removeEventListener(AUTH_CHANGED_EVENT, onAuth);
  }, []);

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return children;
}
