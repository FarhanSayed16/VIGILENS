# Vision thresholds — pilot start (Phase 21)

| | |
|---|---|
| **Date** | 18 October 2026 |
| **Config** | [`configs/default.yaml`](../configs/default.yaml) `version: 1` |
| **Status** | **Good enough for pilot** (scripted behaviours + honesty checks) |
| **Not claimed** | Classroom accuracy on institutional lectures (Phase 22) |

---

## Final values

| Parameter | Value | Role |
|---|---|---|
| `yaw_threshold_deg` | **30** | Tier-2 \|yaw'\| → target-oriented |
| `tier1_yaw_threshold_deg` | **45** | Tier-1 body/shoulder proxy (coarser) |
| `pitch_down_threshold_deg` | **20** | Head-down cue (+pitch = look down) |
| `face_width_min_px` | **80** | Tier-2 gate; below → Tier-1 or unobservable |
| `min_coverage_pct` | **70** | Below → null TTOI, no declines |
| `min_usable_seats` | **5** | Also suppress declines |
| `partial_window_min_seconds` | **15** | Partial → no decline alert |
| `min_drop_points` | **10** | Decline vs ~3 min baseline |
| `min_persist_windows` | **2** | Decline must persist |
| `window_seconds` | **30** | Aggregation |
| `frames_per_second` | **1.5** | Sample rate |

## Scripted behaviours verified

Harness: `python worker/scripts/eval_thresholds.py`  
Report: `uploads/_smoke/phase21_threshold_eval.json`

| Behaviour | Expected |
|---|---|
| Face board (yaw ≈ 0–10°) | High TTOI |
| Turn away (\|yaw\| ≫ 30°) | Low TTOI |
| Head down + explanation | Low TTOI |
| Head down + note_taking | High TTOI (mode hook) |
| Hand raise | `hand_raise_events` ≥ 1 |
| solvePnP L/R/U/D | Sign convention holds |
| Far / tiny face | No Tier-2; Tier-1 or unobservable |
| Few usable seats | `ttoi = null`, `insufficient_coverage` |

## Honesty rules (UI)

- Never fill missing TTOI with zero.
- Far seats must not invent head-pose precision.
- Results grey-hatch low coverage; amber declines only when evidence gates pass.

## Sign-off

Thresholds above are **approved as pilot start values**. Retune only with consented lecture labels (Phase 22) and record changes here + bump `version` in YAML.
