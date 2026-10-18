import { apiPut, apiRequest, apiUploadFile, type UploadProgress } from "./client";
import type { LectureSession, SourceType } from "./sessions";

export type UploadResult = {
  session_id: number;
  filename: string;
  size_bytes: number;
  content_type: string | null;
  has_video: boolean;
  status: string;
  relative_path: string;
};

export type SourceUpdatePayload = {
  source_type: SourceType;
  source_url?: string | null;
  webcam_index?: number | null;
};

/** Default max from backend; UI also reads VITE_MAX_UPLOAD_MB if set. */
export const DEFAULT_MAX_UPLOAD_MB = Number(
  import.meta.env.VITE_MAX_UPLOAD_MB ?? 2048,
);

export function uploadSessionVideo(
  sessionId: number,
  file: File,
  onProgress?: (p: UploadProgress) => void,
): Promise<UploadResult> {
  return apiUploadFile<UploadResult>(`/sessions/${sessionId}/upload`, file, {
    onProgress,
  });
}

export function setSessionSource(
  sessionId: number,
  payload: SourceUpdatePayload,
): Promise<LectureSession> {
  return apiPut<LectureSession>(`/sessions/${sessionId}/source`, payload);
}

/** DELETE /video returns updated SessionRead (aggregates kept). */
export function deleteSessionVideo(
  sessionId: number,
): Promise<LectureSession> {
  return apiRequest<LectureSession>(`/sessions/${sessionId}/video`, {
    method: "DELETE",
  });
}

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 * 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`;
  return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export function isAllowedVideoFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return name.endsWith(".mp4") || name.endsWith(".webm");
}
