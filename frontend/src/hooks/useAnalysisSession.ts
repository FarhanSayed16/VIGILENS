import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import { fetchHealth } from "../api/health";
import {
  getLatestJob,
  getJob,
  isJobActive,
  recoverAnalysis,
  startAnalysis,
  type AnalysisJob,
} from "../api/jobs";
import {
  getSession,
  getSessionSummary,
  type LectureSession,
  type SessionSummary,
} from "../api/sessions";

export function useAnalysisSession(sessionId: number) {
  const [session, setSession] = useState<LectureSession | null>(null);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [recovering, setRecovering] = useState(false);
  const [fakeWorker, setFakeWorker] = useState<boolean | null>(null);
  const pollRef = useRef<number | null>(null);

  const stopPoll = useCallback(() => {
    if (pollRef.current != null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const refreshSession = useCallback(async () => {
    const [s, sum] = await Promise.all([
      getSession(sessionId),
      getSessionSummary(sessionId),
    ]);
    setSession(s);
    setSummary(sum);
    return s;
  }, [sessionId]);

  const beginPoll = useCallback(
    (jobId: number) => {
      stopPoll();
      const tick = async () => {
        try {
          const j = await getJob(jobId);
          setJob(j);
          if (
            j.status === "done" ||
            j.status === "error" ||
            j.status === "cancelled"
          ) {
            stopPoll();
            await refreshSession();
          }
        } catch (err) {
          setError(err instanceof ApiError ? err.message : "Job poll failed");
          stopPoll();
        }
      };
      void tick();
      pollRef.current = window.setInterval(() => void tick(), 1000);
    },
    [refreshSession, stopPoll],
  );

  useEffect(() => {
    if (!Number.isFinite(sessionId) || sessionId <= 0) {
      setError("Invalid session id");
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const [, health, latest] = await Promise.all([
          refreshSession(),
          fetchHealth(),
          getLatestJob(sessionId),
        ]);
        if (cancelled) return;
        if (health) setFakeWorker(Boolean(health.use_fake_worker));
        if (latest) {
          setJob(latest);
          if (isJobActive(latest)) beginPoll(latest.id);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError ? err.message : "Could not load session",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
      stopPoll();
    };
  }, [sessionId, refreshSession, beginPoll, stopPoll]);

  const stuckOrphan =
    (session?.status === "analyzing" || session?.status === "live") &&
    !isJobActive(job);

  async function onRun(force = false) {
    if (!session || starting) return;
    if (force || isJobActive(job)) {
      if (
        !window.confirm(
          "Start a new analysis? Any unfinished job for this session will be superseded.",
        )
      ) {
        return;
      }
    }
    setStarting(true);
    setError(null);
    try {
      const j = await startAnalysis(sessionId);
      setJob(j);
      await refreshSession();
      beginPoll(j.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start analysis");
    } finally {
      setStarting(false);
    }
  }

  async function onRecover() {
    setRecovering(true);
    setError(null);
    try {
      const res = await recoverAnalysis(sessionId);
      setJob(res.job);
      await refreshSession();
      if (res.job && isJobActive(res.job)) beginPoll(res.job.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Recover failed");
    } finally {
      setRecovering(false);
    }
  }

  return {
    session,
    summary,
    job,
    error,
    loading,
    starting,
    recovering,
    fakeWorker,
    stuckOrphan,
    onRun,
    onRecover,
    setError,
  };
}
