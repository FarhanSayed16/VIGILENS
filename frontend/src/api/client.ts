import { clearSession, getAccessToken } from "../stores/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

export function getApiBaseUrl(): string {
  return API_BASE;
}

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  auth?: boolean;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true } = options;
  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (auth) {
    const token = getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && auth) {
    clearSession();
  }

  const text = await res.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const message =
      typeof data === "object" &&
      data !== null &&
      "message" in data &&
      typeof (data as { message: unknown }).message === "string"
        ? (data as { message: string }).message
        : `API ${res.status}: ${path}`;
    throw new ApiError(res.status, message, data);
  }

  return data as T;
}

export function apiGet<T>(path: string, auth = true): Promise<T> {
  return apiRequest<T>(path, { auth });
}

export function apiPost<T>(path: string, body?: unknown, auth = true): Promise<T> {
  return apiRequest<T>(path, { method: "POST", body, auth });
}

export function apiDelete(path: string, auth = true): Promise<void> {
  return apiRequest<void>(path, { method: "DELETE", auth });
}

export function apiPut<T>(path: string, body?: unknown, auth = true): Promise<T> {
  return apiRequest<T>(path, { method: "PUT", body, auth });
}

/** Download a binary/text response (e.g. CSV) and trigger a browser save. */
export async function apiDownload(
  path: string,
  fallbackFilename: string,
  auth = true,
): Promise<void> {
  const headers: Record<string, string> = { Accept: "*/*" };
  if (auth) {
    const token = getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (res.status === 401 && auth) {
    clearSession();
  }
  if (!res.ok) {
    let message = `API ${res.status}: ${path}`;
    try {
      const data = await res.json();
      if (
        typeof data === "object" &&
        data &&
        "message" in data &&
        typeof data.message === "string"
      ) {
        message = data.message;
      }
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, message);
  }
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const match = /filename="?([^";]+)"?/i.exec(disposition);
  const filename = match?.[1] ?? fallbackFilename;
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export type UploadProgress = {
  loaded: number;
  total: number;
  percent: number;
};

/** Multipart upload with progress (XHR). Do not set Content-Type — browser sets boundary. */
export function apiUploadFile<T>(
  path: string,
  file: File,
  options?: {
    fieldName?: string;
    auth?: boolean;
    onProgress?: (p: UploadProgress) => void;
  },
): Promise<T> {
  const { fieldName = "file", auth = true, onProgress } = options ?? {};

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}${path}`);
    xhr.setRequestHeader("Accept", "application/json");

    if (auth) {
      const token = getAccessToken();
      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      }
    }

    xhr.upload.onprogress = (ev) => {
      if (!onProgress) return;
      const total = ev.lengthComputable ? ev.total : file.size;
      const loaded = ev.loaded;
      const percent = total > 0 ? Math.min(100, Math.round((loaded / total) * 100)) : 0;
      onProgress({ loaded, total, percent });
    };

    xhr.onload = () => {
      if (xhr.status === 401 && auth) {
        clearSession();
      }
      let data: unknown = null;
      const text = xhr.responseText;
      if (text) {
        try {
          data = JSON.parse(text);
        } catch {
          data = text;
        }
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(data as T);
        return;
      }
      const message =
        typeof data === "object" &&
        data !== null &&
        "message" in data &&
        typeof (data as { message: unknown }).message === "string"
          ? (data as { message: string }).message
          : `API ${xhr.status}: ${path}`;
      reject(new ApiError(xhr.status, message, data));
    };

    xhr.onerror = () => {
      reject(new ApiError(0, "Network error during upload"));
    };

    const form = new FormData();
    form.append(fieldName, file, file.name);
    xhr.send(form);
  });
}
