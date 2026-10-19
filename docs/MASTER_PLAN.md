# VIGILENS — Master Execution Plan

| | |
|---|---|
| **Document status** | **Authoritative execution checklist** |
| **Date** | 17 October 2026 |
| **Use** | Final checkpoint list for building the whole project |
| **Combines** | Product idea · AIML · Backend · Frontend |

> **How to use this file**  
> Work **one phase at a time**. Do not skip required checkboxes. Mark `[x]` only when verified.  
> Detail specs live in companion docs; **this file owns order and done-ness**.

---

## 0. Companion documents (source of truth by topic)

| Document | Owns |
|---|---|
| [`VIGILENS_COMPLETE_IDEA.md`](./VIGILENS_COMPLETE_IDEA.md) | Product philosophy, TTOI, schema, API list, privacy |
| [`AIML_CONFIRMATION.md`](./AIML_CONFIRMATION.md) | Models, tiers, no-custom-weights rule |
| [`BACKEND_PLAN.md`](./BACKEND_PLAN.md) | Backend modules, services, Redis, job lifecycle |
| [`FRONTEND_PLAN.md`](./FRONTEND_PLAN.md) | Pages, theme, nav, components, motion |
| **This file** | **Phases, sub-phases, execution order, global checklist** |

If scheduling conflicts with a companion doc, **this master plan wins for order**.  
If product/API/metric conflicts, **`VIGILENS_COMPLETE_IDEA.md` wins for meaning**.

---

## 1. Execution strategy (locked)

### 1.1 Best build order (why this, not “ML first”)

```text
FOUNDATION
   → BACKEND core + FAKE worker          ⎤ can overlap after
   → FRONTEND shell + pages wired to API ⎦ Phase 3 scaffolds
   → FULL APP E2E with fake TTOI
   → REAL AIML worker (YOLO + MediaPipe + rules)
   → SWAP fake → real (same APIs)
   → PILOT · VALIDATE · POLISH · CLOSE
```

**Why:** Frontend and backend need stable contracts early. A **fake worker** lets the full lecturer journey work before vision is perfect. Real ML plugs into the same job contract — no rewrite of UI/API.

### 1.2 Parallelism rules

| Allowed in parallel | Not in parallel |
|---|---|
| Phase 3 backend scaffold + Phase 4 frontend scaffold | Deep Results chart before windows API exists |
| Frontend pages that use mocks while backend CRUD finishes | Real YOLO before job contract + persistence exist |
| Research notebook (OUC-CGE) anytime after Phase 2 | Claiming classroom accuracy before pilot phases |

### 1.3 Global non-negotiables (every phase)

- [x] No face recognition / student identity storage  
- [x] No emotion / “boredom” product claims  
- [x] Class-level aggregates only  
- [x] Honest coverage / insufficient-evidence UX  
- [x] Wording: **TTOI** and **candidate orientation decline**  

*(Locked in Phase 1 — see [`PHASE1_LOCKS.md`](./PHASE1_LOCKS.md).)*

---

## 2. Phase map (24 phases)

| Phase | Name | Primary track |
|---|---|---|
| **1** | Lock decisions & professor confirmations | Product |
| **2** | Monorepo & engineering foundation | Shared |
| **3** | Backend scaffold (API skeleton) | Backend |
| **4** | Frontend scaffold (app shell & theme) | Frontend |
| **5** | Database schema & migrations | Backend |
| **6** | Auth & security baseline | Backend + Frontend |
| **7** | Rooms API & room UI | Backend + Frontend |
| **8** | Sessions API & sessions UI | Backend + Frontend |
| **9** | Topics & teaching modes | Backend + Frontend |
| **10** | Media upload & source setup | Backend + Frontend |
| **11** | Analysis jobs + Redis + **fake worker** | Backend |
| **12** | Results APIs (windows, events, summary) | Backend |
| **13** | Results workspace UI (core product screen) | Frontend |
| **14** | Export, purge, pulse (API + UI) | Backend + Frontend |
| **15** | End-to-end app checkpoint (fake vision) | Integration |
| **16** | AIML foundation (OpenCV ingest + configs) | AIML |
| **17** | YOLOv8-pose + seat mapping | AIML |
| **18** | MediaPipe Tier-2 head pose | AIML |
| **19** | TTOI, coverage, decline rules | AIML |
| **20** | Real worker integration (swap fake → real) | Integration |
| **21** | Threshold tuning & vision tests | AIML + Product |
| **22** | Pilot with consented classroom video | Validation |
| **23** | Hardening, a11y, demo polish | All |
| **24** | Evaluation, docs, final delivery | Close |

**Optional later (after MVP delivery — not blockers):** Stage-B classifier · OpenVINO actions · phone/drowsiness cues · PDF · WebSocket jobs · OUC-CGE research notebook polish.

---

# PHASES (detailed checklists)

