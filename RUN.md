# VIGILENS — run commands

Use **three terminals** from `D:\VIGILENS`. PowerShell. Prefer **Python 3.12** (not 3.14).

| Terminal | What | URL |
|---|---|---|
| 1 | Docker: Postgres + Redis | — |
| 2 | Backend API (+ vision worker is started by the API) | http://localhost:8000/docs |
| 3 | Frontend | http://localhost:5173 |

Login: `lecturer` / `change_me` (from `.env`).

---

## First time only

```powershell
# Repo root
copy .env.example .env
# Optional: edit .env (POSTGRES_PASSWORD, SECRET_KEY, LECTURER_PASSWORD)

docker compose up -d

cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -r ..\worker\requirements.txt
alembic upgrade head
cd ..

cd frontend
npm install
cd ..
```

First real-vision run downloads YOLO + MediaPipe weights (see `models/README.md`).

---

## Every day — start the stack

### 1. Postgres + Redis

```powershell
cd D:\VIGILENS
docker compose up -d
docker compose ps
```

Both `vigilens-postgres` and `vigilens-redis` should be **healthy**.

### 2. Backend (keep this terminal open)

```powershell
cd D:\VIGILENS\backend
.\.venv\Scripts\activate

# Live lecture / real cameras (product path)
$env:USE_FAKE_WORKER = "false"
$env:PYTHONPATH = "D:\VIGILENS;D:\VIGILENS\backend"

# Fast UI demo without YOLO (optional instead of the two lines above)
# $env:USE_FAKE_WORKER = "true"

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

You do **not** start the worker in a fourth terminal. Start lecture on the UI; the API runs `worker/live_session.py`.

### 3. Frontend (keep this terminal open)

```powershell
cd D:\VIGILENS\frontend
npm run dev
```

Open http://localhost:5173 → login → Rooms → Sessions → **Start lecture** → Stop → Review.

---

## Stop

| What | Command |
|---|---|
| Backend / frontend | `Ctrl+C` in that terminal |
| Docker (keep data) | `docker compose stop` from repo root |
| Docker (wipe DB + Redis volumes) | `docker compose down -v` |

---

## After a reboot

```powershell
cd D:\VIGILENS
docker compose up -d
```

Then start backend (terminal 2) and frontend (terminal 3) as above.

If Postgres schema is missing after a wipe:

```powershell
cd D:\VIGILENS\backend
.\.venv\Scripts\activate
alembic upgrade head
```

---

## Modes

| Goal | Backend env |
|---|---|
| Live webcam + YOLO (classroom) | `USE_FAKE_WORKER=false` |
| Click through UI with fake numbers | `USE_FAKE_WORKER=true` |
| Cap frames on a short test | `$env:WORKER_MAX_FRAMES = "90"` |

---

## Optional worker smokes (repo root)

Only if you want to test vision without the UI. Use the **backend venv**.

```powershell
cd D:\VIGILENS
.\backend\.venv\Scripts\activate
$env:PYTHONPATH = "D:\VIGILENS;D:\VIGILENS\backend"

python worker\scripts\smoke_capture.py
python worker\scripts\smoke_yolo_seats.py
python worker\scripts\smoke_real_job.py
```

---

## If something fails

| Symptom | Fix |
|---|---|
| Backend cannot connect to Postgres / Redis | `docker compose up -d` then `docker compose ps` |
| `alembic` / import errors | Activate `backend\.venv` first |
| Camera locked / 0 people | Close other apps using the webcam; Start lecture again |
| Port 8000 or 5173 already in use | Stop the old process or change the port |
| Python wheels fail | Use 3.12: `py -3.12 -m venv backend\.venv` |

More detail: [README.md](README.md) · [worker/README.md](worker/README.md) · [docs/DEMO_DRY_RUN.md](docs/DEMO_DRY_RUN.md)
