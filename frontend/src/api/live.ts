import { apiGet, apiPost, apiPut, getApiBaseUrl } from "./client";
import { getAccessToken } from "../stores/auth";

export type LiveSeatStat = {
  seat_id: string;
  orientation_pct: number | null;
  usable: boolean;
};

export type LiveGroup = {
  label: string;
  seat_ids: string[];
  orientation_pct: number | null;
  kind: "decline_cluster" | "interaction" | string;
};

export type LiveAlert = {
  kind: string;
  start_sec: number;
  end_sec?: number | null;
  message?: string | null;
  group_label?: string | null;
  seat_ids?: string[];
};

export type LiveState = {
  session_id: number;
  status: string;
  running: boolean;
  job_id: number | null;
  elapsed_sec: number;
  window_seconds?: number;
  next_window_in_sec?: number | null;
  ttoi: number | null;
  coverage_pct: number | null;
  usable_seats: number | null;
  expected_seats: number | null;
  persons_detected?: number | null;
  persons_in_seats?: number | null;
  per_seat: LiveSeatStat[];
  groups: LiveGroup[];
  alerts: LiveAlert[];
  updated_at: string | null;
  secondary_source_url?: string | null;
  message?: string | null;
  detection_hint?: string | null;
  preview_available?: boolean;
};

export function startLive(sessionId: number): Promise<LiveState> {
  return apiPost<LiveState>(`/sessions/${sessionId}/live/start`);
}

export function stopLive(sessionId: number): Promise<LiveState> {
  return apiPost<LiveState>(`/sessions/${sessionId}/live/stop`);
}

export function getLiveState(sessionId: number): Promise<LiveState> {
  return apiGet<LiveState>(`/sessions/${sessionId}/live/state`);
}

export type EventFeedback = "useful" | "false_alarm" | "insufficient";

export function setEventFeedback(
  sessionId: number,
  eventId: number,
  feedback: EventFeedback,
): Promise<{ id: number; lecturer_feedback: string }> {
  return apiPost(
    `/sessions/${sessionId}/live/events/${eventId}/feedback`,
    { feedback },
  );
}

export function setSecondarySource(
  sessionId: number,
  secondary_source_url: string | null,
): Promise<LiveState> {
  return apiPut<LiveState>(`/sessions/${sessionId}/live/secondary`, {
    secondary_source_url,
  });
}

/** Fetch latest worker JPEG (auth header). Caller should revokeObjectURL. */
export async function fetchLivePreviewBlob(
  sessionId: number,
): Promise<Blob | null> {
  const token = getAccessToken();
  const res = await fetch(
    `${getApiBaseUrl()}/sessions/${sessionId}/live/preview.jpg?t=${Date.now()}`,
    {
      headers: {
        Accept: "image/jpeg",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      cache: "no-store",
    },
  );
  if (res.status === 204 || res.status === 404) return null;
  if (!res.ok) return null;
  return res.blob();
}