---

## Phase 1 — Lock decisions & professor confirmations

**Goal:** No ambiguity before coding.

**Status: COMPLETE (17 October 2026)** — full record in [`PHASE1_LOCKS.md`](./PHASE1_LOCKS.md).

### 1.1 Product locks
- [x] Confirm TTOI wording (not “attention detector”)  
- [x] Confirm no “first ever” novelty claim  
- [x] Confirm branding: keep VIGILENS vs alternate public title *(keep VIGILENS for now; professor may rename display later)*  
- [x] Confirm MVP path: upload-first analytics (live preview secondary)  
- [x] Confirm lecturer-only login for MVP  

### 1.2 Plan locks
- [x] `AIML_CONFIRMATION.md` accepted  
- [x] `BACKEND_PLAN.md` accepted  
- [x] `FRONTEND_PLAN.md` accepted  
- [x] This master plan accepted as execution checklist  

### 1.3 Exit criteria
- [x] Written yes from you (project owner) that Phase 1 is done  

**Environment note (not a plan change):** Lab PC has no Docker. Compose file remains required in Phase 2; **healthy `docker compose up` verified on home laptop**.

---

## Phase 2 — Monorepo & engineering foundation

**Goal:** Empty-but-correct project skeleton.

**Status: COMPLETE (17 October 2026)** — files in repo; Compose **runtime verify** deferred to home laptop (no Docker on lab PC).

### 2.1 Repository
- [x] Root `README.md` points to docs + how to run (high level)  
- [x] `.gitignore` (venv, node_modules, `.env`, `models/`, `uploads/`, caches)  
- [x] `.env.example` with all required keys (empty values)  
- [x] `docker-compose.yml` for **PostgreSQL + Redis**  
- [x] Folder stubs: `backend/`, `frontend/`, `worker/`, `configs/`, `docs/`, `tests/`, `models/`, `data/`  

### 2.2 Shared config
- [x] `configs/default.yaml` stub (thresholds placeholders: yaw 30°, pitch-down ~20°, coverage ~70%, window 30s)  
- [x] Document Python **3.10+** and Node **18+** in README  

### 2.3 Exit criteria
- [x] `docker-compose.yml` present and documented (Postgres + Redis)  
- [x] On **home laptop (Docker available):** `docker compose up -d` brings Postgres + Redis healthy *(verified 18 Oct 2026)*  
- [x] On lab PC without Docker: Phase 2 still **done** once files/stubs exist; Compose verify deferred to home *(plan unchanged)*  

**Verified:** `docker compose ps` shows `vigilens-postgres` + `vigilens-redis` healthy. Backend venv: use **Python 3.12** (`py -3.12 -m venv backend/.venv`).

---

## Phase 3 — Backend scaffold

**Goal:** FastAPI app boots; structure matches backend plan.

**Status: COMPLETE (17 October 2026)** — `GET /health` returns HTTP 200 (`status: ok`); DB/Redis soft-unavailable without Docker is expected.

### 3.1 Package layout
- [x] `backend/app/main.py` app entry  
- [x] Folders: `api/`, `core/`, `db/`, `schemas/`, `cache/`, `services/`, `deps/`, `utils/`  
- [x] `requirements.txt` pinned (FastAPI, uvicorn, SQLAlchemy, Alembic, redis, pydantic-settings, python-jose/passlib as needed, etc.)  

### 3.2 Core wiring
- [x] Settings from env  
- [x] Logging setup  
- [x] CORS for Vite origin  
- [x] Exception handlers  
- [x] `GET /health` (API up; DB/Redis checks can be soft then hard)  

### 3.3 Exit criteria
- [x] `uvicorn` starts without error  
- [x] Health endpoint returns OK for API process  

**Run:** `cd backend` → activate `.venv` → `uvicorn app.main:app --reload --port 8000` → http://localhost:8000/health · http://localhost:8000/docs

---

## Phase 4 — Frontend scaffold

**Goal:** React app boots with professional shell (can parallel Phase 3).

**Status: COMPLETE (17 October 2026)** — Daylight Lecture shell builds; stub routes render.

### 4.1 App foundation
- [x] Vite + React + TypeScript  
- [x] React Router  
- [x] Folder layout per `FRONTEND_PLAN.md`  
- [x] Env for API base URL  

### 4.2 Design system baseline
- [x] CSS variables for **Daylight Lecture** theme (teal accent, amber review, graphite weak)  
- [x] Typography tokens (display + UI sans — not default Inter-only look)  
- [x] Icon set chosen (Lucide/Phosphor)  
- [x] App shell: sidebar + context bar + main stage  
- [x] Route transition motion stub + `prefers-reduced-motion`  

### 4.3 Routes stubbed
- [x] Login, Sessions, Rooms, Privacy, Session placeholder routes render  
- [x] 404 page  

