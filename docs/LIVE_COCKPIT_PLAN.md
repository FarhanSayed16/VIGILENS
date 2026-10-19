# VIGILENS — Live Cockpit Hybrid (Phase 25+)

| | |
|---|---|
| **Status** | Active post-MVP program |
| **Prerequisite** | Checkpoint C (MVP complete) |
| **Privacy** | No face recognition, embeddings, or cross-lecture identity |

---

## Product intent

Lecturers need a **Start → live monitoring → Stop → Review** cockpit:

1. Camera preview in front of them during the lecture  
2. Class-level **TTOI** and **coverage** updating as windows complete  
3. Anonymous **seat / group** overlays (orientation bands, not mental attention)  
4. Full timeline and events after **Stop**

Orientation percentages are **observable alignment with the teaching target**, not attention span or learning grades.

---

## Locked decisions

| Topic | Choice |
|-------|--------|
| Privacy | Class TTOI + anonymous seats/groups; session-scoped track IDs only |
| Capture | Continuous until Stop; `WORKER_MAX_FRAMES` = micro-batch safety only |
| Windows | 30s incremental commits + Redis live snapshot |
| Cameras | v1 one source; optional secondary display (metrics from primary) |
| Theme | Daylight Lecture (light); mockups for layout |
| Evidence | No stored face/group crops |
| Wording | Oriented / mixed / sustained change / unobservable |

---

## Live detection screen

### Cameras

- **Primary** — geometry + metrics (seat regions calibrated to this view).  
- **Secondary (optional)** — situational awareness only; not fused into double-counted seats.  
- With one camera, show a single preview.

### On-screen

- Preview, session timer, class TTOI, coverage, seat/group overlays, event feed.  
- Green = broadly aligned · Amber = mixed · Red = sustained orientation change · Grey = unobservable.

---

## Groups without remembering faces

Students are **seat IDs** (and temporary **Group A/B/…** clusters), never names.

If neighboring seats show sustained low orientation or mutual turn-toward cues across ≥2 windows, outline a **possible interaction pattern**. That is suggestive, not proof of talking.

Short-lived tracker IDs may assist within the session; **seat regions remain the primary key**. No face embeddings; nothing carried to future lectures.

---

## Metrics (per 30s window)

For seat or group \(g\) in window \(w\):

\[
O_{g,w}=100\times
\frac{\text{Aligned observations in group }g}
{\text{Usable observations in group }g}
\]

Class **TTOI** pools usable observations; **coverage** is shown separately.  
Do **not** interpret \(O\) as “% mentally attentive.”

### Event starting rules (tunable)

| Event | Initial rule |
|-------|----------------|
| Possible orientation decline | ≥10 pp drop from recent baseline, sustained ≥2 consecutive 30s windows |
| Possible recovery | Returns near baseline for ≥2 valid windows |
| Insufficient evidence | Too few usable seats / low coverage |
| Possible interaction pattern | Adjacent seats with repeated mutual-orientation cues (confidence-gated) |

---

## Group / event inspector

On select:

- Affected anonymous seat IDs and group label  
- Orientation timeline around the event  
- Start/end, baseline, minimum, coverage, active topic  
- Observable cue comparison (charts, not face crops)  
- Lecturer mark: `useful` / `false_alarm` / `insufficient`

---

## Hybrid Option 3 (implementation)

1. **Start lecture** — set session clock, start streaming worker  
2. **Live** — preview + provisional metrics from Redis snapshot  
3. **Every 30s** — append window aggregates (class + per-seat stats)  
4. **Stop** — finalize declines/recoveries/groups; session complete  
5. **Review** — full timeline, heatmap, events  

Batch upload analysis remains available as a secondary offline path.

---

## Phase map

| Phase | Deliverable |
|-------|-------------|
| 25 | This doc + Console cockpit shell |
| 26 | `live/start` · `live/stop` · `live/state` |
| 27 | Streaming worker + 30s append + Redis snapshot |
| 28 | Wire Console preview / gauges / seat map / feed |
| 29 | Groups + event inspector + feedback |
| 30 | Review heatmap / timeline upgrade |
| 31 | Dual-camera display (optional secondary) |
| 32 | Privacy, tests, Checkpoint D |

---

## Non-goals

- Face recognition / roll numbers / rankings  
- “Attention %” as mental state  
- Stored evidence frames  
- Claiming speech detection as fact  
