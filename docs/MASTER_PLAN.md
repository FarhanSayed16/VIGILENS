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
- [ ] On **home laptop (Docker available):** `docker compose up` brings Postgres + Redis healthy *(do at home — not blocking)*  
- [x] On lab PC without Docker: Phase 2 still **done** once files/stubs exist; Compose verify deferred to home *(plan unchanged)*  

**Home laptop reminder:** `copy .env.example .env` → edit passwords → `docker compose up -d` → `docker compose ps` should show postgres + redis healthy.

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
- [ ] On **home laptop:** `alembic upgrade head` on fresh Postgres + tables visible *(deferred — no Docker here)*  

**Home reminder:** `docker compose up -d` → `cd backend` → `alembic upgrade head` → `\dt` in `psql`.

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
- [x] Create/list/update verified via API tests (SQLite override)  
- [ ] On home laptop with Postgres: create room in UI → list → reload persists  

**Routes:** `/rooms` · `/rooms/new` · `/rooms/:id/edit` · API `/rooms` (JWT)

---

## Phase 8 — Sessions (API + UI)

**Goal:** Lecture units exist.

### 8.1 Backend
- [ ] `GET/POST /sessions`, `GET/DELETE /sessions/{id}`  
- [ ] Source type: upload | webcam | phone_rtsp  
- [ ] Status field  
- [ ] Cascade delete + cache invalidate stubs  

### 8.2 Frontend
- [ ] Sessions home (list, filters, empty state)  
- [ ] New session wizard (title, room, source type, privacy banner)  
- [ ] Session hub (actions grid, honesty strip)  

### 8.3 Exit criteria
- [ ] Create session linked to room  
- [ ] Delete session removes it from list  

---

## Phase 9 — Topics & teaching modes

**Goal:** Timeline context without audio.

### 9.1 Backend
- [ ] `POST/GET /sessions/{id}/topics`  
- [ ] `POST /sessions/{id}/mode` → `mode_changes`  
- [ ] Helper: resolve active topic at time T (for pulse later)  

### 9.2 Frontend
- [ ] Live controls page (big New topic + mode switcher)  
- [ ] Topic list visible on session hub/results later  
- [ ] Modes: explanation · note_taking · qa · discussion  

### 9.3 Exit criteria
- [ ] Add topics/modes via UI → persisted → reload OK  

---

## Phase 10 — Media upload & source setup

**Goal:** Video/source attached to session.

### 10.1 Backend
- [ ] Stream upload to `UPLOAD_DIR`  
- [ ] Enforce `MAX_UPLOAD_MB` (~2048)  
- [ ] `PUT` source URL / webcam hint  
- [ ] Path hygiene (no traversal)  
- [ ] `DELETE .../video` purge file + clear path  

### 10.2 Frontend
- [ ] Setup page: Upload / Webcam / Phone chooser  
- [ ] Dropzone + progress + oversize error  
- [ ] Webcam preview (aiming)  
- [ ] Phone URL field + test UX  

### 10.3 Exit criteria
- [ ] Upload small sample file succeeds  
- [ ] Purge removes file; session metadata remains  

---

## Phase 11 — Analysis jobs + Redis + fake worker

**Goal:** Job lifecycle works without real CV.

### 11.1 Backend job system
- [ ] Redis `lock:analysis` (one heavy job)  
- [ ] `analysis_jobs` rows: queued → running → done/error  
- [ ] `POST /sessions/{id}/analysis`  
- [ ] `GET /jobs/{id}` status/progress  
- [ ] Supersede unfinished job on re-run  
- [ ] Progress updates in Redis  

### 11.2 Fake worker
- [ ] Accepts job contract (session, media path, room geometry)  
- [ ] Writes **synthetic** windows + events (realistic shapes)  
- [ ] Simulates progress %  
- [ ] Same output schema as future real worker  

### 11.3 Frontend
- [ ] Analysis runner page: checklist, Run, progress, errors  
- [ ] Poll job until done  
- [ ] CTA to Results  