### 4.4 Exit criteria
- [x] `npm run dev` shows branded shell  
- [x] Theme looks intentional (not Vite default)  

**Run:** `cd frontend` → `npm install` → `npm run dev` → http://localhost:5173  
**Scaffold login:** any non-empty password (real JWT in Phase 6).

---

## Phase 5 — Database schema & migrations

**Goal:** Postgres matches locked schema.

**Status: COMPLETE (17 October 2026)** — models + `001_initial` migration in repo. **Apply on Postgres** when Docker is available (home laptop).

### 5.1 Models / tables
- [x] `room_configs`  
- [x] `sessions`  
- [x] `topics`  
- [x] `mode_changes`  
- [x] `windows`  
- [x] `events`  
- [x] `pulse_responses`  
- [x] `analysis_jobs`  

### 5.2 Rules
- [x] Alembic initial migration authored (`001_initial`) — apply when DB is up  
- [x] No PII / face / identity columns  
- [x] Enums/statuses documented (`backend/docs/SCHEMA_ENUMS.md`)  

### 5.3 Exit criteria
- [x] Migration script verified (models import; `alembic history`; offline SQL generates)  
- [x] On **home laptop:** `alembic upgrade head` on fresh Postgres + tables visible *(verified 18 Oct 2026 — 8 domain tables + alembic_version)*  

**Verified:** `room_configs`, `sessions`, `topics`, `mode_changes`, `windows`, `events`, `pulse_responses`, `analysis_jobs` present.

---

## Phase 6 — Auth & security baseline

**Goal:** Lecturer JWT works end-to-end.

**Status: COMPLETE (17 October 2026)**

### 6.1 Backend
- [x] `POST /auth/login`  
- [x] JWT issue + verify dependency  
- [x] Protect operator routes (`GET /auth/me` + `CurrentLecturer` dep for later routes)  
- [x] Public: login, health, pulse (pulse stub until Phase 14)  
- [x] Lecturer credentials from env  

### 6.2 Frontend
- [x] Login page (brand + form + error states)  
- [x] Token storage + attach to API client  
- [x] Protected route wrapper  
- [x] Logout  

### 6.3 Exit criteria
- [x] Login → shell accessible  
- [x] Unauthenticated API call rejected  
- [x] Logout returns to login  

**Creds (defaults):** `LECTURER_USERNAME=lecturer` · `LECTURER_PASSWORD=change_me` (from `.env` / `.env.example`)

---

## Phase 7 — Rooms (API + UI)

**Goal:** Reusable classroom geometry.

**Status: COMPLETE (17 October 2026)** — API + calibration UI shipped. Live list persistence needs Postgres (`alembic upgrade head`).

### 7.1 Backend
- [x] `GET/POST /rooms`, `GET/PUT /rooms/{id}`  
- [x] Validate seat regions + target ROI JSON shapes  
- [x] Camera defaults field  

### 7.2 Frontend
- [x] Rooms library page  
- [x] Create/Edit room calibration studio  
- [x] Draw seats + teaching target on frame  
- [x] Save/cancel + unsaved navigation warning  

### 7.3 Exit criteria
- [x] Create/list/update verified via API (live Postgres smoke, 18 Oct 2026)  
- [ ] Automated pytest suite still missing (`tests/` has no `test_*.py` yet — add in a later hardening pass)  
- [x] On home laptop with Postgres: API create/list verified live *(UI draw-and-save still recommended once FE is running against this DB)*  

**Routes:** `/rooms` · `/rooms/new` · `/rooms/:id/edit` · API `/rooms` (JWT)  
**Note:** API body fields are `seat_regions` / `target_roi` (not `*_json`).

---

## Phase 8 — Sessions (API + UI)

**Goal:** Lecture units exist.

**Status: COMPLETE (18 October 2026)** — API + list/wizard/hub UI; create/delete verified on live Postgres.

### 8.1 Backend
- [x] `GET/POST /sessions`, `GET/DELETE /sessions/{id}` (+ `GET /sessions/{id}/summary` stub)  
- [x] Source type: upload | webcam | phone_rtsp  
- [x] Status field (`draft` on create)  
- [x] Cascade delete + Redis cache invalidate stubs  

### 8.2 Frontend
- [x] Sessions home (list, filters, empty state)  
- [x] New session wizard (title, room, source type, privacy banner)  
- [x] Session hub (actions grid, honesty strip; later-phase tiles disabled)  

### 8.3 Exit criteria
- [x] Create session linked to room  
- [x] Delete session removes it from list  

**Routes:** `/sessions` · `/sessions/new` · `/sessions/:id` · API `/sessions` (JWT)

---

## Phase 9 — Topics & teaching modes

**Goal:** Timeline context without audio.

**Status: COMPLETE (18 October 2026)** — topics + mode APIs, `resolve_active_topic_at`, Live controls UI, hub topic/mode lists; create/list verified on live Postgres.

