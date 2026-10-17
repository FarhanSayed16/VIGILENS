# VIGILENS — Complete Backend Plan

| | |
|---|---|
| **Document status** | **Authoritative backend plan (no code)** |
| **Date** | 17 October 2026 |
| **Stack** | FastAPI · PostgreSQL · Redis · Python worker orchestration |
| **Companion docs** | `VIGILENS_COMPLETE_IDEA.md` (product truth) · `AIML_CONFIRMATION.md` (vision models) |
| **Next plans** | Frontend plan → Master plan (frontend + backend + AIML) |

> **Scope of this file:** everything the backend must own — folders, modules, services, APIs, data, jobs, privacy hooks.  
> **Not in this file:** React UI design, YOLO/MediaPipe internals (see AIML confirmation).  
> **No source code here** — structure, responsibilities, and implementation order only.

---

## 1. Backend purpose (one paragraph)

The backend is the **system of record and control plane** for VIGILENS. It authenticates the lecturer, stores room/session/topic/mode data, accepts video sources, starts and tracks analysis jobs, persists **class-level aggregates only** (windows + events), caches hot reads in Redis, exposes CSV export, and purges raw video after analysis. The vision worker does the heavy CV work; the backend **orchestrates**, **persists**, and **serves** results — it never stores faces, names, or per-student identity.

---

## 2. Locked backend stack

| Layer | Choice | Role |
|---|---|---|
| API framework | **FastAPI** (Python 3.10+) | REST (+ optional WebSocket later for job progress) |
| ORM / DB | **SQLAlchemy** + **Alembic** | Models + migrations |
| Primary DB | **PostgreSQL** | Sessions, windows, events, topics, pulse, jobs |
| Cache / job state | **Redis** | Job status, locks, summary/timeline cache |
| Auth | **JWT** (lecturer) | Protect all operator routes |
| Settings | **Pydantic Settings** + `.env` | Config / secrets |
| Validation / schemas | **Pydantic** request/response models | API contracts |
| Local infra | **docker-compose** | Postgres + Redis for dev |
| CV execution | **Python worker** (same repo) | Called/enqueued by backend; writes results back |

**Rejected for backend primary path:** MongoDB as main store · Streamlit as API · unbounded parallel GPU jobs · OAuth/multi-tenant IAM in MVP.

---

## 3. Repository placement (backend slice)

```text
vigilens/
├── docker-compose.yml                 # Postgres + Redis only (MVP)
├── .env.example
├── configs/                           # shared YAML (thresholds, defaults) — read by worker; backend may expose version
├── backend/
│   ├── requirements.txt
│   ├── alembic/                       # migrations
│   ├── alembic.ini
│   └── app/
│       ├── main.py                    # app factory, middleware, router mount
│       ├── api/                       # HTTP route modules (thin)
│       ├── core/                      # settings, auth, cors, logging, security
│       ├── db/                        # engine, session, SQLAlchemy models
│       ├── schemas/                   # Pydantic DTOs (request/response)
│       ├── cache/                     # Redis client + key helpers
│       ├── services/                  # business logic (thick)
│       ├── deps/                      # FastAPI dependencies (db, current user, redis)
│       └── utils/                     # small shared helpers (time, csv, paths)
├── worker/                            # CV pipeline (owned by AIML; backend integrates)
└── tests/
    ├── api/                           # route tests
    ├── services/                      # aggregation/export/job logic tests
    └── fixtures/                      # fake sessions, no real classroom video
```

**Boundary rule:**  
- `backend/app/**` = HTTP, auth, DB, cache, job control, export, purge.  
- `worker/**` = OpenCV, YOLO, MediaPipe, TTOI math.  
- Backend **must not** import Ultralytics/MediaPipe into request handlers. Worker integration is via a **job service** (in-process task for MVP, or background process with the same contract).

---

## 4. Feature modules (how the backend is divided)

