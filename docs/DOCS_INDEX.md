# VIGILENS — Documentation Index

| | |
|---|---|
| **Purpose** | Map of all planning docs and which one to open for what |
| **Date** | 17 October 2026 |
| **Execution entry point** | [`MASTER_PLAN.md`](./MASTER_PLAN.md) |

---

## Start here for building

| Priority | Document | Use it for |
|---|---|---|
| **1 — Execute** | [`MASTER_PLAN.md`](./MASTER_PLAN.md) | Phases 1–24, checklists, checkpoints A/B/C, build order |
| **1b — Phase 1 locks** | [`PHASE1_LOCKS.md`](./PHASE1_LOCKS.md) | Locked product/plan decisions (**Phase 1 complete**) |
| **2 — Product truth** | [`VIGILENS_COMPLETE_IDEA.md`](./VIGILENS_COMPLETE_IDEA.md) | What VIGILENS is/isn’t, TTOI, schema, API list, privacy |
| **3 — Backend detail** | [`BACKEND_PLAN.md`](./BACKEND_PLAN.md) | Modules, services, Redis, job lifecycle, folder plan |
| **4 — Frontend detail** | [`FRONTEND_PLAN.md`](./FRONTEND_PLAN.md) | Pages, theme, nav, components, motion |
| **5 — AIML detail** | [`AIML_CONFIRMATION.md`](./AIML_CONFIRMATION.md) | Models, tiers, training policy, what you must supply |

---

## Conflict rules

1. **Execution order** → `MASTER_PLAN.md` wins  
2. **Product meaning / metrics / privacy** → `VIGILENS_COMPLETE_IDEA.md` wins  
3. **Backend module contracts** → `BACKEND_PLAN.md`  
4. **UI/pages/theme** → `FRONTEND_PLAN.md`  
5. **Vision models** → `AIML_CONFIRMATION.md`  

---

## Locked build strategy (summary)

```text
Foundation → Backend + Frontend (with fake worker) → Checkpoint A
         → Real AIML (YOLO + MediaPipe + TTOI rules) → Checkpoint B
         → Pilot → Polish → Delivery → Checkpoint C
```

- Backend and frontend scaffolds can run **in parallel** early.  
- Real ML starts **after** the full app works with a fake worker.  

---

## Checkpoints

| ID | Meaning | Master phase |
|---|---|---|
| **A** | Full app E2E with fake vision | After Phase 15 |
| **B** | Real YOLO/MediaPipe analysis in the app | After Phase 20 |
| **C** | MVP complete (pilot + docs + demo) | After Phase 24 |

---

## How to work with the agent

1. Confirm plans if needed: *Master confirmed*  
2. Run: **Start Phase N**  
3. Finish that phase’s checkboxes  
4. Mark: **Phase N done**  
5. Do not skip Checkpoint A before AIML phases  

---

## Document status

| Doc | Status |
|---|---|
| Complete idea | Authoritative product |
| AIML confirmation | Locked |
| Backend plan | Locked |
| Frontend plan | Locked |
| Master plan | Locked for execution |
| Phase 1 locks | **Complete** (17 Oct 2026) |
| This index | Navigation aid |

## Execution progress

| Phase | Status |
|---|---|
| **1 — Lock decisions** | **DONE** |
| **2 — Monorepo foundation** | **DONE** (Compose runtime verify on home laptop) |
| **3 — Backend scaffold** | **DONE** |
| **4 — Frontend scaffold** | **DONE** |
| **5 — Database schema** | **DONE** (apply migration on home laptop with Postgres) |
| **6 — Auth & security** | **DONE** |
| **7 — Rooms** | **DONE** (UI persist needs Postgres) |
| **8 — Sessions** | Next |
| 9–24 | Pending |

**Docker:** `docker-compose.yml` is in the repo. On home laptop: `docker compose up -d` then `docker compose ps`.
