import { apiGet } from "./client";
import type { SessionSummary } from "./sessions";
import { getSessionSummary } from "./sessions";

export type WindowPoint = {
  id: number;
  session_id: number;
  start_sec: number;
  end_sec: number;
  topic_id: number | null;
  teaching_mode: string | null;
  expected_regions: number | null;
  usable_regions: number | null;
  coverage_pct: number | null;
  ttoi: number | null;
  ttoi_lo: number | null;
  ttoi_hi: number | null;
  head_down_cue_pct: number | null;
  hand_raise_events: number | null;
  candidate_decline: boolean;
  dominant_cue: string | null;
  data_quality_note: string | null;
};

export type WindowListResponse = {
  session_id: number;
  items: WindowPoint[];
  total: number;
  cached: boolean;
};

export type DeclineEvent = {
  id: number;
  session_id: number;
  start_sec: number;
  end_sec: number;
  depth: number;
  coverage_pct: number | null;
  topic_id: number | null;
  teaching_mode: string | null;
  dominant_cue: string | null;
  note: string | null;
};

export type EventListResponse = {
  session_id: number;
  items: DeclineEvent[];
  total: number;
};

export function listWindows(
  sessionId: number,
  params?: { min_coverage_pct?: number },
): Promise<WindowListResponse> {
  const q = new URLSearchParams();
  if (params?.min_coverage_pct != null) {
    q.set("min_coverage_pct", String(params.min_coverage_pct));
  }
  const qs = q.toString();
  return apiGet<WindowListResponse>(
    `/sessions/${sessionId}/windows${qs ? `?${qs}` : ""}`,
  );
}

export function listEvents(sessionId: number): Promise<EventListResponse> {
  return apiGet<EventListResponse>(`/sessions/${sessionId}/events`);
}

export function getResultsSummary(sessionId: number): Promise<SessionSummary> {
  return getSessionSummary(sessionId);
}