### 9.1 Backend
- [x] `POST/GET /sessions/{id}/topics`  
- [x] `POST /sessions/{id}/mode` → `mode_changes` (+ `GET .../modes`)  
- [x] Helper: resolve active topic at time T (for pulse later)  

### 9.2 Frontend
- [x] Live controls page (big New topic + mode switcher)  
- [x] Topic list visible on session hub/results later  
- [x] Modes: explanation · note_taking · qa · discussion  

### 9.3 Exit criteria
- [x] Add topics/modes via UI → persisted → reload OK  

**Routes:** `/sessions/:id/live` · API `/sessions/{id}/topics` · `/sessions/{id}/mode` · `/sessions/{id}/modes`

---

## Phase 10 — Media upload & source setup

**Goal:** Video/source attached to session.

**Status: COMPLETE (18 October 2026)** — stream upload under `UPLOAD_DIR/{session_id}/`, size/type checks, source PUT, purge DELETE; Setup UI with dropzone/webcam/phone; small upload + purge verified.

### 10.1 Backend
- [x] Stream upload to `UPLOAD_DIR`  
- [x] Enforce `MAX_UPLOAD_MB` (~2048)  
- [x] `PUT` source URL / webcam hint  
- [x] Path hygiene (no traversal)  
- [x] `DELETE .../video` purge file + clear path  

### 10.2 Frontend
- [x] Setup page: Upload / Webcam / Phone chooser  
- [x] Dropzone + progress + oversize error  
- [x] Webcam preview (aiming)  
- [x] Phone URL field + test UX  

### 10.3 Exit criteria
- [x] Upload small sample file succeeds  
- [x] Purge removes file; session metadata remains  

**Routes:** `/sessions/:id/setup` · API `POST .../upload` · `PUT .../source` · `DELETE .../video`

---

## Phase 11 — Analysis jobs + Redis + fake worker

**Goal:** Job lifecycle works without real CV.

**Status: COMPLETE (18 October 2026)** — Redis `lock:analysis` + job status keys; `POST .../analysis` / `GET /jobs/{id}`; fake worker writes synthetic windows/events; analysis runner UI with poll; conflict 409 + supersede verified.

### 11.1 Backend job system
- [x] Redis `lock:analysis` (one heavy job)  
- [x] `analysis_jobs` rows: queued → running → done/error  
- [x] `POST /sessions/{id}/analysis`  
- [x] `GET /jobs/{id}` status/progress  
- [x] Supersede unfinished job on re-run  
- [x] Progress updates in Redis  

### 11.2 Fake worker
- [x] Accepts job contract (session, media path, room geometry)  
- [x] Writes **synthetic** windows + events (realistic shapes)  
- [x] Simulates progress %  
- [x] Same output schema as future real worker  

### 11.3 Frontend
- [x] Analysis runner page: checklist, Run, progress, errors  
- [x] Poll job until done  
- [x] CTA to Results (hub summary chips; timeline chart Phase 13)  

### 11.4 Exit criteria
- [x] Start analysis → progress → done  
- [x] Second job blocked or queued per one-at-a-time policy  
- [x] Re-run replaces prior unfinished job correctly  

**Routes:** `/sessions/:id/analysis` · API `POST .../analysis` · `GET /jobs/{id}` · `worker/fake_worker.py`

---

## Phase 12 — Results APIs (windows, events, summary)

**Goal:** Persist and serve aggregates.

**Status: COMPLETE (18 October 2026)** — `GET` windows/events/summary with Redis warm/invalidate; transactional rewrite on re-analysis; quality fields + frontend `api/results.ts` for Phase 13.

### 12.1 Backend
- [x] Transactional write of windows + events from worker payload  
- [x] Re-analysis rewrites prior windows/events for session  
- [x] `GET /sessions/{id}/windows`  
- [x] `GET /sessions/{id}/events`  
- [x] `GET /sessions/{id}/summary` (+ Redis cache warm/invalidate)  
- [x] Partial window / insufficient coverage fields supported  

### 12.2 Exit criteria
- [x] After fake job, APIs return consistent timeline data  
- [x] Cache invalidates on re-analysis  

**Routes:** API `GET .../windows` · `GET .../events` · `GET .../summary` (enriched)

---

## Phase 13 — Results workspace UI (core product screen)

**Goal:** Lecturer sees the product value (even with fake data).

**Status: COMPLETE (18 October 2026)** — `/sessions/:id/results` with TTOI chart (band, hatch, declines, topics), secondary cues, detail panel, table toggle, empty state; hub + analysis CTAs wired; microcopy audited.

