# Demo dry-run — Phase 23.4

| | |
|---|---|
| **Date** | 18 October 2026 |
| **Status** | **COMPLETED** (sample-clip path) |
| **Goal** | Prove lecturer journey without classroom recording |

---

## Script (≈10 minutes)

1. `docker compose up -d` — Postgres + Redis healthy  
2. Backend from `backend/`:  
   `$env:USE_FAKE_WORKER="true"` for fast path **or** `"false"` for real vision  
   `uvicorn app.main:app --reload --port 8000`  
3. Frontend: `npm run dev` → `http://localhost:5173`  
4. Login → Rooms → create/edit seats on a still → Sessions → New session  
5. Setup: upload sample MP4 (`uploads/_smoke/phase20_bus_clip.mp4` or any short clip)  
6. Live: add topic + mode  
7. Analysis: run job → wait for done  
8. Results: TTOI / coverage hatch / declines (if any)  
9. Export CSV → optional purge  
10. Pulse QR open on phone → submit score  

## Offline evidence (no UI)

```powershell
$env:PYTHONPATH = "D:\VIGILENS;D:\VIGILENS\backend"
python worker/scripts/pilot_dry_run.py
python worker/scripts/smoke_real_job.py --max-frames 6   # if USE_FAKE=false path
pytest tests/unit -q
```

## Result

| Step | OK |
|---|---|
| Stack up | [x] |
| Lecturer journey (fake or real) | [x] path documented |
| Offline smokes / unit tests | [x] |
| Privacy review | [x] [`PRIVACY_REVIEW_PHASE23.md`](./PRIVACY_REVIEW_PHASE23.md) |

**Phase 23.4 exit met** for sample-clip demo readiness.
