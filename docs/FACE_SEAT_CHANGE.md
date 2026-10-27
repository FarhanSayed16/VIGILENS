# Face-based seat registration — feature change

| | |
|---|---|
| **Status** | Plan only. Do not start coding until this checklist is the task. |
| **Date** | 24 October 2026 |
| **Does not replace** | [`MASTER_PLAN.md`](./MASTER_PLAN.md). That file stays the MVP build record. This file owns this one change. |
| **Why a separate file** | Drawn seats and virtual “Extra” seats are already wired through the worker, the API, and the room editor. This change deletes that path. A checklist keeps the old code from being left behind. |

---

## What is wrong now

The live view draws **saved seat rectangles** from the room. Those rectangles are a percentage of the frame from when someone drew them.

On a phone that moves, the rectangles stay put and the room does not. The reference photo shows the person in the corner and the seat boxes on the ceiling. Empty slots also appear as **grey virtual seats** (`v1`, `Extra 1`) even when nobody is there.

Students do not sit in a fixed drawing. Some seats are full, some are empty, and the set can change. A box should exist only where a **face** has actually been seen.

---

## What this change achieves

For the **first 20 seconds** after Start lecture:

1. Find people with the pose model already in the worker (YOLOv8-pose).
2. Confirm a **face** on that person: both eyes visible (pose eye keypoints, and the existing MediaPipe face landmarker when the face is large enough).
3. Draw a box on that face only. No box for an empty drawn seat.
4. If the same face stays in view and is steady, **register a seat** at that place (`S1`, `S2`, …).
5. If the box jitters because the **camera** is moving (phone test), do not create a new seat for the same person. Wait until the face is steady, then lock the seat.
6. After 20 seconds, new faces can still register (someone walks in). Faces that leave drop out. Faces that were never confirmed never become seats.

Orientation (“faced the front”) is then computed **per registered seat**, same as today, but the seat list comes from faces in this session.

### Explicitly not in this change

- No attendance roll.
- No name, no face photo stored, no face embedding, no match to a later lecture.
- A seat id lives for **this session only**. Next lecture starts from zero.
- The room editor’s old seat grid is not the source of seats anymore. Do not keep it “just in case” on the live path.

Attendance can be a later feature **only if** it still refuses cross-lecture identity. Do not leave hooks, tables, or saved crops for it now.

---

## Locked rules

| Rule | Choice |
|---|---|
| Registration window | **20 seconds** from the first frame after Start |
| A seat is born when | A face is confirmed on **at least 5 samples** spread over **at least 2 seconds**, and the box center moves less than **8% of the frame width** during those samples |
| Camera moving | If **most** confirmed faces jump the same direction in one step, treat that step as camera motion. Slide existing tracks. Do not mint new seats from that step. |
| Person moving | One face drifts while others stay. Keep the same seat id. Mark the track **moving** until it is steady again. Do not split it into two seats. |
| Eyes | Both eyes (pose keypoints, or landmarker eye corners) must be visible to **confirm**. A body with no face stays an unconfirmed detection: a thin box is allowed, **no seat id**, not counted in TTOI. |
| Empty seats | Do not draw them. No grey tiles for seats nobody has occupied. |
| Ids | `S1`, `S2`, … in the order faces first confirm. Never `v1` / `Extra`. |
| Cap | 60 confirmed seats per session (same classroom ceiling as now). |
| Facing | Keep the room’s teaching-target direction if one is saved. If the room has no target, treat “faced the front” as facing the camera. Do not block Start because seat boxes were never drawn. |
| Privacy copy | UI keeps saying seats are anonymous and not identity. |

---

## Code to remove (do not leave a second path)

Old logic and the new logic must not both run.

| Remove from the live path | Where it lives now |
|---|---|
| Require drawn `seat_regions` before Start | `backend/app/services/live_service.py` (`no_seats` error) |
| Parse drawn seats as the only seats | `worker/live_session.py` (`parse_seat_regions`, raise if none) |
| Virtual seats for people outside drawings | `worker/seat_mapping.py` `virtual_for_unassigned`, `max_virtual_seats`; call in `live_session.py` |
| Labels `Extra N` / `vN` | `LectureCockpit.tsx`, `ResultsPage.tsx` `seatLabel` |
| Draw saved room boxes on the phone/laptop preview | `LectureCockpit.tsx` overlay that reads `room.seat_regions` |
| Grey “unobservable” tiles for seats that were never detected | Seat map built from `expected_ids` before anyone is seen |

