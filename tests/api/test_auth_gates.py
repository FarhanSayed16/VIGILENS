"""Quality gate: operator routes require JWT."""

from __future__ import annotations

import httpx
import pytest


PROTECTED = [
    ("GET", "/rooms"),
    ("GET", "/sessions"),
    ("GET", "/sessions/1"),
    ("GET", "/sessions/1/summary"),
    ("GET", "/sessions/1/windows"),
    ("GET", "/sessions/1/events"),
    ("GET", "/sessions/1/topics"),
    ("GET", "/sessions/1/modes"),
    ("GET", "/sessions/1/export"),
    ("POST", "/sessions/1/analysis"),
    ("GET", "/jobs/1"),
]


@pytest.mark.parametrize("method,path", PROTECTED)
def test_operator_routes_require_auth(
    client: httpx.Client, method: str, path: str
) -> None:
    r = client.request(method, path)
    assert r.status_code == 401, f"{method} {path} → {r.status_code} {r.text}"


def test_public_routes_ok_without_auth(client: httpx.Client) -> None:
    assert client.get("/health").status_code == 200
    # pulse may 404 for missing session, but must not be 401
    r = client.post("/pulse/999999", json={"score_1_to_5": 3})
    assert r.status_code in (404, 200, 422)
    assert r.status_code != 401
