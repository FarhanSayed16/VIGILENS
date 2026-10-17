import { apiGet, apiPost, apiRequest } from "./client";

export type BoxRegion = {
  type: "box";
  id: string;
  label?: string | null;
  x: number;
  y: number;
  w: number;
  h: number;
};

export type CameraDefaults = {
  preferred_source?: "upload" | "webcam" | "phone_rtsp";
  webcam_index?: number;
  phone_url_example?: string | null;
};

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
