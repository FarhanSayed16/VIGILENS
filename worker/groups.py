"""
Anonymous seat clustering for live cockpit (Phase 29).

No face identity — seat_ids only. Groups are temporary labels (A, B, …).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple


def _parse_seat_index(seat_id: str) -> Tuple[int, int]:
    """Best-effort row/col from labels like R2C3, seat_3, s3."""
    s = seat_id.strip().upper()
    import re

    m = re.match(r"R(\d+)\s*C(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+)", s)
    if m:
        n = int(m.group(1))
        return n // 10, n % 10
    return 0, hash(seat_id) % 100


def _adjacent(a: str, b: str) -> bool:
    ra, ca = _parse_seat_index(a)
    rb, cb = _parse_seat_index(b)
    return abs(ra - rb) + abs(ca - cb) <= 1 and a != b


def cluster_low_orientation_seats(
    per_seat: Sequence[Dict[str, Any]],
    *,
    low_threshold: float = 45.0,
    min_group_size: int = 2,
) -> List[Dict[str, Any]]:
    """
    Group adjacent usable seats with orientation below threshold.

    Returns list of {label, seat_ids, orientation_pct, kind}.
    """
    low: List[Dict[str, Any]] = []
    for s in per_seat:
        o = s.get("orientation_pct")
        if not s.get("usable"):
            continue
        if o is None:
            continue
        if float(o) < low_threshold:
            low.append(s)
    if len(low) < min_group_size:
        return []

    ids = [str(s["seat_id"]) for s in low]
    o_map = {str(s["seat_id"]): float(s["orientation_pct"]) for s in low}
    remaining = set(ids)
    clusters: List[List[str]] = []
    while remaining:
        seed = remaining.pop()
        stack = [seed]
        comp = [seed]
        while stack:
            cur = stack.pop()
            for other in list(remaining):
                if _adjacent(cur, other):
                    remaining.remove(other)
                    stack.append(other)
                    comp.append(other)
        if len(comp) >= min_group_size:
            clusters.append(sorted(comp))

    out: List[Dict[str, Any]] = []
    for i, seats in enumerate(clusters):
        label = chr(ord("A") + (i % 26))
        if i >= 26:
            label = f"G{i + 1}"
        vals = [o_map[sid] for sid in seats]
        mean_o = sum(vals) / len(vals) if vals else None
        kind = "interaction" if len(seats) >= 3 and mean_o is not None and mean_o < 40 else "decline_cluster"
        out.append(
            {
                "label": f"Group {label}",
                "seat_ids": seats,
                "orientation_pct": round(mean_o, 1) if mean_o is not None else None,
                "kind": kind,
            }
        )
    return out


def groups_to_events(
    groups: Sequence[Dict[str, Any]],
    *,
    start_sec: float,
    end_sec: float,
    coverage_pct: Optional[float],
) -> List[Dict[str, Any]]:
    """Materialize group clusters as event payloads for persist on Stop."""
    events: List[Dict[str, Any]] = []
    for g in groups:
        o = g.get("orientation_pct")
        depth = max(0.0, 70.0 - float(o)) if o is not None else 10.0
        kind = (
            "interaction"
            if g.get("kind") == "interaction"
            else "orientation_decline"
        )
        events.append(
            {
                "start_sec": float(start_sec),
                "end_sec": float(end_sec),
                "depth": round(depth, 1),
                "coverage_pct": coverage_pct,
                "note": (
                    "Possible interaction pattern among neighboring seats"
                    if kind == "interaction"
                    else "Sustained low orientation cluster (anonymous seats)"
                ),
                "kind": kind,
                "seat_ids": list(g.get("seat_ids") or []),
                "group_label": g.get("label"),
            }
        )
    return events
