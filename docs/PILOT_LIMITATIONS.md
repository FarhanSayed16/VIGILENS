# Known limitations — pilot (Phase 22)

Honest constraints. Do **not** overclaim classroom accuracy.

## Vision / geometry

| Limitation | Implication |
|---|---|
| Far / tiny faces (&lt; ~80 px) | Tier-1 body proxy or **unobservable** — no invented head yaw |
| Occlusion, backpacks, side views | Missed seats → lower coverage; TTOI may null |
| Seat boxes mis-drawn | Wrong N_expected / person→seat assignment |
| Short clips / few occupied seats | Often `insufficient_coverage`; declines suppressed (by design) |
| Hand-raise cue | Crude wrist-above-shoulder; misses subtle gestures |
| Teaching-target facing | Image-plane yaw' approximation; retune after real room calib |

## Metrics / declines

| Limitation | Implication |
|---|---|
| Rule-based TTOI only | Not a classifier of “engagement” or emotion |
| Decline Method A | Needs ~3 min baseline + 2-window persist; quiet starts may miss early dips |
| ±30 s human match | Timing honesty band — not frame-perfect agreement |
| note_taking mode | Head-down allowed; mis-tagged modes skew scores |

## Product / ops

| Limitation | Implication |
|---|---|
| One analysis job at a time | Global Redis lock |
| Local processing MVP | No multi-tenant cloud story yet |
| Consent is institutional | Still no grading / discipline / identity features |
| Classroom video not in git | Operators keep footage offline under consent protocol |

## What pilot success means

A successful Phase 22 operator run means: **one consented lecture** went through upload → real analysis → Results → CSV → purge, with limitations understood — **not** that VIGILENS is a validated engagement detector.