Each module = **API routes + schemas + service + DB entities** for one domain.

| Module | Owns | Does not own |
|---|---|---|
| **Auth** | Login, JWT issue/verify, lecturer identity | Student accounts, OAuth |
| **Rooms** | Room configs, seat regions JSON, target ROI, camera defaults | Live drawing UI (frontend) |
| **Sessions** | Create/list/detail/delete session, source type, lifecycle status | Frame-by-frame CV |
| **Topics** | Topic markers (`start_sec`, label, optional end) | Auto topic from audio |
| **Modes** | Append teaching-mode changes over time | Interpreting modes in CV (worker reads them) |
| **Media / Upload** | Accept file upload, store path, size limits, source URL fields | Encoding/transcoding video |
| **Analysis Jobs** | Start/supersede job, lock, progress, errors, completion | YOLO inference |
| **Windows** | Serve persisted 30s aggregate timeline | Computing TTOI |
| **Events** | Serve candidate decline events | Deciding decline thresholds (worker) |
| **Summary** | Cached session summary for dashboard header | Chart rendering |
| **Pulse** | Public anonymous 1–5 submit; server stamps `topic_id` | Student identity |
| **Export** | CSV of aggregates | PDF (Phase 2) |
| **Retention / Purge** | Delete raw video; cascade session delete + cache invalidate | Long-term video archive |

---

## 5. Folder & file plan (what should exist — names only)

### 5.1 `backend/app/main.py`
- Create FastAPI app  
- Attach CORS, logging, exception handlers  
- Mount all API routers under a clear prefix (e.g. `/api` or root as locked in master later)  
- Health check route (`/health`) for Postgres + Redis reachability  