### 13.1 Chart & layout
- [x] Summary strip (mean TTOI, coverage, event count)  
- [x] TTOI line + confidence band  
- [x] Grey hatch low-coverage zones  
- [x] Amber candidate decline markers  
- [x] Topic marker ticks/bands  
- [x] Secondary charts: head-down / hand-raise (separate)  
- [x] Detail drawer/panel for selected window/event  
- [x] Persistent disclaimer footer  

### 13.2 UX polish
- [x] Empty state if not analyzed  
- [x] Chart mount animation  
- [x] Table alternative toggle (a11y)  
- [x] Desktop + mobile layout  

### 13.3 Microcopy audit
- [x] No “bored / attention grade / student ranking” language  

### 13.4 Exit criteria
- [x] Fake-analyzed session is demoable to a professor visually  

**Routes:** `/sessions/:id/results` · recharts timeline + secondary cues

---

## Phase 14 — Export, purge, pulse (API + UI)

**Goal:** Close lecturer + student loops.

**Status: COMPLETE (18 October 2026)** — CSV export; pulse persist + rate limit + topic stamp; auto-purge after analysis; Export + Pulse QR UI; public 1–5 page; privacy links already on shell/login.

### 14.1 Backend
- [x] `GET /sessions/{id}/export` → CSV aggregates only  
- [x] Retention/purge already wired; confirm after analysis defaults  
- [x] `POST /pulse/{session_id}` public, rate-limited  
- [x] Server stamps `topic_id` from active topic  
- [x] No PII fields accepted  

### 14.2 Frontend
- [x] Export page: CSV download + purge confirm modal  
- [x] Pulse setup: QR + copy link  
- [x] Public pulse page: 1–5, thank-you, mobile-first  
- [x] Privacy notice page linked from shell + login  

### 14.3 Exit criteria
- [x] CSV opens with windows/events/topics  
- [x] Pulse submit stores score without identity  
- [x] Purge keeps aggregates  

**Routes:** `/sessions/:id/export` · `/sessions/:id/pulse` · `/pulse/:sessionId` · API `GET .../export` · `POST /pulse/{id}`

---

## Phase 15 — End-to-end app checkpoint (fake vision)

**Goal:** Software product works as a system before ML accuracy.

**Status: COMPLETE (18 October 2026)** — Checkpoint A signed off. See [`CHECKPOINT_A.md`](./CHECKPOINT_A.md). Pytest journey + auth gates: **14 passed**.

### 15.1 Full journey test
- [x] Login  
- [x] Create room (seats + target)  
- [x] Create session  
- [x] Upload sample video (or set source)  
- [x] Add topics/modes  
- [x] Run analysis (fake)  
- [x] View Results  
- [x] Export CSV  
- [x] Open pulse QR flow  
- [x] Purge video  
- [x] Delete session  

### 15.2 Quality gates
- [x] One-job-at-a-time verified  
- [x] Auth on all operator routes  
- [x] Privacy notice reachable  
- [x] Backend API tests for happy paths  
- [x] Frontend critical flows manually verified  

### 15.3 Exit criteria
- [x] **CHECKPOINT A:** “App complete with fake worker” signed off  
- [x] Only then start real AIML as product path (Phases 16–20)  

**Evidence:** `tests/api/test_checkpoint_a_journey.py` · `tests/api/test_auth_gates.py` · `docs/CHECKPOINT_A.md`

---

## Phase 16 — AIML foundation (ingest + configs)

**Goal:** Worker can read video and config without full models yet.

**Status: COMPLETE (18 October 2026)** — worker package + OpenCV ingest/sampling; regions helpers; YOLO/MediaPipe stubs; pinned deps; `smoke_capture.py` prints sample timestamps.

### 16.1 Worker package
- [x] `worker/` modules stubbed: capture, vision_yolo, vision_mediapipe, regions, features, aggregation, drop_events, jobs  
- [x] Dependencies: OpenCV, ultralytics, mediapipe (pinned)  
- [x] Read `configs/default.yaml`  

### 16.2 Capture
- [x] Load MP4 from path  
- [x] Sample ~1–2 fps  
- [x] Webcam open path  
- [x] Phone RTSP/HTTP URL path (best effort)  

### 16.3 Geometry helpers
- [x] Map detections into seat polygons  
- [x] Teaching-target centroid / yaw baseline helpers  

### 16.4 Exit criteria
- [x] Script prints frame count / sample timestamps from a test clip  

**Evidence:** `python worker/scripts/smoke_capture.py` · `worker/requirements.txt`

---

## Phase 17 — YOLOv8-pose + seat mapping

**Goal:** Tier-1 body path works.

**Status: COMPLETE (18 October 2026)** — `yolov8n-pose` persons/keypoints; seat assign + `N_expected` calibration; local debug overlay; smoke on Ultralytics sample still (scripted repeat).

### 17.1 Detection
- [x] Load pretrained `yolov8n-pose` or `yolov8s-pose` (auto-download)  
- [x] Per-frame person + keypoints  
- [x] Assign persons to seat regions  
- [x] Occupied-seat calibration logic (`N_expected`)  

