/** This phone's camera, pushed to the PC. Not an IP Webcam URL. */
export const BROWSER_CAMERA_SOURCE = "browser:phone";

export function isPhoneDevice(): boolean {
  if (typeof navigator === "undefined") return false;
  const ua = navigator.userAgent || "";
  if (/Android|iPhone|iPad|iPod|Mobile/i.test(ua)) return true;
  return navigator.maxTouchPoints > 1 && window.matchMedia("(max-width: 900px)").matches;
}

export function isBrowserCameraSource(url: string | null | undefined): boolean {
  return (url || "").trim().toLowerCase().startsWith("browser:");
}

/** The VIGILENS site itself — not a camera stream. */
export function isAppPageUrl(url: string | null | undefined): boolean {
  const raw = (url || "").trim();
  if (!raw || isBrowserCameraSource(raw)) return false;
  try {
    const u = new URL(raw);
    const port = u.port || (u.protocol === "https:" ? "443" : "80");
    return port === "5173" || port === "8000" || port === "4173";
  } catch {
    return false;
  }
}

export function isRealCameraStream(url: string | null | undefined): boolean {
  const raw = (url || "").trim();
  if (!raw || isBrowserCameraSource(raw) || isAppPageUrl(raw)) return false;
  return /^rtsp:\/\//i.test(raw) || /^https?:\/\//i.test(raw);
}

/** Phone browser should capture with getUserMedia and send frames to the PC. */
export function shouldUsePhoneCamera(
  sourceType: string,
  sourceUrl: string | null | undefined,
): boolean {
  if (isBrowserCameraSource(sourceUrl)) return true;
  if (!isPhoneDevice() || sourceType !== "phone_rtsp") return false;
  return !isRealCameraStream(sourceUrl);
}
