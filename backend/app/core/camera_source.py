"""Camera source helpers shared by session create and live start."""

from __future__ import annotations

from urllib.parse import urlparse

BROWSER_CAMERA_SOURCE = "browser:phone"


def is_browser_camera(url: str | None) -> bool:
    return bool(url) and url.strip().lower().startswith("browser:")


def is_app_page_url(url: str | None) -> bool:
    """True when the lecturer pasted the VIGILENS site instead of a camera stream."""
    if not url or is_browser_camera(url):
        return False
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    return port in (5173, 8000, 4173)


def reject_app_page_url(url: str | None) -> None:
    if is_app_page_url(url):
        raise ValueError(
            "That address is the VIGILENS website, not a camera. "
            "On the phone, choose This phone's camera and allow the camera prompt."
        )