### 11.4 Exit criteria
- [ ] Start analysis → progress → done  
- [ ] Second job blocked or queued per one-at-a-time policy  
- [ ] Re-run replaces prior unfinished job correctly  

---

## Phase 12 — Results APIs (windows, events, summary)

**Goal:** Persist and serve aggregates.

### 12.1 Backend
- [ ] Transactional write of windows + events from worker payload  
- [ ] Re-analysis rewrites prior windows/events for session  
- [ ] `GET /sessions/{id}/windows`  
- [ ] `GET /sessions/{id}/events`  
- [ ] `GET /sessions/{id}/summary` (+ Redis cache warm/invalidate)  
- [ ] Partial window / insufficient coverage fields supported  

### 12.2 Exit criteria
- [ ] After fake job, APIs return consistent timeline data  
- [ ] Cache invalidates on re-analysis  

---

## Phase 13 — Results workspace UI (core product screen)

**Goal:** Lecturer sees the product value (even with fake data).

### 13.1 Chart & layout
- [ ] Summary strip (mean TTOI, coverage, event count)  
- [ ] TTOI line + confidence band  
- [ ] Grey hatch low-coverage zones  
- [ ] Amber candidate decline markers  
- [ ] Topic marker ticks/bands  
- [ ] Secondary charts: head-down / hand-raise (separate)  
- [ ] Detail drawer/panel for selected window/event  
- [ ] Persistent disclaimer footer  

### 13.2 UX polish
- [ ] Empty state if not analyzed  
- [ ] Chart mount animation  
- [ ] Table alternative toggle (a11y)  
- [ ] Desktop + mobile layout  

### 13.3 Microcopy audit
- [ ] No “bored / attention grade / student ranking” language  

### 13.4 Exit criteria
- [ ] Fake-analyzed session is demoable to a professor visually  

---

## Phase 14 — Export, purge, pulse (API + UI)

**Goal:** Close lecturer + student loops.

### 14.1 Backend
- [ ] `GET /sessions/{id}/export` → CSV aggregates only  
- [ ] Retention/purge already wired; confirm after analysis defaults  
- [ ] `POST /pulse/{session_id}` public, rate-limited  
- [ ] Server stamps `topic_id` from active topic  
- [ ] No PII fields accepted  

### 14.2 Frontend
- [ ] Export page: CSV download + purge confirm modal  
- [ ] Pulse setup: QR + copy link  
- [ ] Public pulse page: 1–5, thank-you, mobile-first  
- [ ] Privacy notice page linked from shell + login  

### 14.3 Exit criteria
- [ ] CSV opens with windows/events/topics  
- [ ] Pulse submit stores score without identity  
- [ ] Purge keeps aggregates  

---

## Phase 15 — End-to-end app checkpoint (fake vision)

**Goal:** Software product works as a system before ML accuracy.

### 15.1 Full journey test
- [ ] Login  
- [ ] Create room (seats + target)  
- [ ] Create session  
- [ ] Upload sample video (or set source)  
- [ ] Add topics/modes  
- [ ] Run analysis (fake)  
- [ ] View Results  
- [ ] Export CSV  
- [ ] Open pulse QR flow  
- [ ] Purge video  
- [ ] Delete session  

### 15.2 Quality gates
- [ ] One-job-at-a-time verified  
- [ ] Auth on all operator routes  
- [ ] Privacy notice reachable  
- [ ] Backend API tests for happy paths  
- [ ] Frontend critical flows manually verified  

### 15.3 Exit criteria
- [ ] **CHECKPOINT A:** “App complete with fake worker” signed off  
- [ ] Only then start real AIML as product path (Phases 16–20)  

---

## Phase 16 — AIML foundation (ingest + configs)

**Goal:** Worker can read video and config without full models yet.

### 16.1 Worker package
- [ ] `worker/` modules stubbed: capture, vision_yolo, vision_mediapipe, regions, features, aggregation, drop_events, jobs  
- [ ] Dependencies: OpenCV, ultralytics, mediapipe (pinned)  
- [ ] Read `configs/default.yaml`  