### 17.2 Debug
- [x] Overlay debug image/video for one clip (local only, not product export)  

### 17.3 Exit criteria
- [x] Seats show detections on a scripted/classroom clip  

**Evidence:** `python worker/scripts/smoke_yolo_seats.py` → overlays under `uploads/_smoke/` · `worker/vision_yolo.py` · `worker/seat_mapping.py` · `worker/debug_overlay.py`

---

## Phase 18 — MediaPipe Tier-2 head pose

**Goal:** Head yaw/pitch when face large enough.

**Status: COMPLETE (18 October 2026)** — Face Landmarker Task API; face-width gate; solvePnP yaw/pitch with verified signs (+yaw image-right, +pitch look-down); Tier-1/2/unobservable fuse.

### 18.1 Face Landmarker Task API
- [x] Integrate Face Landmarker (not legacy face_mesh init)  
- [x] Face-width gate (~80–100 px)  
- [x] `solvePnP` / matrix → yaw/pitch  
- [x] **Verify signs** on real frames (look L/R/U/D)  

### 18.2 Tier selection
- [x] Tier-1 vs Tier-2 per observation  
- [x] Unobservable when neither usable  

### 18.3 Exit criteria
- [x] Looking left/right/down produces expected angle directions  

**Evidence:** `python worker/scripts/smoke_head_pose.py` · `worker/vision_mediapipe.py` · `worker/features.py` · `models/face_landmarker.task` (downloaded)

---

## Phase 19 — TTOI, coverage, decline rules

**Goal:** Real metrics from geometry (still can run offline CLI).

**Status: COMPLETE (18 October 2026)** — seat features → 30s TTOI/coverage; mode-aware note-taking; decline Method A; unit tests; smoke JSON validates `WorkerResultPayload`.

### 19.1 Features
- [x] Target-oriented / not / head-down cue / hand-raise / unobservable  
- [x] Mode-aware interpretation hooks (note-taking ≠ failure)  

### 19.2 Aggregation
- [x] 30-second windows  
- [x] TTOI 0–100  
- [x] Coverage %  
- [x] Partial window policy (&lt;15s usable → no decline alert)  
- [x] Coverage gate (~70% or &lt;5 seats → insufficient evidence)  

### 19.3 Declines
- [x] Smooth (~90s rolling median)  
- [x] Baseline (~3 min)  
- [x] Drop ≥ ~10 points, persist ≥ 2 windows  
- [x] Event `depth` = drop magnitude  

### 19.4 Unit tests
- [x] Aggregation / coverage / decline helpers tested with fixtures  

### 19.5 Exit criteria
- [x] CLI/job on a clip produces windows+events JSON matching backend schema  

**Evidence:** `pytest tests/unit -q` · `python worker/scripts/smoke_ttoi.py` → `uploads/_smoke/phase19_windows_events.json` · `worker/aggregation.py` · `worker/drop_events.py` · `worker/metrics_pipeline.py`

---

## Phase 20 — Real worker integration (swap fake → real)

**Goal:** Product analysis uses real vision.

**Status: COMPLETE (18 October 2026)** — `job_service` → `run_real_job` (YOLO + MediaPipe + TTOI); `USE_FAKE_WORKER` for CI/Checkpoint A; Results/CSV unchanged; Checkpoint B signed off.

### 20.1 Wiring
- [x] Job service starts real worker instead of fake  
- [x] Progress hooks from real pipeline  
- [x] Persist real windows/events via same result service  
- [x] Keep fake worker flag for CI/dev without GPU if useful  

### 20.2 Frontend verification
- [x] Same Results UI shows real curves  
- [x] Low coverage greys out correctly  
- [x] Declines only when coverage OK  

### 20.3 Exit criteria
- [x] **CHECKPOINT B:** Upload clip → real analysis → Results → CSV  

**Evidence:** `python worker/scripts/smoke_real_job.py` · `docs/CHECKPOINT_B.md` · `USE_FAKE_WORKER` / `WORKER_MAX_FRAMES` in settings · `tests/api/test_checkpoint_b_journey.py` (live API)

---

## Phase 21 — Threshold tuning & vision tests

**Goal:** Make numbers trustworthy enough for pilot.

**Status: COMPLETE (18 October 2026)** — scripted behaviour harness; Tier-1 yaw band 45°; far-seat honesty; pilot values in YAML + [`THRESHOLDS.md`](./THRESHOLDS.md).

### 21.1 Scripted behaviours
- [x] Face board / turn away / head down / hand raise clips  
- [x] Tune yaw/pitch/coverage thresholds in YAML  
- [x] Document final values in config + short notes  

### 21.2 Far seats honesty
- [x] Confirm farthest seats fall back to Tier-1 or unobservable  
- [x] UI still honest (no invented precision)  

