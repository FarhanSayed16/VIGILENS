"""
Phase 15 / Checkpoint A — full lecturer journey against live API + fake worker.

Requires: uvicorn on VIGILENS_API_BASE, Postgres, Redis.
Start API with USE_FAKE_WORKER=true (uploads a non-decodable stub blob).
"""

from __future__ import annotations

import time

import httpx
import pytest


def _wait_job(client: httpx.Client, headers: dict, job_id: int, timeout: float = 45.0) -> dict:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        r = client.get(f"/jobs/{job_id}", headers=headers)
        r.raise_for_status()
        last = r.json()
        if last["status"] in ("done", "error", "cancelled"):
            return last
        time.sleep(0.35)
    pytest.fail(f"Job {job_id} did not finish: {last}")


def test_full_journey_checkpoint_a(
    client: httpx.Client,
    auth_headers: dict[str, str],
    free_analysis_slot: None,
) -> None:
    h = auth_headers

    # 1. Login already done via fixture — verify /auth/me
    me = client.get("/auth/me", headers=h)
    assert me.status_code == 200
    assert me.json().get("username")

    # 2. Create room (seats + target)
    room = client.post(
        "/rooms",
        headers=h,
        json={
            "name": "Checkpoint A Room",
            "seat_regions": [
                {"type": "box", "id": "s1", "x": 0.05, "y": 0.2, "w": 0.2, "h": 0.25},
                {"type": "box", "id": "s2", "x": 0.3, "y": 0.2, "w": 0.2, "h": 0.25},
            ],
            "target_roi": {
                "type": "box",
                "id": "board",
                "x": 0.35,
                "y": 0.0,
                "w": 0.3,
                "h": 0.18,
            },
            "camera_defaults": {
                "preferred_source": "upload",
                "webcam_index": 0,
            },
        },
    )
    assert room.status_code == 201, room.text
    room_id = room.json()["id"]
    assert room.json()["seat_count"] >= 2

    # 3. Create session
    sess = client.post(
        "/sessions",
        headers=h,
        json={
            "title": "Checkpoint A lecture",
            "room_config_id": room_id,
            "source_type": "upload",
        },
    )
    assert sess.status_code == 201, sess.text
    sid = sess.json()["id"]
    assert sess.json()["status"] == "draft"

    # 4. Upload sample video
    blob = b"FAKEVIDEO_CHECKPOINT_A" + b"0" * 60_000
    up = client.post(
        f"/sessions/{sid}/upload",
        headers=h,
        files={"file": ("checkpoint_a.mp4", blob, "video/mp4")},
    )
    assert up.status_code == 200, up.text
    assert up.json()["has_video"] is True
    assert up.json()["status"] == "ready"

    # 5. Topics + modes
    t1 = client.post(
        f"/sessions/{sid}/topics",
        headers=h,
        json={"label": "Warm-up", "start_sec": 0},
    )
    assert t1.status_code == 201
    t2 = client.post(
        f"/sessions/{sid}/topics",
        headers=h,
        json={"label": "Core idea", "start_sec": 90},
    )
    assert t2.status_code == 201
    m1 = client.post(
        f"/sessions/{sid}/mode",
        headers=h,
        json={"mode": "explanation", "start_sec": 0},
    )
    assert m1.status_code == 201
    m2 = client.post(
        f"/sessions/{sid}/mode",
        headers=h,
        json={"mode": "qa", "start_sec": 120},
    )
    assert m2.status_code == 201

    topics = client.get(f"/sessions/{sid}/topics", headers=h).json()
    assert topics["total"] >= 2

    # Prepare second session before starting A (avoids races during job thread)
    sess_b = client.post(
        "/sessions",
        headers=h,
        json={
            "title": "Checkpoint A conflict",
            "room_config_id": room_id,
            "source_type": "webcam",
        },
    )
    assert sess_b.status_code == 201
    sid_b = sess_b.json()["id"]
    src_b = client.put(
        f"/sessions/{sid_b}/source",
        headers=h,
        json={"source_type": "webcam", "webcam_index": 0},
    )
    assert src_b.status_code == 200, src_b.text

    # 6 + quality: one-job-at-a-time — start A, conflict B
    job_a = client.post(f"/sessions/{sid}/analysis", headers=h)
    assert job_a.status_code == 202, job_a.text
    jid_a = job_a.json()["id"]

    conflict = client.post(f"/sessions/{sid_b}/analysis", headers=h)
    assert conflict.status_code == 409, conflict.text

    final_a = _wait_job(client, h, jid_a)
    assert final_a["status"] == "done"
    assert final_a["progress_pct"] == 100.0

    # 7. Results APIs (View Results)
    summary = client.get(f"/sessions/{sid}/summary", headers=h)
    assert summary.status_code == 200
    sbody = summary.json()
    assert sbody["window_count"] > 0
    assert sbody["mean_ttoi"] is not None

    windows = client.get(f"/sessions/{sid}/windows", headers=h)
    assert windows.status_code == 200
    assert windows.json()["total"] == sbody["window_count"]
    assert "ttoi" in windows.json()["items"][0]

    events = client.get(f"/sessions/{sid}/events", headers=h)
    assert events.status_code == 200
    assert events.json()["total"] == sbody["event_count"]

    # 8. Export CSV
    export = client.get(f"/sessions/{sid}/export", headers=h)
    assert export.status_code == 200
    assert "text/csv" in (export.headers.get("content-type") or "")
    csv_text = export.text
    assert "# WINDOWS" in csv_text
    assert "# EVENTS" in csv_text
    assert "# TOPICS" in csv_text
    assert "Warm-up" in csv_text
    assert "Core idea" in csv_text

    # 9. Pulse QR flow (public submit)
    pulse_bad = client.post(
        f"/pulse/{sid}", json={"score_1_to_5": 5, "student_name": "nope"}
    )
    assert pulse_bad.status_code == 422

    pulse = client.post(f"/pulse/{sid}", json={"score_1_to_5": 4})
    assert pulse.status_code == 200, pulse.text
    assert pulse.json()["score_1_to_5"] == 4
    assert pulse.json().get("topic_id") is not None

    # 10. Purge video (may already be auto-purged after analysis)
    before = client.get(f"/sessions/{sid}", headers=h).json()
    if before["has_video"]:
        purged = client.delete(f"/sessions/{sid}/video", headers=h)
        assert purged.status_code == 200
        assert purged.json()["has_video"] is False
    else:
        # Privacy default auto-purge after analysis — still OK
        assert before["status"] in ("purged_video", "complete")

    # Aggregates remain after purge
    assert (
        client.get(f"/sessions/{sid}/windows", headers=h).json()["total"] > 0
    )
    assert (
        client.get(f"/sessions/{sid}/export", headers=h).status_code == 200
    )

    # 11. Delete session
    deleted = client.delete(f"/sessions/{sid}", headers=h)
    assert deleted.status_code == 204
    gone = client.get(f"/sessions/{sid}", headers=h)
    assert gone.status_code == 404

    # Cleanup B (rooms have no DELETE in MVP — leave Checkpoint A Room)
    client.delete(f"/sessions/{sid_b}", headers=h)


def test_health_reports_deps(client: httpx.Client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"
    assert body.get("database", {}).get("status") == "ok"
    assert body.get("redis", {}).get("status") == "ok"
