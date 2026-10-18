# VIGILENS audit — Phases 1–23

| | |
|---|---|
| **Date** | 18 October 2026 |
| **Scope** | Completeness & correctness vs [`MASTER_PLAN.md`](./MASTER_PLAN.md) through Phase 23 |
| **Method** | Plan checklists · code/route inventory · frontend pages · worker pipeline · tests · known bugs |
| **Purpose** | Single backlog of **required fixes and improvements** before demo / Phase 24 close-out |

---

## 1. Executive verdict

| Band | Verdict |
|---|---|
| **Phases 1–15 (app + Checkpoint A)** | **Substantially complete** — full lecturer journey with fake worker verified |
| **Phases 16–21 (AIML + thresholds)** | **Substantially complete** — real pipeline + smokes + unit tests |
| **Phase 20 / Checkpoint B** | **Tooling signed off** — real worker wired; short-clip honesty noted |
| **Phase 22 (pilot)** | **Path/tooling complete; institutional lecture not recorded** — [`PILOT_SESSION.md`](./PILOT_SESSION.md) still blank |
| **Phase 23 (hardening)** | **Not complete** — MASTER_PLAN §23 checkboxes still open; UI/API polish gaps remain |
| **Docs / README** | **Lagging** — root README still says “Phases 1–7”; mega-checklist mostly unchecked |

**Bottom line:** The product is **Checkpoint A/B–capable** and AIML is wired, but it is **not yet demo-hardened**. Treat Phase 23 + remaining open P1/P2 items below as the backlog before claiming “development complete through Phase 23.”

### Fix pass (18 Oct 2026 — Phase 23 deferred)

Implemented outside Phase 23 polish:

| ID | Status |
|---|---|
| P0-1 job supersede/progress race | **Fixed** |
| P0-2 Results event detail | **Fixed** |
| P0-3 fake-worker copy | **Fixed** |
| P0-4 README progress / TTOI pitch | **Fixed** |
| P1-1 public username hint | **Fixed** (removed; exposes `use_fake_worker` only) |
| P1-2 bcrypt-capable password | **Fixed** (bcrypt hash or plaintext) |
| P1-3 purge while analyzing | **Fixed** (409) |
| P1-4 pulse topic on upload | **Fixed** (no wall-clock stamp for upload) |
| P1-5 pulse rate-limit fail-closed | **Fixed** (503) |
| P1-6 model path vs CWD | **Fixed** (`resolve_model_path`) |
| P1-7 Tier-1 target-relative yaw' | **Fixed** |
| P1-8 full-frame face fallback | **Fixed** (crop only) |
| P1-9 calib horizon ~3 min | **Fixed** (`calibration.horizon_seconds`) |
| P1-10 compare_declines CSV | **Fixed** |
| P1-14 duplicate `tests/worker` | **Fixed** (removed) |
| P1-16 redact `source_url` creds | **Fixed** |
| P2-14 invent seat grid | **Fixed** (require room seats) |
| P2-17 worker README fake default | **Fixed** |
| P0-5 / Phase 23 / P1-11–13 / P1-15 | **Still open** (deferred) |

---

## 2. Phase-by-phase scorecard