### 5.2 `backend/app/core/`
| File / unit | Responsibility |
|---|---|
| `settings` | `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `UPLOAD_DIR`, `MAX_UPLOAD_MB`, JWT expiry, model/config paths, CORS origins |
| `security` | Password verify (MVP: single lecturer creds from env), JWT create/decode |
| `cors` | Allowed origins (Vite `localhost:5173` in dev) |
| `logging` | Structured / consistent log format for API + job errors |
| `exceptions` | Domain errors mapped to HTTP status (not found, conflict, upload too large, job busy) |

### 5.3 `backend/app/db/`
| File / unit | Responsibility |
|---|---|
| `base` / `session` | Engine, session factory, request-scoped DB dependency |
| `models` (or split per table) | SQLAlchemy tables matching §6 below |
| Alembic migration `001_initial` | All MVP tables in one first migration |

### 5.4 `backend/app/schemas/`
One schema group per module: create / update / read / list / summary / job status / pulse submit / export metadata.  
**Rule:** API never returns raw filesystem paths that escape the upload root; never returns face crops or embeddings (none exist).

### 5.5 `backend/app/api/` (thin routers)
| Router | Endpoints (conceptual) |
|---|---|
| `auth` | Login |
| `rooms` | List / create / get / update |
| `sessions` | List / create / get / summary / delete |
| `topics` | Add topic to session |
| `modes` | Append mode change |
| `media` | Upload video / attach source URL / delete video |
| `analysis` | Start analysis; get job by id |
| `windows` | List windows for session |
| `events` | List events for session |
| `pulse` | Public submit |
| `export` | CSV download |
| `health` | Liveness / readiness |

### 5.6 `backend/app/services/` (thick logic)
| Service | Responsibility |
|---|---|
| `auth_service` | Authenticate lecturer; issue token |
| `room_service` | Validate seat polygons + target ROI shape; CRUD |
| `session_service` | Session lifecycle; status transitions; cascade delete |
| `topic_service` | Insert markers; resolve “active topic at time T” |
| `mode_service` | Append mode history; optional current-mode denormalize |
| `media_service` | Stream-to-disk upload; enforce `MAX_UPLOAD_MB`; path hygiene; purge file |
| `job_service` | Acquire Redis lock; create `analysis_jobs` row; start worker; update progress; supersede unfinished job; release lock |
| `result_service` | Persist windows/events from worker payload; invalidate caches |
| `summary_service` | Build/read cached summary (mean TTOI, coverage, event count) |
| `export_service` | Generate CSV from windows + events (+ topics) |
| `pulse_service` | Rate-limit; assign `topic_id` from active topic; store score only |
| `retention_service` | Purge video; honour privacy defaults |

### 5.7 `backend/app/cache/`
| Unit | Responsibility |
|---|---|
| Redis client wrapper | Connection from settings |
| Key helpers | `job:{id}:status`, `session:{id}:summary`, `session:{id}:windows`, `lock:analysis` |
| TTL / invalidate rules | On analysis complete, session delete, video purge |

### 5.8 `backend/app/deps/`
- Current lecturer (JWT required)  
- DB session  
- Redis client  
- Optional: “public pulse” dependency with rate limit  

---

## 6. Database plan (PostgreSQL)

### 6.1 Tables (MVP — locked)

| Table | Purpose | Key fields (logical) |
|---|---|---|
| `room_configs` | Reusable classroom geometry | name, seat_regions_json, target_roi_json, camera_defaults, created_at |
| `sessions` | One lecture recording/analysis unit | room_config_id, title, started_at, ended_at, source_type, status, video_path (nullable), created_at |
| `topics` | Manual topic markers | session_id, start_sec, end_sec, label |
| `mode_changes` | Teaching context over time | session_id, start_sec, mode |
| `windows` | 30-second class aggregates | session_id, time range, topic_id, teaching_mode, coverage, ttoi (+ band), secondary cues, data_quality_note, candidate_decline flag |
| `events` | Candidate orientation declines | session_id, time range, depth, coverage, topic_id, mode, note |
| `pulse_responses` | Anonymous 1–5 scores | session_id, topic_id (server-set), score, created_at — **no PII** |
| `analysis_jobs` | Job tracking | session_id, status, progress_pct, error_message, created_at, finished_at |

### 6.2 Enums / controlled values (conceptual)

| Field | Allowed values (MVP) |
|---|---|
| `sessions.source_type` | `upload` · `webcam` · `phone_rtsp` |
| `sessions.status` | e.g. `draft` · `ready` · `analyzing` · `complete` · `error` · `purged_video` |
| `mode_changes.mode` | `explanation` · `note_taking` · `qa` · `discussion` |
| `analysis_jobs.status` | `queued` · `running` · `done` · `error` · `cancelled` |
| `windows.data_quality_note` | null · `insufficient_coverage` · `partial_window` · … |

### 6.3 What must never be stored
- Face embeddings, face crops, student names, roll numbers, seat ↔ person identity history  
- Permanent raw video in DB (video is **disk temp** only)  
- Per-student scoreboards  

### 6.4 Relationships (logical)
- Room → many Sessions  
- Session → many Topics, ModeChanges, Windows, Events, PulseResponses, AnalysisJobs  
- Window/Event may reference Topic  
- Pulse gets `topic_id` from server at submit time  

### 6.5 Migrations
- Alembic as sole schema evolution path  
- First migration = full MVP schema  
- Seed optional: none required for MVP (lecturer creds from env)  

---

## 7. Redis plan

| Key pattern | Contents | Lifetime / rule |
|---|---|---|
| `lock:analysis` | Machine-wide single heavy job lock | Held while one job runs |
| `job:{job_id}:status` | status, progress %, error, session_id | Until done + short retain |
| `session:{id}:summary` | mean TTOI, coverage, event count, etc. | Invalidate on analysis rewrite / delete |
| `session:{id}:windows` | Optional hot timeline cache | Invalidate on analysis rewrite / delete |

**MVP policy:** one active heavy analysis job at a time per machine. Re-run for a session **cancels/supersedes** that session’s unfinished job.

---

## 8. Auth & security plan

| Topic | MVP approach |
|---|---|
| Who logs in | Single lecturer (or small shared) account |
| Credential store | Env-based username/password hash (no full user admin UI yet) |
| Token | JWT access token; protect all operator routes |
| Public routes | `POST /auth/login`, `POST /pulse/{session_id}`, `GET /health` |
| Pulse safety | No PII accepted; rate limit; only score + server-stamped topic |
| CORS | Vite origin in dev; same-origin / explicit list in production |
| Uploads | Size cap (~2 GB default); stream to disk; reject path traversal |
| Secrets | `.env` only; commit `.env.example` without secrets |

---

## 9. Complete API surface (backend contract)

### 9.1 Auth
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/login` | Public | Issue lecturer JWT |

