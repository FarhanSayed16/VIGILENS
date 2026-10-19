# Checkpoint D — Live Cockpit Hybrid

| | |
|---|---|
| **Status** | Implemented (engineering sign-off) |
| **Date** | 19 October 2026 |
| **Plan** | [`LIVE_COCKPIT_PLAN.md`](./LIVE_COCKPIT_PLAN.md) |

## Exit criteria

- [x] Console is a **Lecture cockpit** with Start / Stop / Review  
- [x] `POST /sessions/{id}/live/start|stop` + `GET …/live/state`  
- [x] Streaming worker commits **30s windows** (append) + Redis live snapshot  
- [x] Live UI: preview (webcam), class TTOI/coverage, seat map, event feed  
- [x] Anonymous **groups** + event inspector feedback marks  
- [x] Review: heatmap for selected window + inspector  
- [x] Optional **secondary** source URL (display only)  
- [x] Privacy: no face embeddings / evidence crops; orientation ≠ attention  

## How to demo

1. Room with seats calibrated; session source = webcam  
2. Console → **Start lecture** (set `USE_FAKE_WORKER=true` for fast synthetic windows)  
3. Watch gauges / seat colors update as windows commit  
4. **Stop lecture** → open **Review**  
5. Optional: mark an event Useful / False alarm / Insufficient  

## Evidence

- APIs: `backend/app/api/live.py`, `backend/app/services/live_service.py`  
- Worker: `worker/live_session.py`, `worker/groups.py`  
- UI: `LectureCockpit.tsx`, `SessionHubPage.tsx`, Review heatmap  
- Tests: `tests/unit/test_groups.py`  