### 16.2 Capture
- [ ] Load MP4 from path  
- [ ] Sample ~1–2 fps  
- [ ] Webcam open path  
- [ ] Phone RTSP/HTTP URL path (best effort)  

### 16.3 Geometry helpers
- [ ] Map detections into seat polygons  
- [ ] Teaching-target centroid / yaw baseline helpers  

### 16.4 Exit criteria
- [ ] Script prints frame count / sample timestamps from a test clip  

---

## Phase 17 — YOLOv8-pose + seat mapping

**Goal:** Tier-1 body path works.

### 17.1 Detection
- [ ] Load pretrained `yolov8n-pose` or `yolov8s-pose` (auto-download)  
- [ ] Per-frame person + keypoints  
- [ ] Assign persons to seat regions  
- [ ] Occupied-seat calibration logic (`N_expected`)  

### 17.2 Debug
- [ ] Overlay debug image/video for one clip (local only, not product export)  

### 17.3 Exit criteria
- [ ] Seats show detections on a scripted/classroom clip  

---

## Phase 18 — MediaPipe Tier-2 head pose

**Goal:** Head yaw/pitch when face large enough.

### 18.1 Face Landmarker Task API
- [ ] Integrate Face Landmarker (not legacy face_mesh init)  
- [ ] Face-width gate (~80–100 px)  
- [ ] `solvePnP` / matrix → yaw/pitch  
- [ ] **Verify signs** on real frames (look L/R/U/D)  

### 18.2 Tier selection
- [ ] Tier-1 vs Tier-2 per observation  
- [ ] Unobservable when neither usable  

### 18.3 Exit criteria
- [ ] Looking left/right/down produces expected angle directions  

---

## Phase 19 — TTOI, coverage, decline rules

**Goal:** Real metrics from geometry (still can run offline CLI).

### 19.1 Features
- [ ] Target-oriented / not / head-down cue / hand-raise / unobservable  
- [ ] Mode-aware interpretation hooks (note-taking ≠ failure)  

### 19.2 Aggregation
- [ ] 30-second windows  
- [ ] TTOI 0–100  
- [ ] Coverage %  
- [ ] Partial window policy (&lt;15s usable → no decline alert)  
- [ ] Coverage gate (~70% or &lt;5 seats → insufficient evidence)  

### 19.3 Declines
- [ ] Smooth (~90s rolling median)  
- [ ] Baseline (~3 min)  
- [ ] Drop ≥ ~10 points, persist ≥ 2 windows  
- [ ] Event `depth` = drop magnitude  

### 19.4 Unit tests
- [ ] Aggregation / coverage / decline helpers tested with fixtures  

### 19.5 Exit criteria
- [ ] CLI/job on a clip produces windows+events JSON matching backend schema  

---

## Phase 20 — Real worker integration (swap fake → real)

**Goal:** Product analysis uses real vision.

### 20.1 Wiring
- [ ] Job service starts real worker instead of fake  
- [ ] Progress hooks from real pipeline  
- [ ] Persist real windows/events via same result service  
- [ ] Keep fake worker flag for CI/dev without GPU if useful  

### 20.2 Frontend verification
- [ ] Same Results UI shows real curves  
- [ ] Low coverage greys out correctly  
- [ ] Declines only when coverage OK  

### 20.3 Exit criteria
- [ ] **CHECKPOINT B:** Upload clip → real analysis → Results → CSV  

---

## Phase 21 — Threshold tuning & vision tests

**Goal:** Make numbers trustworthy enough for pilot.

### 21.1 Scripted behaviours
- [ ] Face board / turn away / head down / hand raise clips  
- [ ] Tune yaw/pitch/coverage thresholds in YAML  
- [ ] Document final values in config + short notes  

### 21.2 Far seats honesty
- [ ] Confirm farthest seats fall back to Tier-1 or unobservable  
- [ ] UI still honest (no invented precision)  

### 21.3 Exit criteria
- [ ] Team agrees thresholds are “good enough for pilot”  