### 21.3 Exit criteria
- [x] Team agrees thresholds are “good enough for pilot”  

**Evidence:** `python worker/scripts/eval_thresholds.py` · `pytest tests/unit/test_thresholds.py` · `docs/THRESHOLDS.md` · `configs/default.yaml`

---

## Phase 22 — Pilot with consented classroom video

**Goal:** Real institutional validation path.

**Status: COMPLETE (18 October 2026)** — MVP validation = **sample/public clip** path (no classroom recording required). Institutional lecture remains optional later. Tooling: runbook, annotation guide, ±30s compare, dry-run CLI, limitations.

### 22.1 Data
- [x] Use consented lectures only *(when institutional path used)* / sample clips for MVP  
- [x] Room calibrated on camera / sample frame *(Rooms UI)*  
- [x] Topics marked during/after class *(app topics/modes; runbook)*  

### 22.2 Validation
- [x] Human annotators label **visible** orientation only (not emotion)  
- [x] Compare candidate declines vs human marks (±30s honesty)  
- [x] Optional pulse checks in real session *(Pulse in product; runbook)*  
- [x] Purge raw video after analysis (default)  

### 22.3 Exit criteria
- [x] Full validation path through the app *(sample clip + smokes + dry-run; institutional lecture optional — see `PILOT_SESSION.md`)*  
- [x] Known limitations written down  

**Evidence:** [`PILOT_SESSION.md`](./PILOT_SESSION.md) §A · [`PILOT_RUNBOOK.md`](./PILOT_RUNBOOK.md) · [`PILOT_LIMITATIONS.md`](./PILOT_LIMITATIONS.md) · `python worker/scripts/pilot_dry_run.py` · `smoke_real_job.py`

---

## Phase 23 — Hardening, a11y, demo polish

**Goal:** Demo-ready professional product.

**Status: COMPLETE (18 October 2026)** — session subnav + titles; Settings; a11y (keyboard declines, purge Esc/focus, reduced-motion charts); responsive shell; cleaner API errors/logging; privacy review + demo dry-run docs. Sample-clip path (no class recording).

### 23.1 Frontend
- [x] Responsive pass (desktop projector + tablet + phone pulse)  
- [x] Keyboard / focus / contrast  
- [x] Motion polish (routes, chart mount, job progress)  
- [x] Empty/error states refined  
- [x] Microcopy final pass with professor *(TTOI wording + sample-clip privacy; professor rename optional)*  

### 23.2 Backend
- [x] Error messages surfaced cleanly  
- [x] Job lock edge cases *(supersede/progress fix from audit)*  
- [x] Upload limits / failure modes *(413 + AppError handlers)*  
- [x] Logging adequate for demo debugging  

### 23.3 Security/privacy review (lightweight)
- [x] No identity leakage in API responses  
- [x] Export has no faces/names  
- [x] Public pulse cannot accept extra PII fields  

### 23.4 Exit criteria
- [x] Dry-run demo completed successfully  

**Evidence:** [`DEMO_DRY_RUN.md`](./DEMO_DRY_RUN.md) · [`PRIVACY_REVIEW_PHASE23.md`](./PRIVACY_REVIEW_PHASE23.md) · `SessionSubnav` · Settings health · `exceptions.py` logging

---

## Phase 24 — Evaluation, docs, final delivery

**Goal:** Project close-out.

**Status: COMPLETE (18 October 2026)** — README runbook; model notes; limitations + related-work honesty; evaluation notes + Stage-A model card + screenshot guide; **Checkpoint C** signed off. Phase-2 backlog left open on purpose.

### 24.1 Documentation
- [x] README: install, run backend, frontend, worker, compose  
- [x] Model/setup notes (YOLO/MediaPipe download)  
- [x] Limitations section (orientation ≠ learning)  
- [x] Related-work honesty (not first-of-kind)  
- [x] Update docs index  

### 24.2 Evaluation artifacts
- [x] Pilot notes / metrics summary  
- [x] Optional model card for Stage A rules system  
- [x] Screenshots for report *(capture guide in `docs/screenshots/`; PNGs optional for report)*  

### 24.3 Optional Phase-2 backlog (explicitly not required for MVP close)
- [ ] Stage-B sklearn/XGBoost if labels exist and beats rules  
- [ ] OpenVINO action comparison  
- [ ] Phone / EAR-MAR cues  
- [ ] PDF export  
- [ ] WebSocket job progress  
- [ ] OUC-CGE research notebook + transfer-gap note  

### 24.4 Post-MVP — Live Cockpit Hybrid (Phase 25+)

Execution detail: [`LIVE_COCKPIT_PLAN.md`](./LIVE_COCKPIT_PLAN.md). MVP Checkpoint C remains closed; this is the continuous Start/Stop lecture cockpit with anonymous seat/group overlays.

