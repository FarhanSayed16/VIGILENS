import { apiDownload } from "./client";

export function downloadSessionExport(sessionId: number): Promise<void> {
  return apiDownload(
    `/sessions/${sessionId}/export`,
    `vigilens_session_${sessionId}.csv`,
  );
}
