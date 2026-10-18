# Checkpoint B — Real worker E2E

| | |
|---|---|
| **Date** | 18 October 2026 |
| **Phase** | 20 — Real worker integration |
| **Status** | **SIGNED OFF** (offline real job + same Results/CSV contracts) |
| **Meaning** | Product analysis path uses YOLO + MediaPipe + TTOI rules behind the same job / Results / CSV surfaces as Checkpoint A |

---

## 20.1 Wiring (verified)

| Item | Evidence |
|---|---|
| Job service → real worker | `job_service` calls `worker.jobs.run_real_job` when `USE_FAKE_WORKER=false` |
| Progress hooks | Stages `ingest` → `vision` → `calibrate` → `aggregate` → `done` |
| Persist windows/events | Same `result_service.persist_and_warm` + `WorkerResultPayload` |
| Fake flag for CI | `USE_FAKE_WORKER=true` keeps Checkpoint A journey on synthetic TTOI |

## 20.2 Frontend (contract unchanged)

Results UI already charts class-level TTOI from the same window fields:

- Low coverage → grey hatch (`insufficient_coverage` / coverage &lt; threshold)
- Amber markers only when `candidate_decline` is true (declines suppressed when coverage/partial gates fail in `drop_events`)
- Export CSV uses aggregates only (no video paths)

No Results rewrite required for Phase 20 — real worker fills the same schema.

## 20.3 Journey

### Offline (always runnable)

```powershell
$env:PYTHONPATH = "D:\VIGILENS;D:\VIGILENS\backend"
python worker/scripts/smoke_real_job.py
```

Produces `uploads/_smoke/phase20_real_job.json` validated as `WorkerResultPayload`.

### Live API (optional, stack up)

1. Start API with **`USE_FAKE_WORKER=false`** (and optionally `WORKER_MAX_FRAMES=24` for short clips)
2. Login → room (seat boxes covering people) → session → **upload a real MP4**
3. Topics/modes → Run analysis → poll job to `done`
4. Results: windows present; low-evidence windows may show insufficient coverage (honest)
5. Export CSV → topics/windows/events rows

Checkpoint A journey (`tests/api/test_checkpoint_a_journey.py`) must run with **`USE_FAKE_WORKER=true`** because it uploads a non-decodable stub blob.

## Honesty note

Short public samples (e.g. bus still → clip) often yield `N_usable < 5` → `insufficient_coverage` and **no** decline events. That is correct product behaviour, not a regression. Classroom pilots (Phase 22) use consented lecture video with enough seats for TTOI.

## Sign-off

**CHECKPOINT B approved.** Real vision is behind the product analysis job. Threshold tuning remains Phase 21; institutional pilot is Phase 22 / Checkpoint C.