Keep `worker/regions.py` and the room editor **on disk** for now, but **live and review must not read drawn seats**. Deleting the editor is a follow-up, not part of the first working slice. Do not add a new “also use drawn seats if present” branch.

`dedupe_persons` in `seat_mapping.py` can stay. The nearest-drawn-seat function cannot stay on the live path.

---

## New logic (one module)

Add `worker/face_seats.py`. It owns registration. `live_session.py` calls it instead of `assign_persons_to_seats`.

Per frame, input is the existing person list from `vision_yolo.detect_persons` plus eye/face confirmation:

- Pose: `left_eye` and `right_eye` keypoints present and above a confidence floor.
- If the face is wide enough, MediaPipe face landmarker (already loaded) must also see the face. If it cannot, the pose eyes are enough only when both eye scores are high. Do not invent a face from a torso.

State for each track:

| Field | Meaning |
|---|---|
| `track_id` | Internal, this session only |
| `seat_id` | `S1`… once confirmed, else empty |
| `bbox` | Last face box (eyes + nose, else the person box cropped to the head) |
| `confirmed` | Registered seat or not |
| `steady` | Center stable vs still moving |
| `last_seen_sec` | Drop the track after **3 seconds** unseen |
| `samples` | Times the face was confirmed |

Matching frame to frame: highest overlap (IoU) of the face box, else nearest center within **15% of frame width**. After a camera-motion step, use the shifted centers.

Output each frame: the same shape `FrameSeatMap` already uses (`seat_to_person_indices`), but ids are only confirmed `S*` seats. Unconfirmed people go to `unassigned_indices` and are **not** given a fake seat.

Preview boxes:

- Confirmed seat: solid box, label `S2`, plus the orientation color already used (green / amber / red).
- Unconfirmed face: thin box, no seat name, caption `confirming`.
- No other rectangles.

Seat map under the video lists **only confirmed seats**. Before the first confirmation, the map says “Finding faces — seats appear as each face stays steady.”

---

## Checklist

Work in order. Do not tick an item because the code exists; tick it when the behaviour below is true.

### A. Stop the old path

- [ ] Start lecture works when the room has **no** drawn seat boxes.
- [ ] Live loop does not call `virtual_for_unassigned`.
- [ ] No `vN` or `Extra` id can appear in Redis, the database window, or the UI.
- [ ] The preview no longer paints `room.seat_regions`.
- [ ] Unit tests that only exist to prove virtual seats (`tests/unit/test_multi_person_seats.py` and the solo drawn-seat fallback) are replaced, not left red and not left describing the old rule.

### B. Register from the face

- [ ] `worker/face_seats.py` confirms a face only when both eyes are visible.
- [ ] A seat id is assigned only after the steady-sample rule (5 samples, 2 seconds, center movement under 8% of width).
- [ ] Two overlapping detections of one person become one track (`dedupe_persons`).
- [ ] A face that leaves for 3 seconds drops off the map. It does not leave a grey seat behind.
- [ ] A new face after the 20 second window can still become a seat. The window is “start registering immediately,” not “ignore everyone who arrives later.”
- [ ] Camera-motion step does not create a second seat for a face that jumped with the frame.
- [ ] A person who turns or shifts, while the others stay, keeps one seat id and is marked moving until steady.

### C. Wire live and review

- [ ] `run_real_live_session` uses `face_seats` for both the laptop webcam and the phone camera (`browser:phone`).
- [ ] TTOI / coverage use the confirmed seat count as “expected,” not the old drawn count. If nobody is confirmed yet, coverage is empty, not 0% of six grey seats.
- [ ] Phone preview shows face boxes on the video the phone is sending.
- [ ] Review “who faced the front” uses `S1`, `S2`, … only.
- [ ] Copy no longer tells the lecturer to draw seats or to read “Extra” slots.

### D. Prove it

- [ ] Unit test: one steady face becomes `S1` and no other tile.
- [ ] Unit test: a second face becomes `S2`. A duplicate box on the first face does not.
- [ ] Unit test: all boxes jump together → still two seats, not four.
- [ ] Unit test: one box drifts → same seat id, `steady` false, then true when it stops.
- [ ] Unit test: eyes missing → no seat.
- [ ] Manual: phone session, move the phone for a few seconds, hold still. Boxes sit on the face, not on the ceiling. Empty drawn slots are gone.

---

## Done when

A lecturer can Start on the phone or the laptop **without drawing seats**. Within about 20 seconds, each steady face has one box and one seat id. Moving the camera does not spray new seats. The seat map has no grey placeholders. Nothing in this slice can name a student or recognise them next time.
