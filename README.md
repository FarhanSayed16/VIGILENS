# VIGILENS — A Clearer Lens on Learning
### Privacy-Preserving Classroom Engagement Trend Analyzer

> **One-line pitch:** A local, privacy-first computer-vision system that shows a lecturer *when* class-level orientation toward the teaching target declines (TTOI), *how reliable* that reading is (coverage), and *which topic* was active — without identifying students or scoring individuals.

**MVP status:** Phases **1–24 complete** · Checkpoints **A / B / C** signed off  
**Runtime:** Python **3.10–3.12** (prefer **3.12**: `py -3.12 -m venv .venv`) · Node.js **18+** · Docker for Postgres + Redis  
**Avoid Python 3.14** — several pinned wheels fail to build.

---

## Documentation

| Doc | Purpose |
|---|---|
| [`docs/MASTER_PLAN.md`](docs/MASTER_PLAN.md) | Execution checklist (Phases 1–24) |
| [`docs/DOCS_INDEX.md`](docs/DOCS_INDEX.md) | Map of all docs |
| [`docs/CHECKPOINT_C.md`](docs/CHECKPOINT_C.md) | **MVP complete** sign-off |
| [`docs/DEMO_DRY_RUN.md`](docs/DEMO_DRY_RUN.md) | ~10 min sample-clip demo script |
| [`docs/VIGILENS_COMPLETE_IDEA.md`](docs/VIGILENS_COMPLETE_IDEA.md) | Product truth (TTOI, privacy, schema) |
| [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) | Orientation ≠ learning; honest constraints |
| [`docs/RELATED_WORK.md`](docs/RELATED_WORK.md) | Not first-of-kind — differentiation |
| [`docs/THRESHOLDS.md`](docs/THRESHOLDS.md) | Pilot-start vision thresholds |
| [`models/README.md`](models/README.md) | YOLO / MediaPipe download notes |

---

## What it is / is not

**Is:** Class-level **Teaching-Target Orientation Index (TTOI)** timeline + coverage gating + candidate declines + topics, from consented video processed **locally**.

**Is not:** Mind-reading, emotion AI, face recognition, attendance, grading, or a “first ever attention detector.” See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) and [`docs/RELATED_WORK.md`](docs/RELATED_WORK.md).

---

## Architecture

```text
[ Webcam / phone stream / uploaded MP4 ]
              │
              ▼
┌─────────────────────────────────────┐
│ React (Vite) — lecturer UI          │
└──────────────────┬──────────────────┘
                   │ REST + JWT
┌──────────────────▼──────────────────┐
│ FastAPI                             │
└────────┬─────────────────┬──────────┘
         ▼                 ▼
   PostgreSQL            Redis
         │                 ▲
         ▼                 │
┌─────────────────────────────────────┐
│ Worker: YOLOv8-pose + Face Landmarker│
│ → TTOI / coverage / declines         │
└─────────────────────────────────────┘
```

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | **3.10–3.12** (3.12 recommended) |
| Node.js | **18+** |
| Docker Desktop / Engine | for Postgres 16 + Redis 7 |
| Git | any |

---

## Quick start (full stack)

### 1. Clone & env

```powershell
# From repo root
copy .env.example .env
# Edit .env — set POSTGRES_PASSWORD, SECRET_KEY, LECTURER_PASSWORD
```

### 2. Infrastructure

```powershell
docker compose up -d
docker compose ps   # postgres + redis healthy
```

### 3. Backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head

# Fake worker = fast UI / Checkpoint A tests
$env:USE_FAKE_WORKER = "true"
# Real vision = product path (downloads models on first job)
# $env:USE_FAKE_WORKER = "false"
# $env:WORKER_MAX_FRAMES = "24"   # optional smoke cap

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: http://localhost:8000/health  
- OpenAPI: http://localhost:8000/docs  
- Default login: `lecturer` / `change_me` (from `.env`)

### 4. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 → login → Rooms → Sessions → Setup → Analysis → Results → Export / Pulse.

### 5. Worker (real vision / smokes)

```powershell
# Prefer same venv as backend, or a dedicated one at repo root
pip install -r worker/requirements.txt
$env:PYTHONPATH = "D:\VIGILENS;D:\VIGILENS\backend"
python worker/scripts/smoke_real_job.py
```

First real run downloads **YOLOv8-pose** weights and **MediaPipe Face Landmarker** (see [`models/README.md`](models/README.md)).

---

## Common workflows

| Goal | Flags / command |
|---|---|
| UI demo (no GPU) | `USE_FAKE_WORKER=true` + frontend |
| Real analysis | `USE_FAKE_WORKER=false` + short MP4 |
| Unit tests | `pytest tests/unit -q` (no API) |
| Checkpoint A API journey | API with fake worker → `pytest tests/api/test_checkpoint_a_journey.py -v` |
| Checkpoint B API journey | API with real worker + short clip → `pytest tests/api/test_checkpoint_b_journey.py -v` |
| Demo script | [`docs/DEMO_DRY_RUN.md`](docs/DEMO_DRY_RUN.md) |

Details: [`tests/README.md`](tests/README.md) · [`worker/README.md`](worker/README.md).

---

## Repository layout

```text
vigilens/
├── README.md
├── docker-compose.yml
├── .env.example
├── configs/default.yaml
├── docs/
├── backend/          # FastAPI + Alembic
├── frontend/         # React + Vite
├── worker/           # YOLO + MediaPipe + TTOI
├── tests/
├── models/           # weights gitignored
├── uploads/          # runtime video (gitignored)
└── data/
```

---

## Privacy

Designed to align with India’s **DPDP Act, 2023** where applicable — **not legal advice; confirm with the institution.**

- No face recognition / student IDs in storage  
- Local processing by default; purge raw video after analysis  
- Class-level aggregates only  
- Not for grading, attendance, or discipline  

Sign-off: [`docs/PRIVACY_REVIEW_PHASE23.md`](docs/PRIVACY_REVIEW_PHASE23.md).

---

## Limitations & related work (honesty)

- **Orientation ≠ learning / attention / emotion.** Coverage gates suppress fake confidence.  
- **Not first-of-kind** classroom CV — differentiation is TTOI + coverage + topics + privacy + local validation.  

Full notes: [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) · [`docs/RELATED_WORK.md`](docs/RELATED_WORK.md).

---

## License / academic use

Academic / institutional project under approved consent protocol. Do not deploy for discipline or grading.
