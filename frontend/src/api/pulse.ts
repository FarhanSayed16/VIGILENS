import { apiPost } from "./client";

export type PulseAccepted = {
  status: string;
  session_id: number;
  score_1_to_5: number;
  topic_id: number | null;
  created_at: string;
  message: string;
};

/** Public — no JWT. Body must be score only (extra fields rejected by API). */
export function submitPulse(
  sessionId: number,
  score_1_to_5: number,
): Promise<PulseAccepted> {
  return apiPost<PulseAccepted>(
    `/pulse/${sessionId}`,
    { score_1_to_5 },
    false,
  );
}

export function pulsePublicUrl(sessionId: number): string {
  const origin = window.location.origin;
  return `${origin}/pulse/${sessionId}`;
}
