import { getApiBaseUrl } from "./client";

export type HealthInfo = {
  status?: string;
  version?: string;
  use_fake_worker?: boolean;
  database?: string;
  redis?: string;
};

export async function fetchHealth(): Promise<HealthInfo | null> {
  try {
    const r = await fetch(`${getApiBaseUrl()}/health`);
    if (!r.ok) return null;
    return (await r.json()) as HealthInfo;
  } catch {
    return null;
  }
}