| Phase | Plan status | Audit | Notes |
|---|---|---|---|
| 1 Locks | DONE | OK | [`PHASE1_LOCKS.md`](./PHASE1_LOCKS.md) |
| 2 Monorepo | DONE | OK | Compose Postgres/Redis |
| 3 Backend scaffold | DONE | OK | FastAPI + health |
| 4 Frontend scaffold | DONE | OK | Vite shell + theme |
| 5 Schema | DONE | OK | Alembic tables present |
| 6 Auth | DONE | OK w/ risks | Plaintext env password; public username hint |
| 7 Rooms | DONE | OK | Create/edit; no DELETE (acceptable) |
| 8 Sessions | DONE | OK | |
| 9 Topics/modes | DONE | OK | |
| 10 Media | DONE | OK w/ bugs | Purge-while-analyzing status gap |
| 11 Jobs + fake | DONE | OK w/ bugs | Supersede/progress race |
| 12 Results APIs | DONE | OK | |
| 13 Results UI | DONE | OK w/ bugs | Event detail panel logic |
| 14 Export/purge/pulse | DONE | OK w/ risks | Pulse rate-limit fail-open |
| 15 Checkpoint A | SIGNED OFF | OK | Needs `USE_FAKE_WORKER=true` |
| 16 AIML foundation | DONE | OK | |
| 17 YOLO + seats | DONE | OK | |
| 18 MediaPipe Tier-2 | DONE | OK | |
| 19 TTOI/declines | DONE | OK | |
| 20 Real worker | DONE / B signed | OK w/ gaps | Model path/CWD; Tier-1 facing |
| 21 Thresholds | DONE | OK | [`THRESHOLDS.md`](./THRESHOLDS.md) |
| 22 Pilot | DONE (path) | **Partial** | No filled `PILOT_SESSION.md` |
| 23 Hardening | **Next / open** | **Incomplete** | See §4 |

---

## 3. Required fixes (prioritized)

### P0 — Fix before demo / real analysis demos

| ID | Area | Issue | Where | Required fix |
|---|---|---|---|---|
| **P0-1** | Jobs | Supersede releases Redis lock while old worker thread may still run; `on_progress` can set a **cancelled** job back to `RUNNING`; late persist can race a newer job | `backend/app/services/job_service.py` | Ignore progress if job cancelled; refuse persist unless `job_id` still owns lock / is current; optionally join/stop old thread or use generation token |
| **P0-2** | Results UI | Clicking a decline also selects a window, so detail panel condition `selectedEvent && !selectedWindow` **never shows event detail** | `frontend/src/pages/results/ResultsPage.tsx` | Prefer event detail when an event is selected (or tab “Window / Event”) |
| **P0-3** | Copy | UI still says **“Fake worker”** after Phase 20 | `AnalysisRunnerPage.tsx` ~178; `SessionHubPage.tsx` ~203 | Reflect real/fake from `/health.use_fake_worker` or neutral “Analysis job” |
| **P0-4** | Docs | Root `README.md` claims **“Phases 1–7 · next Phase 8”** and engagement-heavy pitch | `README.md` | Bring install/run/progress in sync with Phases 1–22; keep TTOI wording (Phase 24 can finish, but progress line is misleading now) |
| **P0-5** | Phase 23 | Hardening **not executed** while claiming “up to Phase 23” | `MASTER_PLAN.md` §23 | Complete §23 checklist **or** explicitly mark Phase 23 incomplete in DOCS_INDEX |

### P1 — Should fix before pilot / Checkpoint C

