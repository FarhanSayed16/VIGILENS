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

export type AnalysisRecover = {
  recovered: boolean;
  session_status: string;
  job: AnalysisJob | null;
  message: string;
};

export function startAnalysis(sessionId: number): Promise<AnalysisJob> {
  return apiPost<AnalysisJob>(`/sessions/${sessionId}/analysis`);
}

export function getJob(jobId: number): Promise<AnalysisJob> {
  return apiGet<AnalysisJob>(`/jobs/${jobId}`);
}

export async function getLatestJob(
  sessionId: number,
): Promise<AnalysisJob | null> {
  // API returns null (200) when no job exists yet
  const job = await apiGet<AnalysisJob | null>(
    `/sessions/${sessionId}/analysis/latest`,
  );
  return job ?? null;
}

export function recoverAnalysis(sessionId: number): Promise<AnalysisRecover> {
  return apiPost<AnalysisRecover>(`/sessions/${sessionId}/analysis/recover`);
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

export function isJobActive(job: AnalysisJob | null | undefined): boolean {
  return job?.status === "queued" || job?.status === "running";
}
