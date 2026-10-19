import { apiDelete, apiGet, apiPost } from "./client";

export type SourceType = "upload" | "webcam" | "phone_rtsp";
export type SessionStatus =
  | "draft"
  | "ready"
  | "analyzing"
  | "live"
  | "complete"
  | "error"
  | "purged_video";

export type LectureSession = {
  id: number;
  title: string;
  room_config_id: number;
  room_name: string | null;
  source_type: SourceType;
  status: SessionStatus;
  source_url: string | null;
  secondary_source_url?: string | null;
  video_path: string | null;
  current_mode: string | null;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  has_video: boolean;
};

export type SessionListResponse = {
  items: LectureSession[];
  total: number;
};

export type SessionCreatePayload = {
  title: string;
  room_config_id: number;
  source_type: SourceType;
  source_url?: string | null;
  started_at?: string | null;
};

export type SessionSummary = {
  session_id: number;
  status: SessionStatus;
  mean_ttoi: number | null;
  mean_coverage: number | null;
  event_count: number;
  window_count: number;
  insufficient_coverage_windows?: number;
  partial_windows?: number;
  candidate_decline_windows?: number;
  duration_sec?: number | null;
  cached?: boolean;
  note: string;
};

export function listSessions(params?: {
  room_config_id?: number;
  status?: string;
}): Promise<SessionListResponse> {
  const q = new URLSearchParams();
  if (params?.room_config_id) q.set("room_config_id", String(params.room_config_id));
  if (params?.status) q.set("status", params.status);
  const qs = q.toString();
  return apiGet<SessionListResponse>(`/sessions${qs ? `?${qs}` : ""}`);
}

export function getSession(id: number): Promise<LectureSession> {
  return apiGet<LectureSession>(`/sessions/${id}`);
}

export function createSession(payload: SessionCreatePayload): Promise<LectureSession> {
  return apiPost<LectureSession>("/sessions", payload);
}

export function deleteSession(id: number): Promise<void> {
  return apiDelete(`/sessions/${id}`);
}

export function getSessionSummary(id: number): Promise<SessionSummary> {
  return apiGet<SessionSummary>(`/sessions/${id}/summary`);
}