| ID | Area | Issue | Where | Required fix |
|---|---|---|---|---|
| **P1-1** | Auth | `GET /auth/public-info` exposes `username_hint` = real lecturer username | `backend/app/api/auth.py` | Remove hint or return non-sensitive placeholder |
| **P1-2** | Auth | Lecturer password still plaintext env compare (plan mentioned hashing) | `backend/app/core/security.py` | Store hash (bcrypt/argon2) even for single-user MVP |
| **P1-3** | Media | Purge while `status=analyzing` clears file but can leave session stuck analyzing | `media_service.purge_video` | Block purge during analyzing **or** force status update + cancel job |
| **P1-4** | Pulse | Topic stamp uses wall-clock vs media timeline for upload sessions | `topic_service.elapsed_sec_for_session` | Document limitation; for upload mode prefer media-relative stamp or “no topic” |
| **P1-5** | Pulse | Rate limit **fail-open** if Redis down | `pulse_service.py` | Fail closed (503) when Redis unavailable |
| **P1-6** | Worker | Relative `yolov8n-pose.pt` / `models/face_landmarker.task` depend on **CWD** (API often started from `backend/`) | `configs/default.yaml`, `vision_*`, `jobs.py` | Resolve weights against repo root / `CONFIG_PATH` parent |
| **P1-7** | Worker | Tier-1 shoulder yaw **ignores teaching-target facing** (Tier-2 only) | `features.fuse_seat_feature` / Tier-1 path | Apply `yaw_relative_to_target` (or document as known limitation in THRESHOLDS) |
| **P1-8** | Worker | Full-frame MediaPipe fallback uses `face_index=0` — wrong face→seat risk | `features.py` | Disable full-frame fallback or match face to person bbox |
| **P1-9** | Worker | Calibration uses **all frames**; no manual `N_expected` override | `jobs.run_real_job`, seat_mapping | Optional calib window + room/session override field |
| **P1-10** | Pilot | `compare_declines.py` needs events **JSON**; product export is **CSV only** | export + runbook | Export events JSON endpoint **or** CSV→JSON helper in compare script |
| **P1-11** | Frontend | Session deep routes all titled **“Session hub”**; no session subnav | `AppShell.tsx` | Correct titles + Hub/Setup/Live/Analysis/Results/Export/Pulse subnav |
| **P1-12** | Frontend | Settings page is a stub | `SettingsPage.tsx` | Privacy link, version, logout, optional read-only thresholds |
| **P1-13** | Frontend | Decline list / table rows not keyboard-operable; purge modal no focus trap/Esc | Results + Export | a11y pass (Phase 23.1) |
| **P1-14** | Tests | Duplicate suites `tests/unit/*` and `tests/worker/*` (import shadowing risk) | `tests/worker/` | Delete or merge duplicates; keep one package |
| **P1-15** | Pilot | First consented lecture not recorded | `PILOT_SESSION.md` | Operator run + fill template (cannot be faked in git) |
| **P1-16** | Sessions API | `source_url` may leak RTSP credentials in `SessionRead` | `schemas/sessions.py` | Redact credentials in API responses |

### P2 — Improvements (demo polish / quality)

| ID | Area | Improvement |
|---|---|---|
| **P2-1** | Phase 23.1 | Responsive pass: projector Results density, tablet, phone pulse |
| **P2-2** | Phase 23.1 | Motion: chart mount respects `prefers-reduced-motion`; job progress polish |
| **P2-3** | Phase 23.1 | Empty/error states + ErrorBoundary |
| **P2-4** | Phase 23.1 | Microcopy final pass with professor (remove residual “engagement” ambiguity in README pitch) |
| **P2-5** | Phase 23.2 | Cleaner API error bodies; upload size/type failure UX |
| **P2-6** | Phase 23.2 | Job cancel endpoint; stuck-lock recovery documented/automated |
| **P2-7** | Phase 23.2 | Structured logging for demo debugging (job_id, session_id, stage) |
| **P2-8** | Phase 23.3 | Formal privacy review checklist sign-off (export columns, pulse `extra=forbid`, no identity fields) |
| **P2-9** | Phase 23.4 | Dry-run demo script + recorded pass |
| **P2-10** | Frontend | Login restore `location.state.from` after auth |
| **P2-11** | Frontend | Live page optional pulse QR peek |
| **P2-12** | Frontend | Colour not sole decline signal (icon/pattern on chart) |
| **P2-13** | Worker | `hand_raise_events` counts frames not discrete raises — debounce or rename |
| **P2-14** | Worker | Refuse invented seat grid when `seat_regions` empty (force room calibration) |
| **P2-15** | Docs | Update mega-checklist §3.1–3.3 in MASTER_PLAN to match reality |
| **P2-16** | Docs | Sync DOCS_INDEX Phase 23 status; link this audit |
| **P2-17** | Docs | Fix `worker/README.md` “backend default” fake-worker line |
| **P2-18** | CI | Add TestClient/unit API tests that don’t require manual uvicorn; run Checkpoint A/B with explicit env matrix |
| **P2-19** | Auth gates | Expand 401 tests to POST/PUT/DELETE operator routes |
| **P2-20** | Rooms | Empty-state CTA polish; optional room DELETE |

---

## 4. Phase 23 — incomplete checklist (explicit)

From [`MASTER_PLAN.md`](./MASTER_PLAN.md) §23 — **all still open in the plan**:

