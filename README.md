# VIGILENS — A Clearer Lens on Learning
### Privacy-Preserving Classroom Engagement Trend Analyzer

> **One-line pitch:** A local, privacy-first computer-vision system that shows a lecturer *when* observable classroom engagement signals decline during a lecture, *how reliable* that reading is, and *which topic or slide* was being taught at that moment.

**Runtime targets:** Python **3.10+** · Node.js **18+**

---

## Documentation (start here)

| Doc | Purpose |
|---|---|
| [`docs/MASTER_PLAN.md`](docs/MASTER_PLAN.md) | **Execution checklist** — Phases 1–24 |
| [`docs/DOCS_INDEX.md`](docs/DOCS_INDEX.md) | Map of all planning docs |
| [`docs/PHASE1_LOCKS.md`](docs/PHASE1_LOCKS.md) | Locked product decisions (Phase 1 done) |
| [`docs/VIGILENS_COMPLETE_IDEA.md`](docs/VIGILENS_COMPLETE_IDEA.md) | Product truth (TTOI, schema, API, privacy) |
| [`docs/BACKEND_PLAN.md`](docs/BACKEND_PLAN.md) | Backend modules & contracts |
| [`docs/FRONTEND_PLAN.md`](docs/FRONTEND_PLAN.md) | Pages, theme, UI plan |
| [`docs/AIML_CONFIRMATION.md`](docs/AIML_CONFIRMATION.md) | Vision models & training policy |

**Current progress:** Phases 1–7 done · next = Phase 8 (sessions)

---

## Executive overview

**VIGILENS** is a reflective teaching tool: it analyses consented classroom video locally and produces an anonymous **class-level** timeline of observable orientation toward the teaching target (**TTOI**), with coverage/uncertainty and topic markers. It does **not** read minds, identify students, or grade anyone.

### Core philosophy

1. **Observable behaviour ≠ internal emotion** — looking down may be note-taking.
2. **Class-level aggregation only** — no individual scores, no face recognition, no permanent student tracking.
3. **Coverage first** — low evidence → “insufficient visual evidence,” not a fake score (~**70%** usable seats, tunable).
4. **Rule-based TTOI first** — ML only if it beats the baseline on held-out local sessions.
5. **Human validation** — annotator labelling + anonymous pulse checks.

---

## System architecture

```text
[ Laptop webcam / Mobile phone stream / Uploaded MP4 ]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ React Frontend (Vite)                                  │
└───────────────────────┬────────────────────────────────┘
                        │ REST
┌───────────────────────▼────────────────────────────────┐
│ FastAPI Backend                                        │
└───────────┬─────────────────────────┬──────────────────┘
            ▼                         ▼
┌──────────────────────┐   ┌────────────────────────────┐
│ PostgreSQL           │   │ Redis                      │
└──────────┬───────────┘   └────────────▲───────────────┘
           │                            │
           ▼                            │
┌────────────────────────────────────────────────────────┐
│ Vision Worker (YOLOv8-pose + MediaPipe Face Landmarker)│
└────────────────────────────────────────────────────────┘
```

**Locked stack:** FastAPI + React + PostgreSQL + Redis.  
**Locked vision:** pretrained YOLOv8-pose + MediaPipe Face Landmarker.  
**Thresholds start:** yaw **±30°**, pitch-down **~20°** (see `configs/default.yaml`).

---

## Repository layout (Phase 2)

```text
vigilens/
├── README.md
├── docker-compose.yml          # Postgres + Redis
├── .gitignore
├── .env.example
├── configs/
│   ├── default.yaml            # TTOI / coverage / decline thresholds
│   └── camera_room.yaml        # example room/camera hints
├── docs/                       # plans + locks
├── backend/                    # FastAPI (Phase 3+)
├── frontend/                   # React Vite (Phase 4+)
├── worker/                     # CV pipeline (Phase 11 / 16+)
├── tests/
├── models/                     # weights gitignored; README explains download
├── data/                       # sample aggregates only
├── notebooks/                  # optional research
└── uploads/                    # runtime video (gitignored)
```

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | **3.10+** | Backend + worker |
| Node.js | **18+** | Frontend |
| Docker Desktop / Engine | Latest | For Postgres + Redis via Compose |
| Git | any | |

**Docker note:** If Docker is not on this machine, still keep using `docker-compose.yml`. Run `docker compose up -d` on a machine that has Docker (e.g. home laptop) to verify Postgres + Redis are healthy.

---

## Quick start — infrastructure (Phase 2)

```bash
# From repo root
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
# Edit .env — at least POSTGRES_PASSWORD and SECRET_KEY

docker compose up -d
docker compose ps               # postgres + redis should be up/healthy
```

Stop:

```bash
docker compose down
```

### Backend (Phase 3+)

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# http://localhost:8000/health
```

### Frontend (Phase 4+)

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173  (scaffold login: any non-empty password)
```

---

## Privacy & DPDP

Designed to align with India’s **DPDP Act, 2023** / **DPDP Rules, 2025** where applicable — **confirm with the institution; this is not legal advice.**

- No face recognition or student IDs in storage  
- Local processing by default; purge raw video after analysis  
- Aggregates only retained by default  
- Not for grading, attendance, or discipline  
- Principal / Dean / student consents already obtained for this project  

---

## How to continue building

Follow [`docs/MASTER_PLAN.md`](docs/MASTER_PLAN.md) in order. Next: **Phase 3 — Backend scaffold**.
