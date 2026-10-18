# Pilot runbook — consented classroom lecture (Phase 22)

| | |
|---|---|
| **Consent** | Principal, Dean, and student consents already obtained (project fact) |
| **Rule** | Use **only** lectures under that protocol. **Never** commit classroom video to git |
| **Default retention** | Analyse → keep aggregates → **purge raw video** |

---

## Before class

1. Confirm consent covers this session (existing institutional protocol).  
2. Create / open a **Room** in the app; draw seats + teaching-target ROI on a still from the **real camera** placement.  
3. Save room; note camera height/angle in room notes if useful.  
4. Create a **Session** linked to that room; acknowledge privacy banner.  
5. Prefer **upload** of a recorded lecture, or live webcam/phone if stable.

## During / after class

6. Mark **topics** (start/end) during or after class.  
7. Mark **teaching modes** (explanation / note_taking / qa / …) — note_taking must not be scored as failure.  
8. Optional: open **Pulse** QR for anonymous student checks (score only; no PII).

## Analysis

9. Start analysis with `USE_FAKE_WORKER=false` (real YOLO + MediaPipe).  
10. Wait for job `done`. Review **Results**: TTOI, coverage hatch, candidate declines.  
11. **Export CSV** (aggregates only).  
12. Confirm video **purged** (auto after analysis, or manual on Export page). Aggregates remain.

## Human validation (visible orientation only)

13. If annotation is needed **before** purge, export a short working copy offline (not in git), then purge.  
14. Annotators watch video and fill CSV marks — see [`annotation/ORIENTATION_LABELS.md`](./annotation/ORIENTATION_LABELS.md).  
   - Label **visible** orientation clusters / declines only.  
   - **Forbidden:** bored, distracted, lazy, emotion words.  
15. Compare machine events to human marks (±30 s):

```powershell
$env:PYTHONPATH = "D:\VIGILENS"
python worker/scripts/compare_declines.py `
  --human path\to\human_marks.csv `
  --machine path\to\session_events.json `
  --tolerance 30 `
  --out uploads\_smoke\pilot_compare.json
```

16. Record the session in [`PILOT_SESSION.md`](./PILOT_SESSION.md).  
17. Read [`PILOT_LIMITATIONS.md`](./PILOT_LIMITATIONS.md) — update if new issues appear.

## Tooling dry-run (no classroom video)

```powershell
$env:PYTHONPATH = "D:\VIGILENS;D:\VIGILENS\backend"
python worker/scripts/pilot_dry_run.py
```

This proves the validation path; it does **not** replace a real lecture.

## Checklist

- [ ] Consented lecture only  
- [ ] Room calibrated on real camera  
- [ ] Topics (+ modes) marked  
- [ ] Real analysis → Results → CSV  
- [ ] Video purged; aggregates kept  
- [ ] Optional pulse  
- [ ] Optional human marks + ±30s compare  
- [ ] `PILOT_SESSION.md` filled  