### 9.2 Rooms
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/rooms` | JWT | List room configs |
| POST | `/rooms` | JWT | Create room (seats + target ROI) |
| GET | `/rooms/{id}` | JWT | Get room |
| PUT | `/rooms/{id}` | JWT | Update seats / target / camera defaults |

### 9.3 Sessions
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/sessions` | JWT | List sessions |
| POST | `/sessions` | JWT | Create session + source config |
| GET | `/sessions/{id}` | JWT | Session metadata |
| GET | `/sessions/{id}/summary` | JWT | Cached analytics summary |
| DELETE | `/sessions/{id}` | JWT | Delete session + derived rows + caches |

### 9.4 Topics & modes
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/sessions/{id}/topics` | JWT | Add topic marker |
| GET | `/sessions/{id}/topics` | JWT | List topics (needed by UI; include even if thin) |
| POST | `/sessions/{id}/mode` | JWT | Append mode change |

### 9.5 Media
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/sessions/{id}/upload` | JWT | Upload MP4/WebM (stream to `UPLOAD_DIR`) |
| PUT | `/sessions/{id}/source` | JWT | Set webcam device hint or phone RTSP/HTTP URL |
| DELETE | `/sessions/{id}/video` | JWT | Purge raw video; keep aggregates |

### 9.6 Analysis & results
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/sessions/{id}/analysis` | JWT | Start or supersede analysis job |
| GET | `/jobs/{id}` | JWT | Job status (Redis + DB) |
| GET | `/sessions/{id}/windows` | JWT | TTOI timeline |
| GET | `/sessions/{id}/events` | JWT | Candidate declines |

### 9.7 Pulse & export & health
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/pulse/{session_id}` | Public | Anonymous pulse 1–5 |
| GET | `/sessions/{id}/export` | JWT | CSV export |
| GET | `/health` | Public | API + DB + Redis check |

**API rules:**  
- Never expose permanent raw video streaming as a product feature.  
- Optional short-lived preview for webcam aiming is a frontend/device concern; backend stores path/URL only.  
- Job progress: polling `GET /jobs/{id}` for MVP; WebSocket optional later.

---

## 10. Analysis job lifecycle (backend responsibility)

```text
1. Lecturer: POST /sessions/{id}/analysis
2. Backend validates: session exists, source ready (file path or URL), room config present
3. Backend tries Redis lock:analysis
   - if busy → 409 Conflict (or queue message: one-at-a-time)
4. Create analysis_jobs row (queued); set session status analyzing
5. Invalidate old summary/windows cache for that session
6. Start worker with a job contract:
     session_id, job_id, video/source, room geometry, modes, topics, config thresholds
7. Worker reports progress → Redis (+ optional DB progress_pct)
8. On success:
     worker returns / writes windows + events
     backend result_service persists
     job → done; session → complete
     warm Redis summary (+ optional windows cache)
     release lock
9. On failure:
     job → error + error_message
     session → error
     release lock
10. Re-analysis:
     cancel/supersede unfinished job for that session
     replace windows/events for that session (transactional rewrite)
```

