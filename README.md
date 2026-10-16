# VIGILENS — A Clearer Lens on Learning
### Privacy-Preserving Classroom Engagement Trend Analyzer

> **One-line pitch:** A local, privacy-first computer-vision system that shows a lecturer *when* observable classroom engagement signals decline during a lecture, *how reliable* that reading is, and *which topic or slide* was being taught at that moment.

**Sole plan document:** [`docs/VIGILENS_COMPLETE_IDEA.md`](docs/VIGILENS_COMPLETE_IDEA.md)

**Runtime targets:** Python **3.10+** · Node.js **18+**

---

## Executive overview

**VIGILENS** is a reflective teaching tool: it analyses consented classroom video locally and produces an anonymous **class-level** timeline of observable orientation toward the teaching target (TTOI), with coverage/uncertainty and topic markers. It does **not** read minds, identify students, or grade anyone.

### Core philosophy

1. **Observable behaviour ≠ internal emotion** — looking down may be note-taking.
2. **Class-level aggregation only** — no individual scores, no face recognition, no permanent student tracking.
3. **Coverage first** — low evidence → “insufficient visual evidence,” not a fake score (~**70%** usable seats, tunable).
4. **Rule-based TTOI first** — ML only if it beats the baseline on held-out local sessions.
5. **Human validation** — double-**labelling** for annotator agreement + anonymous pulse checks (not “double-blind” clinical trials).

---

## System architecture

```text
[ Laptop webcam / Mobile phone stream / Uploaded MP4 ]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ React Frontend (Vite)                                  │
│  Session setup · ingest · topic markers · timeline UI  │
└───────────────────────┬────────────────────────────────┘
                        │ REST (+ WebSocket job progress)
┌───────────────────────▼────────────────────────────────┐
│ FastAPI Backend                                        │
│  Auth (lecturer JWT) · CORS · jobs · export            │
└───────────┬─────────────────────────┬──────────────────┘
            ▼                         ▼
┌──────────────────────┐   ┌────────────────────────────┐
│ PostgreSQL           │   │ Redis                      │
│ sessions · windows · │   │ job status · summaries     │
│ events · topics      │   │ timeline cache             │
└──────────┬───────────┘   └────────────▲───────────────┘
           │                            │
           ▼                            │
┌────────────────────────────────────────────────────────┐
│ Vision Worker                                          │
│  YOLOv8-pose + MediaPipe Face Landmarker (Tier-2)      │
│  Seat regions → TTOI / coverage → candidate declines   │
│  Writes Postgres; updates Redis progress               │
└────────────────────────────────────────────────────────┘
```

**Locked stack:** FastAPI + React + PostgreSQL + Redis (not Streamlit-as-product).  
**Locked vision:** pretrained YOLOv8-pose + MediaPipe **Face Landmarker** Task API.  
**Orientation start thresholds:** yaw **±30°**, pitch-down **~20°** (tune on pilot).

---

## Core metric: TTOI

**Teaching-Target Orientation Index** — share of usable seat observations oriented toward the configured teaching-target zone (usually the board/screen area).

- Every window reports **coverage**; below ~70% (or &lt;5 usable seats) → suppress decline alerts.
- In **Note-taking** mode, head-down is not treated as failure.
- Candidate declines = observable orientation change worth reviewing — not “students got bored.”

---

## Repository structure (target)

```text
vigilens/
├── README.md
├── docker-compose.yml              # Postgres + Redis
├── .gitignore
├── .env.example
├── docs/
│   └── VIGILENS_COMPLETE_IDEA.md   # ★ Sole project plan
├── backend/                        # FastAPI + Alembic + Redis
├── worker/                         # YOLO + MediaPipe pipeline
├── frontend/                       # React (Vite)
├── configs/                        # default.yaml, camera_room.yaml
├── notebooks/                      # OUC-CGE / evaluation notebooks
├── models/                         # pretrained weights (gitignored)
├── data/                           # sample aggregates only in git
└── tests/
```

---

## Quick start (after scaffold exists)

```bash
# 1. Infra
docker compose up -d

# 2. Backend (example)
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env   # or cp on Unix — set DATABASE_URL, REDIS_URL, SECRET_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd ../frontend
npm install
npm run dev
# Open http://localhost:5173  (API at http://localhost:8000)
```

Until the scaffold is created, follow the **First 7 days** checklist in the plan doc.

---

## Privacy & DPDP

Designed to align with India’s **DPDP Act, 2023** / **DPDP Rules, 2025** where applicable — **confirm with the institution; this is not legal advice.**

- No face recognition or student IDs in storage  
- Local processing by default; purge raw video after analysis  
- Aggregates only retained by default  
- Not for grading, attendance, or discipline  
- Principal / Dean / student consents already obtained for this project  

---

## Documentation

- **[Complete Idea & Final Plan](docs/VIGILENS_COMPLETE_IDEA.md)** — only plan file (architecture, schema, API, calculations, action plan, appendices).
