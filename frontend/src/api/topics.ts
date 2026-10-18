import { apiGet, apiPost } from "./client";

export type TeachingMode =
  | "explanation"
  | "note_taking"
  | "qa"
  | "discussion";

export type Topic = {
  id: number;
  session_id: number;
  start_sec: number;
  end_sec: number | null;
  label: string;
};

export type TopicListResponse = {
  items: Topic[];
  total: number;
};

export type ModeChange = {
  id: number;
  session_id: number;
  start_sec: number;
  mode: TeachingMode;
};

export type ModeChangeListResponse = {
  items: ModeChange[];
  total: number;
  current_mode: TeachingMode | null;
};

export const TEACHING_MODES: {
  value: TeachingMode;
  label: string;
  hint: string;
}[] = [
  { value: "explanation", label: "Explanation", hint: "Lecturer presenting" },
  { value: "note_taking", label: "Note-taking", hint: "Students writing" },
  { value: "qa", label: "Q&A", hint: "Questions & answers" },
  { value: "discussion", label: "Discussion", hint: "Class dialogue" },
];

export function listTopics(sessionId: number): Promise<TopicListResponse> {
  return apiGet<TopicListResponse>(`/sessions/${sessionId}/topics`);
}

export function createTopic(
  sessionId: number,
  payload: { label: string; start_sec?: number; end_sec?: number | null },
): Promise<Topic> {
  return apiPost<Topic>(`/sessions/${sessionId}/topics`, payload);
}

export function listModes(sessionId: number): Promise<ModeChangeListResponse> {
  return apiGet<ModeChangeListResponse>(`/sessions/${sessionId}/modes`);
}

export function setMode(
  sessionId: number,
  payload: { mode: TeachingMode; start_sec?: number },
): Promise<ModeChange> {
  return apiPost<ModeChange>(`/sessions/${sessionId}/mode`, payload);
}

export function formatElapsed(totalSec: number): string {
  const s = Math.max(0, Math.floor(totalSec));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) {
    return `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  }
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

export function formatModeLabel(mode: string | null | undefined): string {
  if (!mode) return "—";
  const found = TEACHING_MODES.find((m) => m.value === mode);
  return found?.label ?? mode.replace("_", " ");
}
