# Backend (FastAPI)

Phase **3** scaffold is in place. Domain APIs land in later phases.

## Layout

```text
backend/
├── requirements.txt
├── README.md
└── app/
    ├── main.py              # create_app() + uvicorn target
    ├── api/                 # routers (health now; auth/rooms/… later)
    ├── core/                # settings, logging, CORS, exceptions
    ├── db/                  # Phase 5 — SQLAlchemy + Alembic
    ├── schemas/             # Phase 6+
    ├── cache/               # Phase 11 — Redis helpers
    ├── services/            # Phase 6+
    ├── deps/                # Phase 5/6
    └── utils/
```

## Run (from `backend/`)

```bash
# From repo root — once
copy .env.example .env

cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

`database` / `redis` in health may show `unavailable` until Docker Compose is running (OK for Phase 3).

## Database (Phase 5)

Models live in `app/db/`. Enums documented in `docs/SCHEMA_ENUMS.md`.

```bash
# With Postgres running (docker compose up -d from repo root):
cd backend
.\.venv\Scripts\activate
alembic upgrade head
alembic current
```

Without Docker on this machine, migration file still exists (`alembic/versions/001_initial_schema.py`); apply on home laptop after Compose is up.

## Auth (Phase 6)

| Route | Auth | Notes |
|---|---|---|
| `POST /auth/login` | Public | Body: `{ username, password }` → JWT |
| `GET /auth/me` | Bearer JWT | Lecturer identity |
| `POST /pulse/{session_id}` | Public | Stub until Phase 14 |
| `GET /health` | Public | Soft DB/Redis checks |

Defaults: `lecturer` / `change_me` (override in `.env`).

## Rooms (Phase 7)

JWT-protected: `GET/POST /rooms`, `GET/PUT /rooms/{id}`  
Seat/target geometry: normalized box (or polygon) regions in `[0,1]`.

## Next

- **Phase 8** — Sessions API + UI  



