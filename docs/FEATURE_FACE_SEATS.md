# Feature change — face registration instead of drawn seats

Do not treat this file as the project master plan. The execution checklist stays in `docs/MASTER_PLAN.md`. This file is only the seat-logic change.

## Rule

A seat exists only after the camera has seen a face. Empty chairs are not invented. Slots are anonymous (`P1`, `P2`, …) for this lecture only. This is not attendance and not face recognition: no names, no embeddings, no face crops, nothing kept for the next lecture.

## How a lecture starts

1. The first **15 seconds** after Start are registration.
2. A box is drawn only around a detected face. Both eyes must be visible (MediaPipe Face Landmarker). A body with no face does not become a seat.
3. The box locks into `P1`, `P2`, … only after it stays roughly still for about **2 seconds**. If the phone or webcam is moving, the live box is shown and the hint says to hold steady. Nothing locks yet.
4. After lock, that slot is the person for this lecture. Looking down later can read as unobservable. The slot is not replaced by a grey placeholder.
5. A new stable face can still join after the opening window. Someone who leaves does not leave an empty tile.
6. “Faced the front” is computed only for registered faces. On a phone, facing the lens counts as oriented, because a drawn board box cannot follow a moving camera.

## Removed so it cannot run beside this

- Live start no longer requires drawn `seat_regions_json`.
- Live assignment no longer uses drawn regions, virtual `vN` / “Extra” seats, or the one-seat fallback.
- The live preview no longer paints the room’s saved boxes. The only boxes are live face boxes, then locked `P` slots.
- Quick setup no longer creates a default 6-seat grid, and the room editor does not require seats before a lecture.
- Review copy talks about registered faces this session, not drawn boxes or Extra seats.

A teaching-target box may still aim orientation for a fixed room camera. It does not create seats.

## Files

| Area | Path |
|---|---|
| Registrar | `worker/face_registrar.py` |
| Live loop | `worker/live_session.py` |
| Preview boxes | `worker/debug_overlay.py` |
| Start gate | `backend/app/services/live_service.py` |
| Old assign | `worker/seat_mapping.py` |
| Grid preset | `worker/quick_calibrate.py`, `frontend/src/pages/rooms/RoomEditorPage.tsx` |
| Lecturer UI | `frontend/src/components/domain/LectureCockpit.tsx`, `frontend/src/pages/results/ResultsPage.tsx` |
| Tests | `tests/unit/test_face_registrar.py` |
