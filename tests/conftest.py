"""Pytest fixtures for live-stack integration tests (Postgres + Redis + API)."""

from __future__ import annotations

import os
import time

import httpx
import pytest

BASE_URL = os.environ.get("VIGILENS_API_BASE", "http://127.0.0.1:8000").rstrip("/")


@pytest.fixture(scope="session")
def api_base() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def client(api_base: str) -> httpx.Client:
    with httpx.Client(base_url=api_base, timeout=60.0) as c:
        # Fail fast if API is down
        r = c.get("/health")
        if r.status_code != 200:
            pytest.skip(f"API not healthy at {api_base}: {r.status_code}")
        yield c


@pytest.fixture(scope="session")
def auth_headers(client: httpx.Client) -> dict[str, str]:
    r = client.post(
        "/auth/login",
        json={"username": "lecturer", "password": "change_me"},
    )
    if r.status_code != 200:
        pytest.skip(f"Login failed: {r.status_code} {r.text}")
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def clear_stale_analysis_lock(client: httpx.Client, headers: dict[str, str]) -> None:
    """
    Free Redis lock:analysis for tests.

    Waits briefly for a live job; if still held (e.g. worker killed mid-reload),
    cancels the DB row and deletes the lock so Checkpoint A can proceed.
    """
    try:
        import redis
        from app.core.settings import get_settings
        from app.db.enums import JobStatus, SessionStatus
        from app.db.models import AnalysisJob, Session as SessionModel
        from app.db.session import SessionLocal

        r = redis.from_url(get_settings().redis_url, decode_responses=True)
        try:
            for _ in range(20):
                holder = r.get("lock:analysis")
                if not holder:
                    return
                try:
                    jid = int(holder)
                except ValueError:
                    r.delete("lock:analysis")
                    return
                jr = client.get(f"/jobs/{jid}", headers=headers)
                if jr.status_code == 404:
                    r.delete("lock:analysis")
                    return
                status = jr.json().get("status")
                if status in ("done", "error", "cancelled"):
                    r.delete("lock:analysis")
                    return
                time.sleep(0.4)

            # Force-clear stuck lock from interrupted worker
            holder = r.get("lock:analysis")
            if holder:
                try:
                    jid = int(holder)
                except ValueError:
                    r.delete("lock:analysis")
                    return
                db = SessionLocal()
                try:
                    job = db.get(AnalysisJob, jid)
                    if job and job.status in (
                        JobStatus.QUEUED.value,
                        JobStatus.RUNNING.value,
                    ):
                        job.status = JobStatus.CANCELLED.value
                        job.error_message = "Cleared by test fixture (stale lock)"
                        sess = db.get(SessionModel, job.session_id)
                        if sess and sess.status == SessionStatus.ANALYZING.value:
                            sess.status = SessionStatus.READY.value
                        db.commit()
                finally:
                    db.close()
                r.delete("lock:analysis")
        finally:
            r.close()
    except Exception:
        pass


@pytest.fixture
def free_analysis_slot(client: httpx.Client, auth_headers: dict[str, str]) -> None:
    clear_stale_analysis_lock(client, auth_headers)
