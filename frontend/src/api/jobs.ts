import { apiGet, apiPost } from "./client";

export type JobStatus =
  | "queued"
  | "running"
  | "done"
  | "error"
  | "cancelled";

export type JobStage =
  | "queued"
  | "ingest"
  | "vision"
  | "aggregate"
  | "done"
  | "error"
  | "cancelled";

export type AnalysisJob = {
  id: number;
  session_id: number;
  status: JobStatus;
  progress_pct: number;
  stage: JobStage | null;
  error_message: string | null;
  created_at: string;
  finished_at: string | null;
  message?: string;
};

export function startAnalysis(sessionId: number): Promise<AnalysisJob> {
  return apiPost<AnalysisJob>(`/sessions/${sessionId}/analysis`);
}

export function getJob(jobId: number): Promise<AnalysisJob> {
  return apiGet<AnalysisJob>(`/jobs/${jobId}`);
}

export const JOB_STAGES: { id: JobStage; label: string }[] = [
  { id: "ingest", label: "Ingest" },
  { id: "vision", label: "Vision" },
  { id: "aggregate", label: "Aggregate" },
  { id: "done", label: "Done" },
];

export function stageIndex(stage: JobStage | null | undefined): number {
  if (!stage || stage === "queued") return -1;
  if (stage === "error" || stage === "cancelled") return -2;
  const i = JOB_STAGES.findIndex((s) => s.id === stage);
  return i;
}
