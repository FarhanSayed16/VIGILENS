import { apiGet, apiPost } from "./client";

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  username: string;
};

export type LecturerMe = {
  username: string;
  role: string;
};

export function loginRequest(username: string, password: string): Promise<TokenResponse> {
  return apiPost<TokenResponse>("/auth/login", { username, password }, false);
}

export function fetchMe(): Promise<LecturerMe> {
  return apiGet<LecturerMe>("/auth/me", true);
}
