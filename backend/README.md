# Backend (FastAPI)

Lecturer API: auth, rooms, sessions, topics/modes, media, jobs, results, export, purge, pulse, retention, health.

## Run

```powershell
# Repo root once
copy .env.example .env

cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head   # Postgres must be up: docker compose up -d

# Fake worker for fast UI / Checkpoint A
$env:USE_FAKE_WORKER = "true"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  
- Login defaults: `LECTURER_USERNAME` / `LECTURER_PASSWORD` from `.env`

Set `USE_FAKE_WORKER=false` for real YOLO/MediaPipe jobs (install `worker/requirements.txt`; see root README).

## Layout

```text
backend/app/
├── main.py
├── api/          # routers
├── core/         # settings, security, exceptions
├── db/           # SQLAlchemy + Alembic
├── schemas/
├── services/
├── cache/        # Redis
└── deps/
```

Full stack: [../README.md](../README.md).
