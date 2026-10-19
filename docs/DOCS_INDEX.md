# VIGILENS — Documentation Index

| | |
|---|---|
| **Purpose** | Map of all planning docs and which one to open for what |
| **Date** | 18 October 2026 |
| **Execution entry point** | [`MASTER_PLAN.md`](./MASTER_PLAN.md) |

---

## Start here for building

| Priority | Document | Use it for |
|---|---|---|
| **1 — Execute** | [`MASTER_PLAN.md`](./MASTER_PLAN.md) | Phases 1–24, checklists, checkpoints A/B/C, build order |
| **1b — Phase 1 locks** | [`PHASE1_LOCKS.md`](./PHASE1_LOCKS.md) | Locked product/plan decisions (**Phase 1 complete**) |
| **1c — Checkpoint A** | [`CHECKPOINT_A.md`](./CHECKPOINT_A.md) | Fake-worker app E2E sign-off (**Phase 15 complete**) |
| **1d — Checkpoint B** | [`CHECKPOINT_B.md`](./CHECKPOINT_B.md) | Real-worker analysis sign-off (**Phase 20 complete**) |
| **1e — Pilot** | [`PILOT_RUNBOOK.md`](./PILOT_RUNBOOK.md) | Consented lecture path + [`PILOT_LIMITATIONS.md`](./PILOT_LIMITATIONS.md) |
| **1f — Audit 1–23** | [`AUDIT_PHASES_1_23.md`](./AUDIT_PHASES_1_23.md) | Gaps, bugs, P0–P2 backlog before Phase 24 |
| **1g — Demo dry-run** | [`DEMO_DRY_RUN.md`](./DEMO_DRY_RUN.md) | Phase 23.4 sample-clip demo script |
| **1h — Privacy review** | [`PRIVACY_REVIEW_PHASE23.md`](./PRIVACY_REVIEW_PHASE23.md) | Phase 23.3 lightweight sign-off |
| **1h2 — Privacy live** | [`PRIVACY_REVIEW_PHASE32.md`](./PRIVACY_REVIEW_PHASE32.md) | Live cockpit privacy notes |
| **1i — Checkpoint C** | [`CHECKPOINT_C.md`](./CHECKPOINT_C.md) | **MVP complete** delivery sign-off |
| **1j — Evaluation** | [`EVALUATION_NOTES.md`](./EVALUATION_NOTES.md) | Metrics summary + claim boundaries |
| **1k — Limitations** | [`LIMITATIONS.md`](./LIMITATIONS.md) | Orientation ≠ learning |
| **1l — Related work** | [`RELATED_WORK.md`](./RELATED_WORK.md) | Not first-of-kind honesty |
| **1m — Stage-A card** | [`MODEL_CARD_STAGE_A.md`](./MODEL_CARD_STAGE_A.md) | Rules + pretrained detectors |
| **1n — Hardening pass** | [`POST_MVP_HARDENING.md`](./POST_MVP_HARDENING.md) | Gap fixes after Checkpoint C |
| **1o — Quick calibration** | [`QUICK_CALIBRATION.md`](./QUICK_CALIBRATION.md) | Viewpoint presets + detect seats |
| **1p — Live cockpit** | [`LIVE_COCKPIT_PLAN.md`](./LIVE_COCKPIT_PLAN.md) | Phase 25+ Start/Stop hybrid cockpit |
| **1q — Checkpoint D** | [`CHECKPOINT_D.md`](./CHECKPOINT_D.md) | Live Cockpit Hybrid sign-off |
| **2 — Product truth** | [`VIGILENS_COMPLETE_IDEA.md`](./VIGILENS_COMPLETE_IDEA.md) | What VIGILENS is/isn’t, TTOI, schema, API list, privacy |
| **3 — Backend detail** | [`BACKEND_PLAN.md`](./BACKEND_PLAN.md) | Modules, services, Redis, job lifecycle, folder plan |
| **4 — Frontend detail** | [`FRONTEND_PLAN.md`](./FRONTEND_PLAN.md) | Pages, theme, nav, components, motion |
| **5 — AIML detail** | [`AIML_CONFIRMATION.md`](./AIML_CONFIRMATION.md) | Models, tiers, training policy, what you must supply |
| **5b — Thresholds** | [`THRESHOLDS.md`](./THRESHOLDS.md) | Pilot-start YAML values + Phase 21 sign-off |

---

## Conflict rules

