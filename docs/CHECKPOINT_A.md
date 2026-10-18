# Checkpoint A — App complete with fake worker

| | |
|---|---|
| **Date** | 18 October 2026 |
| **Phase** | 15 — End-to-end app checkpoint (fake vision) |
| **Status** | **SIGNED OFF** |
| **Meaning** | Lecturer journey works end-to-end with synthetic TTOI; ready for real AIML (Phases 16–20) without rewriting API/UI contracts |

---

## 15.1 Journey (verified)

Automated via `tests/api/test_checkpoint_a_journey.py` against live API + Postgres + Redis:

1. Login (JWT)  
2. Create room (seats + target ROI)  
3. Create session  
4. Upload sample MP4  
5. Add topics + teaching modes  
6. Run analysis (fake worker)  
7. Results: summary / windows / events  
8. Export CSV (topics + windows + events)  
9. Pulse public submit (score only; topic stamped)  
10. Purge video (or confirm auto-purge after analysis); aggregates kept  
11. Delete session  

## 15.2 Quality gates

| Gate | Evidence |
|---|---|
| One-job-at-a-time | Second `POST .../analysis` → **409** while lock held |
| Auth on operator routes | `tests/api/test_auth_gates.py` — protected paths → **401** |
| Privacy notice reachable | Frontend `/privacy` (public) + `/app/privacy` (shell); linked from login |
| Backend API happy paths | Pytest journey + auth gates (this checkpoint) |
| Frontend critical flows | Routes wired: login, rooms, sessions, setup, live, analysis, results, export, pulse QR, public pulse; production `npm run build` OK |

## Product surface (fake vision)

- Stack: FastAPI · React · PostgreSQL · Redis  
- Fake worker writes real `windows` / `events` rows  
- Results UI charts class-level TTOI (not attention / emotion / rankings)  
- Privacy default: purge raw video after analysis; CSV excludes identity and video paths  

## Sign-off

**CHECKPOINT A approved.** Phases 16–20 may begin (real AIML behind the same job contract).

Do **not** claim classroom accuracy or pilot success until later checkpoints (B / C).