---

## Phase 22 — Pilot with consented classroom video

**Goal:** Real institutional validation path.

### 22.1 Data
- [ ] Use consented lectures only  
- [ ] Room calibrated on real camera placement  
- [ ] Topics marked during/after class  

### 22.2 Validation
- [ ] Human annotators label **visible** orientation only (not emotion)  
- [ ] Compare candidate declines vs human marks (±30s honesty)  
- [ ] Optional pulse checks in real session  
- [ ] Purge raw video after analysis (default)  

### 22.3 Exit criteria
- [ ] At least one full real lecture through the app  
- [ ] Known limitations written down  

---

## Phase 23 — Hardening, a11y, demo polish

**Goal:** Demo-ready professional product.

### 23.1 Frontend
- [ ] Responsive pass (desktop projector + tablet + phone pulse)  
- [ ] Keyboard / focus / contrast  
- [ ] Motion polish (routes, chart mount, job progress)  
- [ ] Empty/error states refined  
- [ ] Microcopy final pass with professor  

### 23.2 Backend
- [ ] Error messages surfaced cleanly  
- [ ] Job lock edge cases  
- [ ] Upload limits / failure modes  
- [ ] Logging adequate for demo debugging  

### 23.3 Security/privacy review (lightweight)
- [ ] No identity leakage in API responses  
- [ ] Export has no faces/names  
- [ ] Public pulse cannot accept extra PII fields  

### 23.4 Exit criteria
- [ ] Dry-run demo completed successfully  

---

## Phase 24 — Evaluation, docs, final delivery

**Goal:** Project close-out.

### 24.1 Documentation
- [ ] README: install, run backend, frontend, worker, compose  
- [ ] Model/setup notes (YOLO/MediaPipe download)  
- [ ] Limitations section (orientation ≠ learning)  
- [ ] Related-work honesty (not first-of-kind)  
- [ ] Update docs index  

### 24.2 Evaluation artifacts
- [ ] Pilot notes / metrics summary  
- [ ] Optional model card for Stage A rules system  
- [ ] Screenshots for report  

### 24.3 Optional Phase-2 backlog (explicitly not required for MVP close)
- [ ] Stage-B sklearn/XGBoost if labels exist and beats rules  
- [ ] OpenVINO action comparison  
- [ ] Phone / EAR-MAR cues  
- [ ] PDF export  
- [ ] WebSocket job progress  
- [ ] OUC-CGE research notebook + transfer-gap note  

### 24.4 Exit criteria
- [ ] **CHECKPOINT C — PROJECT MVP COMPLETE**  
- [ ] Demo + report materials ready  

---

## 3. Mega-checklist: nothing missed (by layer)

### 3.1 Product / privacy
- [ ] Consent acknowledged in UI  
- [ ] Local processing default  
- [ ] Video purge default  
- [ ] Class-level only  
- [ ] No grading/discipline features  

### 3.2 Backend modules
- [ ] Auth · Rooms · Sessions · Topics · Modes · Media · Jobs · Windows · Events · Summary · Pulse · Export · Retention · Health  

### 3.3 Frontend pages
- [ ] Login · Sessions · Rooms create/edit · Wizard · Hub · Setup · Live · Analysis · Results · Export · Pulse setup · Pulse public · Privacy · Settings · 404  

### 3.4 AIML
- [ ] OpenCV ingest  
- [ ] YOLOv8-pose  
- [ ] MediaPipe Face Landmarker Tier-2  
- [ ] Seat + target geometry  
- [ ] TTOI + coverage + declines  
- [ ] Mode-aware rules  
- [ ] Config thresholds  
- [ ] No custom training required for MVP  

### 3.5 Integration
- [ ] Fake worker E2E (Checkpoint A)  
- [ ] Real worker E2E (Checkpoint B)  
- [ ] Pilot (Phase 22)  
- [ ] Delivery (Checkpoint C)  

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
7. At least one consented pilot path executed  
8. README allows another person to run the stack  

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
