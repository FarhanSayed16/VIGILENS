# Tests

Integration tests target a **running** stack (Postgres + Redis + `uvicorn` on port 8000).

## Setup

```bash
# from repo root, with backend venv active
pip install -r backend/requirements-dev.txt
# ensure API is up: uvicorn app.main:app --port 8000
```

## Run

```bash
cd D:\VIGILENS
$env:PYTHONPATH = "D:\VIGILENS;D:\VIGILENS\backend"   # PowerShell
pytest tests/unit -q    # Phase 19 aggregation / declines (no API)

# Checkpoint A journey — API must use fake worker:
#   $env:USE_FAKE_WORKER = "true"; uvicorn app.main:app --port 8000
pytest tests/api/test_checkpoint_a_journey.py -v

# Checkpoint B journey — API must use real worker:
#   $env:USE_FAKE_WORKER = "false"; $env:WORKER_MAX_FRAMES = "16"
pytest tests/api/test_checkpoint_b_journey.py -v
```

Optional: `VIGILENS_API_BASE=http://127.0.0.1:8000`

## Layout

| Path | Purpose |
|---|---|
| `tests/unit/test_aggregation.py` | TTOI / coverage / mode hooks |
| `tests/unit/test_drop_events.py` | Decline smooth / baseline / persist |
| `tests/unit/test_thresholds.py` | Phase 21 pilot threshold / honesty |
| `tests/unit/test_pilot_validation.py` | Phase 22 ±30s decline match |
| `tests/fixtures/pilot/` | Example human marks CSV (no video) |
| `tests/api/test_auth_gates.py` | Operator routes require JWT |
| `tests/api/test_checkpoint_a_journey.py` | Phase 15 full journey + one-job lock (`USE_FAKE_WORKER=true`) |
| `tests/api/test_checkpoint_b_journey.py` | Phase 20 real worker → Results → CSV (`USE_FAKE_WORKER=false`) |
| `tests/fixtures/` | Fake windows/events JSON only — **no real classroom video** |

Checkpoint sign-off: [`docs/CHECKPOINT_A.md`](../docs/CHECKPOINT_A.md).
