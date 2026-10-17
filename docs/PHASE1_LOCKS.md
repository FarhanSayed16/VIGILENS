# VIGILENS — Phase 1 Decision Locks

| | |
|---|---|
| **Status** | **LOCKED — Phase 1 complete** |
| **Date** | 17 October 2026 |
| **Owner confirmation** | Project owner: stick to plan; no scope changes; proceed to build |
| **Environment note** | This lab PC has **no Docker**. `docker-compose.yml` stays in the plan; **verify Postgres/Redis via Compose on home laptop**. No plan change. |

---

## 1.1 Product locks (final)

| Decision | Locked choice | Notes |
|---|---|---|
| Primary metric wording | **TTOI** — Teaching-Target Orientation Index | Observable orientation to teaching target — **not** “attention detector,” not mood/interest |
| Decline wording | **Candidate orientation decline** | Worth reviewing; not “students got bored” |
| Novelty claim | **No “first ever” claim** | Differentiate via TTOI + coverage + topics + privacy + local validation |
| Branding (MVP / reports) | **Keep VIGILENS** for now | vigilens.in name collision noted; if professor later wants an alternate public title, rename display only — no architecture change |
| MVP analysis path | **Upload / record → analyze job first** | Live webcam/phone preview secondary after pipeline is solid |
| Auth (MVP) | **Lecturer-only JWT** | Single/shared lecturer account; pulse page public/anonymous |
| Output level | **Class-level only** | No named student rankings, no face ID, no grading |
| Emotion / interest / mood models | **Out of scope** | Not added now or as product claim |
| Extra cues (phone, OpenVINO, Stage-B ML) | **After MVP only** | Do not block Phases 2–20 |
| Vision models (MVP) | **YOLOv8-pose + MediaPipe Face Landmarker** | Pretrained; no custom weights from owner |
| Training (MVP) | **None** — rule-based TTOI on pose geometry | Stage-B classifier optional later if it beats rules |
| Stack | **FastAPI + React + PostgreSQL + Redis** | Not Streamlit-as-product; not MongoDB primary |
| Build order | **App (BE+FE + fake worker) → then real AIML** | Per master plan Checkpoints A → B → C |

---

## 1.2 Plan document locks

| Document | Status |
|---|---|
| `docs/AIML_CONFIRMATION.md` | **Accepted** |
| `docs/BACKEND_PLAN.md` | **Accepted** |
| `docs/FRONTEND_PLAN.md` | **Accepted** |
| `docs/MASTER_PLAN.md` | **Accepted** as execution checklist |
| `docs/VIGILENS_COMPLETE_IDEA.md` | **Accepted** as product truth |
| `docs/DOCS_INDEX.md` | Navigation aid |

**Conflict rules (unchanged):**  
Execution order → Master · Product meaning → Complete Idea · Backend detail → Backend plan · UI → Frontend plan · Models → AIML confirmation.

---

## 1.3 Environment lock (Docker)

| Topic | Decision |
|---|---|
| Keep `docker-compose.yml` in repo? | **Yes** — plan unchanged |
| Verify Compose on this PC? | **No** — Docker not installed here |
| When to verify? | **Home laptop** (has Docker) — Phase 2 file still created; exit check “compose healthy” deferred to home |
| Dev without Docker on this PC? | Allowed later: local Postgres/Redis **or** defer DB bring-up until home; do **not** remove Compose from the plan |

---

## 1.4 Global non-negotiables (locked)

1. No face recognition / student identity storage  
2. No emotion / “boredom” product claims  
3. Class-level aggregates only  
4. Honest coverage / insufficient-evidence UX  
5. Wording: **TTOI** and **candidate orientation decline**  

---

## 1.5 Explicitly not changing

- No new ML models for mood/interest  
- No MongoDB, no Streamlit product UI  
- No skipping fake-worker Checkpoint A before real YOLO  
- No requirement to run Docker on the lab PC to continue Phase 2 scaffolding  

---

## 1.6 Phase 1 exit

| Criterion | Result |
|---|---|
| Product locks written | **Done** |
| Plan docs accepted | **Done** |
| Owner: Phase 1 done, stick to plan | **Done** (this session) |
| Next phase | **Phase 2 — Monorepo & engineering foundation** |

---

**Phase 1 is complete.** Start Phase 2 when ready.