### Job contract (logical payload — no code)
**Input to worker:** session id, job id, media location, seat regions, target ROI, N_expected / calibration flags, mode timeline, topic timeline, YAML threshold version.  
**Output from worker:** list of window aggregates, list of decline events, optional calibration stats, data-quality notes.  
**Backend never receives:** face images, embeddings, student IDs.

---

## 11. Media & upload plan

| Concern | Rule |
|---|---|
| Max size | Default ~2048 MB; reject oversize early |
| Storage | Disk under `UPLOAD_DIR/{session_id}/…` only |
| Formats MVP | MP4 / WebM (extend later if needed) |
| Webcam / phone | Store source type + URL or device hint on session; worker opens capture |
| After analysis | Default purge raw file via retention service |
| Annotation hold | Optional longer keep only if explicitly approved (flag later) |

---

## 12. CSV export plan

Export must include **aggregates only**, suitable for lecturer reflection:

- Session metadata (title, times, room name)  
- Topics list  
- Windows: time, TTOI, coverage, quality notes, modes, secondary cue rates  
- Events: candidate declines with depth and linked topic  

**Exclude:** any path to raw video, any identity fields, any frame dumps.  
PDF export = Phase 2 (not backend MVP blocker).

---

## 13. Pulse-check plan (backend)

| Step | Behavior |
|---|---|
| Input | `session_id` + score 1–5 only |
| Auth | Public endpoint |
| Server action | Resolve active topic (`latest topic with start_sec <= now`); set `topic_id` (or null) |
| Store | score + timestamps + topic_id — nothing else |
| Abuse | Rate limit by IP / session |

---

## 14. Integration with AIML worker (backend view)

| Backend owns | Worker owns |
|---|---|
| Job create / lock / status API | Frame sampling |
| Passing room + session config | YOLO-pose + MediaPipe |
| Persisting windows/events | TTOI, coverage, declines |
| Cache + export + purge | Threshold application from `configs/` |

**MVP wiring style:** same machine; backend job service starts worker runnable (thread/process/background task). Same interfaces so a later queue (RQ/Celery) can replace the starter without changing API routes.

---

## 15. Config & environment plan

| Variable / config | Purpose |
|---|---|
| `DATABASE_URL` | Postgres |
| `REDIS_URL` | Redis |
| `SECRET_KEY` | JWT signing |
| `LECTURER_USERNAME` / password hash | MVP auth |
| `UPLOAD_DIR` | Temp video root |
| `MAX_UPLOAD_MB` | Upload cap |
| `CORS_ORIGINS` | Frontend origin list |
| `CONFIG_PATH` | Path to `configs/default.yaml` for worker |
| JWT expiry | Session length for lecturer token |

Commit **`.env.example`** with empty placeholders only.

---

## 16. Error handling & logging plan

| Case | Backend behavior |
|---|---|
| Unknown session/room | 404 |
| Job already running (global lock) | 409 |
| Upload too large / bad type | 413 / 400 |
| Analysis failure | Job `error` + `error_message` surfaced to UI via job status |
| Redis down | Health fails; prefer fail loud on job start rather than silent |
| Partial worker success | Do not mark done; do not leave half-written windows (transaction rewrite) |

Logs: request id optional; always log job start/finish/fail with `session_id` / `job_id`. Never log raw student imagery (none should flow through API).

---

## 17. Testing plan (backend)

| Layer | What to test |
|---|---|
| Unit — services | Topic active resolution; summary builder; export rows; purge deletes file + clears path; supersede job rules |
| Unit — schemas | Mode/source enums; pulse score bounds |
| API — TestClient | Auth required on protected routes; login issues token; rooms/sessions CRUD; pulse public; analysis creates job; export returns CSV content-type |
| Integration | Postgres + Redis via docker-compose in CI or local |
| Fixtures | Fake window/event JSON — **no real classroom video in git** |

