# Post–Checkpoint C hardening pass (18 Oct 2026)

Gap sweep after Phases 1–24. Fixes applied so local testing is less fragile.

## Fixed in this pass

| Area | Change |
|---|---|
| Frontend | `ErrorBoundary` around app |
| Frontend | 401 → `clearSession` notifies `RequireAuth` → redirect to login |
| Frontend | Analysis + Hub show fake vs real worker from `/health` |
| Frontend | Results table rows keyboard-operable |
| Frontend | Sessions filter-empty vs truly empty; rooms empty CTA |
| Backend | Block upload / source change while `analyzing` (same as purge) |
| Backend | Refresh analysis lock TTL on progress (long jobs) |
| Worker | Require teaching-target ROI for real jobs |
| Worker | YOLO weights download under `models/` (not API CWD) |
| Worker | `hand_raise_events` = rising-edge counts |
| Pilot | `compare_declines` accepts API `{items: [...]}` |

## Accepted residuals (do not block testing)

| Item | Notes |
|---|---|
| `USE_FAKE_WORKER` default `false` | Set `true` for Checkpoint A / fast UI (README) |
| No job cancel API | Re-run supersedes; Redis lock clears on finish |
| Institutional lecture `PILOT_SESSION.md` §B | Optional — sample path is MVP |
| Phase-2 backlog | PDF, WebSockets, Stage-B classifier, etc. |
| Purge modal focus trap | Escape + initial focus present |
| Screenshot PNGs | Capture guide only until demo |

## Suggested test order

1. `docker compose up -d`
2. `USE_FAKE_WORKER=true` + unit tests + Checkpoint A journey
3. Flip `USE_FAKE_WORKER=false` + short clip / Checkpoint B when ready