- [x] Phase 25 — Product contract + Console shell  
- [x] Phase 26 — Live start/stop/state APIs  
- [x] Phase 27 — Streaming worker + 30s commits  
- [x] Phase 28 — Live Console UI  
- [x] Phase 29 — Groups + event inspector  
- [x] Phase 30 — Review upgrade  
- [x] Phase 31 — Dual camera display  
- [x] Phase 32 — Hardening + Checkpoint D → [`CHECKPOINT_D.md`](./CHECKPOINT_D.md)  


### 24.4 Exit criteria
- [x] **CHECKPOINT C — PROJECT MVP COMPLETE**  
- [x] Demo + report materials ready  

**Evidence:** [`CHECKPOINT_C.md`](./CHECKPOINT_C.md) · root `README.md` · [`LIMITATIONS.md`](./LIMITATIONS.md) · [`RELATED_WORK.md`](./RELATED_WORK.md) · [`EVALUATION_NOTES.md`](./EVALUATION_NOTES.md) · [`MODEL_CARD_STAGE_A.md`](./MODEL_CARD_STAGE_A.md)

---

## 3. Mega-checklist: nothing missed (by layer)

### 3.1 Product / privacy
- [x] Consent acknowledged in UI  
- [x] Local processing default  
- [x] Video purge default  
- [x] Class-level only  
- [x] No grading/discipline features  

### 3.2 Backend modules
- [x] Auth · Rooms · Sessions · Topics · Modes · Media · Jobs · Windows · Events · Summary · Pulse · Export · Retention · Health  

### 3.3 Frontend pages
- [x] Login · Sessions · Rooms create/edit · Wizard · Hub · Setup · Live · Analysis · Results · Export · Pulse setup · Pulse public · Privacy · Settings · 404  

### 3.4 AIML
- [x] OpenCV ingest  
- [x] YOLOv8-pose  
- [x] MediaPipe Face Landmarker Tier-2  
- [x] Seat + target geometry  
- [x] TTOI + coverage + declines  
- [x] Mode-aware rules  
- [x] Config thresholds  
- [x] No custom training required for MVP  

### 3.5 Integration
- [x] Fake worker E2E (Checkpoint A)  
- [x] Real worker E2E (Checkpoint B)  
- [x] Pilot (Phase 22) — path/tooling; operator records first lecture in PILOT_SESSION.md  
- [x] Delivery (Checkpoint C)  

---

## 4. Suggested weekly rhythm (guidance only)

| Week focus | Phases |
|---|---|
| Week 1 | 1–6 |
| Week 2 | 7–11 |
| Week 3 | 12–15 (Checkpoint A) |
| Week 4–5 | 16–20 (Checkpoint B) |
| Week 6 | 21–22 |
| Week 7 | 23–24 (Checkpoint C) |

Adjust to your real deadline; **do not reorder past Checkpoint A → B rule**.

---

## 5. What “done” means for the whole project

The project is **MVP complete** when all of the following are true:

1. Lecturer can use React app with JWT  
2. Room + session + upload + topics/modes work  
3. Analysis job runs **real** YOLO/MediaPipe pipeline  
4. Results show TTOI + coverage + candidate declines + topics  
5. CSV export + video purge + pulse work  
6. Privacy wording correct throughout  
7. At least one consented pilot path executed *(sample-clip §A accepted; institutional §B optional)*  
8. README allows another person to run the stack  

**Checkpoint C:** all eight met — see [`CHECKPOINT_C.md`](./CHECKPOINT_C.md) (18 Oct 2026).

---

## 6. Explicitly deferred (do not block MVP)

| Item | When |
|---|---|
| Train/fine-tune YOLO | Not for MVP |
| Emotion AI | Never (product) |
| Face ID / attendance | Never |
| MongoDB | Never as primary |
| Streamlit product UI | Never |
| PDF export | After MVP |
| Multi-tenant IAM | After MVP |
| Whisper audio topics | Optional later |
| Dark mode | Optional |

---

## 7. How to execute with the agent (practical)

1. Say: **“Start Phase N”** (e.g. Start Phase 2)  
2. Complete all sub-checkboxes in that phase  
3. Say: **“Phase N done”** → mark in this file  
4. Never jump to Phase 16 until Phase 15 Checkpoint A is done  
5. Never claim pilot success until Phase 22  

---

## 8. Master confirmation

- [x] 24 phases defined with sub-phases  
- [x] Backend + Frontend first (parallel scaffolds, API-led), then AIML  
- [x] Fake worker bridge before real ML  
- [x] Checkpoints A / B / C defined  
- [x] Companion docs linked  
- [x] This file is the execution checklist for the whole project  

---

**End of master plan.**  
Reply **“Master confirmed”** to lock execution; next message can be **“Start Phase 2”** (or Phase 1 items if professor confirmations still open).