Vision smoke tests live under worker/tests; backend only checks that **persisting a fake worker payload** works.

---

## 18. Privacy & retention (backend checklist)

1. Aggregates-first persistence  
2. Auto or explicit video purge after successful analysis  
3. Session delete cascades derived data + Redis keys  
4. Pulse has no identity fields in schema  
5. Export has no faces/names  
6. In-app purpose/retention copy is frontend; backend enforces retention actions  

---

## 19. Explicitly out of backend MVP

| Item | When / note |
|---|---|
| Multi-tenant orgs / many lecturer roles | Later |
| OAuth / SSO | Later |
| PDF export | Phase 2 |
| Chunked/resumable upload | Phase 2 if needed |
| WebSocket job stream | Optional after polling works |
| Audio / Whisper topic APIs | Off by default / later |
| MongoDB | Not used |
| Emotion / face-ID endpoints | Never |
| Storing permanent classroom video | Never (default) |

---

## 20. Backend implementation order (build sequence)

### Stage B0 — Scaffold
1. `backend/` package layout as in §3  
2. Settings + `.env.example`  
3. docker-compose Postgres + Redis  
4. Alembic + initial models  
5. Health + CORS + logging  
6. JWT login stub  

### Stage B1 — Core CRUD
1. Rooms CRUD (including JSON validation for seats/target)  
2. Sessions CRUD + source fields  
3. Topics + mode_changes  
4. Cascade delete + cache invalidate stubs  

### Stage B2 — Media
1. Upload streaming + size limits  
2. Source URL attachment for phone/webcam paths  
3. Delete video / purge path  

### Stage B3 — Jobs & results
1. Redis lock + job status keys  
2. `analysis_jobs` persistence  
3. Job service → worker contract (can start with **fake worker** writing sample windows)  
4. Windows + events read APIs  
5. Summary cache  
6. Real worker swap-in (AIML pipeline) without changing route shapes  

### Stage B4 — Lecturer deliverables
1. CSV export  
2. Pulse public endpoint + topic stamp + rate limit  
3. Harden errors, logging, tests  

### Stage B5 — Hardening
1. One-job-at-a-time edge cases  
2. Re-analysis rewrite correctness  
3. Retention defaults verified  
4. Ready for frontend integration  

---

## 21. Definition of done (backend MVP)

Backend MVP is done when:

1. Lecturer can log in with JWT  
2. Room + session + topics + modes can be stored and retrieved  
3. Video can be uploaded (or source set) under size limits  
4. Analysis job can be started, polled, and completes with windows + events in Postgres  
5. Summary endpoint works from Redis after completion  
6. CSV export downloads aggregates only  
7. Video purge removes file and clears path; aggregates remain  
8. Pulse accepts anonymous scores without PII  
9. Only one heavy job runs at a time  
10. Automated API tests cover auth + main happy paths  

*(Full YOLO accuracy is AIML done-ness, not backend done-ness — fake worker is acceptable until AIML Stage A lands.)*

---

## 22. How this connects to the other plans

| Plan | Relationship |
|---|---|
| **AIML confirmation** | Worker produces the payload backend persists |
| **Frontend plan** (next) | Consumes exactly the API surface in §9 |
| **Master plan** (last) | Merges frontend + backend + AIML into one execution timeline |

---

## 23. Confirmation checklist

- [x] FastAPI + PostgreSQL + Redis locked  
- [x] Module split: Auth, Rooms, Sessions, Topics, Modes, Media, Jobs, Windows, Events, Summary, Pulse, Export, Retention  
- [x] No identity / emotion / face storage  
- [x] One analysis job at a time  
- [x] CSV required; PDF deferred  
- [x] Worker is separate from request handlers  
- [x] This document is the backend plan to follow until the master plan supersedes scheduling only (not these contracts)

---

**End of backend plan.**  
Reply **“Backend confirmed”** when this matches what you want; next prompt can be the **complete frontend plan**.
