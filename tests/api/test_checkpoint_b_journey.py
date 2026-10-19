"""
Phase 20 / Checkpoint B — real worker journey against live API.

Requires:
  - uvicorn with USE_FAKE_WORKER=false
  - Postgres + Redis
  - OpenCV-readable short MP4 (auto-built from bus.jpg under uploads/_smoke)

Skip when health reports use_fake_worker=true.
"""

from __future__ import annotations

import time
from pathlib import Path

import httpx
import pytest

REPO = Path(__file__).resolve().parents[2]


def _ensure_clip() -> Path:
    """Build / reuse phase20_bus_clip.mp4 via smoke helper pieces."""
    out = REPO / "uploads" / "_smoke" / "phase20_bus_clip.mp4"
    if out.is_file() and out.stat().st_size > 10_000:
        return out
    import sys

    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from worker.scripts.smoke_real_job import _ensure_bus, _write_clip_from_image

    bus = _ensure_bus(REPO / "uploads" / "_smoke" / "bus.jpg")
    return _write_clip_from_image(bus, out, n_frames=10, fps=2.0)


def _wait_job(
    client: httpx.Client, headers: dict, job_id: int, timeout: float = 300.0
) -> dict:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        r = client.get(f"/jobs/{job_id}", headers=headers)
        r.raise_for_status()
        last = r.json()
        if last["status"] in ("done", "error", "cancelled"):
            return last
        time.sleep(1.0)
    pytest.fail(f"Job {job_id} did not finish: {last}")


def test_checkpoint_b_real_worker_journey(
    client: httpx.Client,
    auth_headers: dict[str, str],
    free_analysis_slot: None,
) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    if health.json().get("use_fake_worker", True):
        pytest.skip(
            "API has USE_FAKE_WORKER=true — restart with USE_FAKE_WORKER=false for Checkpoint B"
        )

    h = auth_headers
    clip = _ensure_clip()

    room = client.post(
        "/rooms",
        headers=h,
        json={
            "name": "Checkpoint B Room",
            "seat_regions": [
                {"type": "box", "id": "s1", "x": 0.05, "y": 0.35, "w": 0.22, "h": 0.55},
                {"type": "box", "id": "s2", "x": 0.28, "y": 0.35, "w": 0.22, "h": 0.55},
                {"type": "box", "id": "s3", "x": 0.52, "y": 0.35, "w": 0.22, "h": 0.55},
                {"type": "box", "id": "s4", "x": 0.74, "y": 0.35, "w": 0.22, "h": 0.55},
            ],
            "target_roi": {
                "type": "box",
                "id": "board",
                "x": 0.3,
                "y": 0.0,
                "w": 0.4,
                "h": 0.2,
            },
        },
    )
    assert room.status_code == 201, room.text
    room_id = room.json()["id"]

    sess = client.post(
        "/sessions",
        headers=h,
        json={
            "title": "Checkpoint B real worker",
            "room_config_id": room_id,
            "source_type": "upload",
        },
    )
    assert sess.status_code == 201, sess.text
    sid = sess.json()["id"]

    data = clip.read_bytes()
    up = client.post(
        f"/sessions/{sid}/upload",
        headers=h,
        files={"file": ("checkpoint_b.mp4", data, "video/mp4")},
    )
    assert up.status_code == 200, up.text

    assert (
        client.post(
            f"/sessions/{sid}/topics",
            headers=h,
            json={"label": "Demo", "start_sec": 0},
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/sessions/{sid}/modes",
            headers=h,
            json={"mode": "explanation", "start_sec": 0},
        ).status_code
        == 201
    )

    start = client.post(f"/sessions/{sid}/analysis", headers=h)
    assert start.status_code == 200, start.text
    job_id = start.json()["id"]
    job = _wait_job(client, h, job_id, timeout=300.0)
    assert job["status"] == "done", job

    summary = client.get(f"/sessions/{sid}/summary", headers=h)
    assert summary.status_code == 200, summary.text
    assert summary.json()["window_count"] >= 1

    windows = client.get(f"/sessions/{sid}/windows", headers=h)
    assert windows.status_code == 200
    assert len(windows.json()["items"]) >= 1

    # Declines only when coverage OK — may be zero on short sample (honest)
    events = client.get(f"/sessions/{sid}/events", headers=h)
    assert events.status_code == 200

    export = client.get(f"/sessions/{sid}/export", headers=h)
    assert export.status_code == 200, export.text
    body = export.text
    assert "windows" in body.lower() or "ttoi" in body.lower()
    assert "video_path" not in body.lower()
