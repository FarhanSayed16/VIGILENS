# Evaluation notes / metrics summary (Phase 24.2)

| | |
|---|---|
| **Date** | 18 October 2026 |
| **MVP validation mode** | Sample / public clip path ([`PILOT_SESSION.md`](./PILOT_SESSION.md) §A) |
| **Institutional lecture** | Optional — not required for Checkpoint C |

---

## What was evaluated

| Layer | Evidence |
|---|---|
| Fake-worker E2E | Checkpoint A — [`CHECKPOINT_A.md`](./CHECKPOINT_A.md) |
| Real YOLO + MediaPipe job | Checkpoint B — [`CHECKPOINT_B.md`](./CHECKPOINT_B.md) · `smoke_real_job.py` |
| Threshold honesty | [`THRESHOLDS.md`](./THRESHOLDS.md) · `eval_thresholds.py` · unit tests |
| Pilot tooling | [`PILOT_RUNBOOK.md`](./PILOT_RUNBOOK.md) · `pilot_dry_run.py` · ±30s compare |
| Demo polish | [`DEMO_DRY_RUN.md`](./DEMO_DRY_RUN.md) · [`PRIVACY_REVIEW_PHASE23.md`](./PRIVACY_REVIEW_PHASE23.md) |
| Automated unit | `pytest tests/unit` — aggregation, declines, thresholds, pilot match |

---

## Metrics summary (Stage A)

| Metric | Role | Notes |
|---|---|---|
| **TTOI %** | Share of usable seats oriented toward target | Null / suppressed when coverage low |
| **Coverage** | Usable evidence fraction | Gate ~70% (tunable) |
| **Candidate declines** | Persistent dips vs baseline | Method A; suppressed under poor coverage |
| **Secondary cues** | Head-down %, hand-raise counts | Observable only — not boredom scores |

Typical short-sample outcome: **honest `insufficient_coverage`**, few or no decline events. That is a **pass** for pipeline integrity, not a fail for “engagement detection.”

---

## Report screenshots

Capture checklist and paths: [`screenshots/README.md`](./screenshots/README.md).

---

## Claims allowed in write-ups

- Local lecturer workflow end-to-end with JWT, rooms, sessions, analysis, Results, CSV, purge, pulse  
- Pretrained vision + rule-based TTOI with coverage gating  
- Sample-clip / smoke validation of the pipeline  

## Claims to avoid until Section B pilot is filled

- Classroom accuracy, sensitivity/specificity vs human annotators  
- “Validated on N lectures” without records in `PILOT_SESSION.md` §B  
