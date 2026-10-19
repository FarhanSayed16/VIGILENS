import { ApiError, apiGet, apiPost, apiRequest, getApiBaseUrl } from "./client";
import { getAccessToken } from "../stores/auth";

export type BoxRegion = {
  type: "box";
  id: string;
  label?: string | null;
  x: number;
  y: number;
  w: number;
  h: number;
};

export type CameraPlacement =
  | "back_of_room"
  | "facing_class"
  | "left_side"
  | "right_side";

export type CameraDefaults = {
  preferred_source?: "upload" | "webcam" | "phone_rtsp";
  webcam_index?: number;
  phone_url_example?: string | null;
  placement?: CameraPlacement | string | null;
  /** toward_camera = no in-frame board; looking at lens = oriented */
  facing_mode?: "toward_camera" | "toward_board" | string | null;
};

export type CalibrateSuggestResult = {
  placement: CameraPlacement;
  seat_regions: BoxRegion[];
  target_roi: BoxRegion | null;
  facing_mode: string;
  hint: string;
  mode: string;
};

export type CalibrateDetectResult = CalibrateSuggestResult & {
  people_found: number;
  message?: string | null;
};

export function suggestCalibration(body: {
  placement: CameraPlacement;
  rows?: number;
  cols?: number;
}): Promise<CalibrateSuggestResult> {
  return apiPost<CalibrateSuggestResult>("/rooms/calibrate/suggest", body);
}

export async function detectCalibration(
  file: File,
  opts: { placement: CameraPlacement; rows?: number; cols?: number },
): Promise<CalibrateDetectResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("placement", opts.placement);
  form.append("rows", String(opts.rows ?? 3));
  form.append("cols", String(opts.cols ?? 4));
  const headers: Record<string, string> = { Accept: "application/json" };
  const token = getAccessToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${getApiBaseUrl()}/rooms/calibrate/detect`, {
    method: "POST",
    headers,
    body: form,
  });
  if (res.status === 401) {
    const { clearSession } = await import("../stores/auth");
    clearSession();
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message =
      typeof data === "object" &&
      data &&
      "message" in data &&
      typeof data.message === "string"
        ? data.message
        : `API ${res.status}`;
    throw new ApiError(res.status, message, data);
  }
  return data as CalibrateDetectResult;
}

export type Room = {
  id: number;
  name: string;
  seat_regions: BoxRegion[];
  target_roi: BoxRegion | null;
  camera_defaults: CameraDefaults | null;
  created_at: string;
  seat_count: number;
};

export type RoomPayload = {
  name: string;
  seat_regions: BoxRegion[];
  target_roi: BoxRegion | null;
  camera_defaults?: CameraDefaults | null;
};

export function listRooms(): Promise<Room[]> {
  return apiGet<Room[]>("/rooms");
}

export function getRoom(id: number): Promise<Room> {
  return apiGet<Room>(`/rooms/${id}`);
}

export function createRoom(payload: RoomPayload): Promise<Room> {
  return apiPost<Room>("/rooms", payload);
}

export function updateRoom(id: number, payload: Partial<RoomPayload>): Promise<Room> {
  return apiRequest<Room>(`/rooms/${id}`, { method: "PUT", body: payload });
}