### 23.1 Frontend
- [ ] Responsive pass (desktop projector + tablet + phone pulse)  
- [ ] Keyboard / focus / contrast  
- [ ] Motion polish (routes, chart mount, job progress)  
- [ ] Empty/error states refined  
- [ ] Microcopy final pass with professor  

### 23.2 Backend
- [ ] Error messages surfaced cleanly  
- [ ] Job lock edge cases  
- [ ] Upload limits / failure modes  
- [ ] Logging adequate for demo debugging  

### 23.3 Security/privacy review (lightweight)
- [ ] No identity leakage in API responses  
- [ ] Export has no faces/names *(mostly true — re-verify & sign)*  
- [ ] Public pulse cannot accept extra PII fields *(coded `extra=forbid` — sign review)*  

### 23.4 Exit
- [ ] Dry-run demo completed successfully  

---

## 5. Risks (accept vs mitigate)

| Risk | Severity | Recommendation |
|---|---|---|
| Job supersede/progress race | **High** | Mitigate (P0-1) before multi-rerun demos |
| Claiming Phase 23 done without hardening | **High** | Complete Phase 23 or stop claiming it |
| No real lecture in `PILOT_SESSION.md` | **High** for academic claims | Do not claim classroom validation until filled |
| Model path/CWD failures on fresh machines | **Medium** | P1-6 |
| Far seats / &lt;5 usable → null TTOI looks “broken” | **Medium** | Demo script: calibrate ≥5 seats; explain honesty |
| Pulse spam if Redis down | **Medium** | P1-5 |
| Public username + default password | **Medium** | P1-1, P1-2; change defaults before any shared demo |
| Tier-1 not board-relative | **Medium** for accuracy | P1-7 or document in limitations |
| Wrong-face Tier-2 fallback | **Medium** | P1-8 |
| Dual Checkpoint A/B env mutual exclusion | **Low** | Document; separate processes or env matrix in CI |

---

## 6. What is already in good shape (do not rework)

- Class-level TTOI wording and Results disclaimer (not attention/emotion detector)  
- Coverage honesty (null TTOI, grey hatch, decline suppression)  
- Fake ↔ real same `WorkerResultPayload` contract  
- Pulse `extra=forbid`; CSV export without video paths  
- Worker smokes 16–21 + unit tests for aggregation/declines/thresholds/pilot match  
- Checkpoints A/B documentation and journey tests  
- Privacy strips on most key frontend pages  
- Consent acknowledgment on new session  

---

## 7. Recommended fix order

1. **P0-1** job race · **P0-2** event detail · **P0-3** fake-worker copy  
2. **P0-4 / P2-17** README + worker README honesty  
3. Execute **Phase 23** items (a11y, responsive, errors, privacy sign-off, dry-run demo) covering P1-11…P1-13 and P2-1…P2-9  
4. **P1-6** model paths · **P1-1/P1-2** auth hardening · **P1-3** purge-while-analyzing  
5. Worker accuracy items **P1-7, P1-8, P1-9** (or document as known limits)  
6. **P1-15** operator pilot lecture + fill `PILOT_SESSION.md`  
7. Then Phase 24 (Checkpoint C, final README, evaluation artifacts)

---

## 8. Definition of “caught up through Phase 23”

Treat Phases 1–23 as **actually complete** only when:

1. All **P0** items closed  
2. MASTER_PLAN §23 checkboxes verified and marked `[x]`  
3. Dry-run demo recorded (23.4)  
4. DOCS_INDEX / README progress lines match reality  
5. (`PILOT_SESSION.md` filled **or** explicitly deferred with no classroom-accuracy claims)

---

## 9. Out of scope for this audit (Phase 24 / deferred)

- Checkpoint C packaging  
- Stage-B classifier, OpenVINO, EAR/MAR, PDF, WebSockets  
- Multi-tenant IAM  
- Fine-tuning YOLO  

---

**End of audit.**  
Next step when you want implementation: say **“Fix P0 items”** or **“Start Phase 23”** (hardening pass using this backlog).
