const TOKEN_KEY = "vigilens_access_token";
const USER_KEY = "vigilens_username";

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUsername(): string | null {
  return localStorage.getItem(USER_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(getAccessToken());
}

export function setSession(token: string, username: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, username);
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
