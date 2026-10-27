import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import {
  getLiveState,
  startLive,
  stopLive,
  type LiveState,
} from "../api/live";
import { getSession, type LectureSession } from "../api/sessions";

export function useLiveSession(sessionId: number) {
  const [session, setSession] = useState<LectureSession | null>(null);
  const [live, setLive] = useState<LiveState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const pollRef = useRef<number | null>(null);

  const stopPoll = useCallback(() => {
    if (pollRef.current != null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const refresh = useCallback(async () => {
    const [s, st] = await Promise.all([
      getSession(sessionId),
      getLiveState(sessionId),
    ]);
    setSession(s);
    setLive(st);
    return { s, st };
  }, [sessionId]);

  const beginPoll = useCallback(() => {
    stopPoll();
    const tick = async () => {
      try {
        const st = await getLiveState(sessionId);
        setLive(st);
        if (!st.running && st.status !== "live") {
          stopPoll();
          const s = await getSession(sessionId);
          setSession(s);
        }
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Live poll failed");
      }
    };
    void tick();
    pollRef.current = window.setInterval(() => void tick(), 1000);
  }, [sessionId, stopPoll]);

  useEffect(() => {
    if (!Number.isFinite(sessionId) || sessionId <= 0) {
      setError("Invalid session id");
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const { st } = await refresh();
        if (!cancelled && (st.running || st.status === "live")) {
          beginPoll();
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
  }, [sessionId, refresh, beginPoll, stopPoll]);

  async function onStart(opts?: { browserCamera?: boolean }) {
    setStarting(true);
    setError(null);
    try {
      // Laptop webcam: wait so Windows releases the browser camera before OpenCV.
      // Phone camera: keep the stream and send frames; do not release it.
      if (!opts?.browserCamera) {
        await new Promise((r) => window.setTimeout(r, 900));
      }
      const st = await startLive(sessionId, opts);
      setLive(st);
      const s = await getSession(sessionId);
      setSession(s);
      beginPoll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start lecture");
    } finally {
      setStarting(false);
    }
  }

  async function onStop() {
    setStopping(true);
    setError(null);
    try {
      const st = await stopLive(sessionId);
      setLive(st);
      const s = await getSession(sessionId);
      setSession(s);
      stopPoll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not stop lecture");
    } finally {
      setStopping(false);
    }
  }

  return {
    session,
    live,
    error,
    loading,
    starting,
    stopping,
    onStart,
    onStop,
    setError,
    refresh,
  };
}