1. **Execution order** → `MASTER_PLAN.md` wins  
2. **Product meaning / metrics / privacy** → `VIGILENS_COMPLETE_IDEA.md` wins  
3. **Backend module contracts** → `BACKEND_PLAN.md`  
4. **UI/pages/theme** → `FRONTEND_PLAN.md`  
5. **Vision models** → `AIML_CONFIRMATION.md`  
6. **Numeric threshold start values** → `THRESHOLDS.md` / `configs/default.yaml`  

---

## Locked build strategy (summary)

```text
Foundation → Backend + Frontend (with fake worker) → Checkpoint A
         → Real AIML (YOLO + MediaPipe + TTOI rules) → Checkpoint B
         → Pilot → Polish → Delivery → Checkpoint C
```

- Backend and frontend scaffolds can run **in parallel** early.  
- Real ML starts **after** the full app works with a fake worker.  

---

## Checkpoints

| ID | Meaning | Master phase |
|---|---|---|
| **A** | Full app E2E with fake vision | **SIGNED OFF** (Phase 15, 18 Oct 2026) |
| **B** | Real YOLO/MediaPipe analysis in the app | **SIGNED OFF** (Phase 20, 18 Oct 2026) |
| **C** | MVP complete (pilot + docs + demo) | **SIGNED OFF** (Phase 24, 18 Oct 2026) |

---

## How to work with the agent

1. Confirm plans if needed: *Master confirmed*  
2. Run: **Start Phase N**  
3. Finish that phase’s checkboxes  
4. Mark: **Phase N done**  
5. Do not skip Checkpoint A before AIML phases  

---

## Document status

| Doc | Status |
|---|---|
| Complete idea | Authoritative product |
| AIML confirmation | Locked |
| Backend plan | Locked |
| Frontend plan | Locked |
| Master plan | **Phases 1–24 complete**; Checkpoint C signed off |
| Phase 1 locks | **Complete** (17 Oct 2026) |
| Checkpoint C | **SIGNED OFF** (18 Oct 2026) |
| This index | Navigation aid |

## Execution progress

| Phase | Status |
|---|---|
| **1 — Lock decisions** | **DONE** |
| **2 — Monorepo foundation** | **DONE** — Compose verified healthy (18 Oct 2026) |
| **3 — Backend scaffold** | **DONE** |
| **4 — Frontend scaffold** | **DONE** |
| **5 — Database schema** | **DONE** — `alembic upgrade head` applied on live Postgres |
| **6 — Auth & security** | **DONE** — login / JWT / 401 verified live |
| **7 — Rooms** | **DONE** — create/list verified on Postgres (use field names `seat_regions` / `target_roi`) |
| **8 — Sessions** | **DONE** |
| **9 — Topics & modes** | **DONE** |
| **10 — Media upload** | **DONE** |
| **11 — Jobs + fake worker** | **DONE** |
| **12 — Results APIs** | **DONE** |
| **13 — Results UI** | **DONE** |
| **14 — Export / purge / pulse** | **DONE** |
| **15 — Checkpoint A** | **DONE** — see [`CHECKPOINT_A.md`](./CHECKPOINT_A.md) |
| **16 — AIML foundation** | **DONE** — capture + config + regions; YOLO/MP stubs |
| **17 — YOLOv8-pose** | **DONE** — seat assign + N_expected; smoke overlay |
| **18 — MediaPipe Tier-2** | **DONE** — Face Landmarker + solvePnP signs verified |
| **19 — TTOI / coverage / declines** | **DONE** — offline metrics + unit tests + schema JSON |
| **20 — Real worker integration** | **DONE** — Checkpoint B; `USE_FAKE_WORKER` flag |
| **21 — Threshold tuning** | **DONE** — see [`THRESHOLDS.md`](./THRESHOLDS.md) |
| **22 — Pilot / validation** | **DONE** — sample-clip MVP path (`PILOT_SESSION.md` §A) |
| **23 — Hardening / demo polish** | **DONE** — subnav, a11y, privacy review, demo dry-run |
| **24 — Delivery / Checkpoint C** | **DONE** — see [`CHECKPOINT_C.md`](./CHECKPOINT_C.md) |

**Docker (verified):** `docker compose up -d` → `vigilens-postgres` + `vigilens-redis` healthy. Use **Python 3.12** for backend venv (`py -3.12 -m venv .venv`); Python 3.14 lacks many wheels.
