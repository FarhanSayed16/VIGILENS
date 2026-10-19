# Limitations — read before claiming results

VIGILENS reports **observable class-level orientation toward a teaching target (TTOI)**, gated by **coverage**. It does **not** measure learning, attention, interest, emotion, or individual students.

---

## Core product limits

| Claim to avoid | Reality |
|---|---|
| “Attention dropped” | Orientation toward the board/screen declined (or coverage was low) |
| “Students are bored / disengaged” | Looking down may be note-taking; modes change interpretation |
| “Accurate engagement score” | Rule-based proxy with uncertainty; declines are *candidates* |
| “Works on any classroom video” | Needs usable seats, faces/bodies large enough, sensible seat ROIs |

---

## Vision / geometry

| Limitation | Implication |
|---|---|
| Far / tiny faces | Tier-1 body proxy or **unobservable** — no invented yaw |
| Occlusion, side views | Missed seats → lower coverage; TTOI may null |
| Mis-drawn seat boxes | Wrong N_expected / assignment |
| Short clips / few people | Often `insufficient_coverage`; declines suppressed **by design** |
| Hand-raise cue | Crude wrist-above-shoulder heuristic |
| Target facing | Image-plane yaw' approximation; retune per room |
| Live seat / group map | Anonymous geometry only — not who is talking; interaction patterns are suggestive |
| Single primary camera | Secondary source is display-only; metrics are not dual-fused |
| Live 30s windows | Provisional until Stop; declines finalized after Stop |

---

## Metrics / declines

| Limitation | Implication |
|---|---|
| Stage-A rules only | Not a trained engagement classifier |
| Decline Method A | Needs baseline + persist; quiet starts may miss early dips |
| Mode tags wrong | e.g. note-taking vs lecture changes head-down policy |

---

## Ops

| Limitation | Implication |
|---|---|
| One analysis job at a time | Global Redis lock |
| Single lecturer account | No multi-tenant ACL |
| Local MVP | Not a cloud SaaS story yet |
| Sample-clip validation | Does **not** equal classroom accuracy claims |

Pilot-specific detail: [`PILOT_LIMITATIONS.md`](./PILOT_LIMITATIONS.md).
