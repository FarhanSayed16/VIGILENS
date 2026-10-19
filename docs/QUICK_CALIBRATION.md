# Quick room calibration

Professors should not hand-draw every seat. Use **Quick setup** on Create/Edit room.

## What is solid (by design)

| Piece | Behavior |
|---|---|
| Viewpoint presets | 4 placements → seat band + amber board ROI |
| Facing / TTOI | Still **seat-cluster → target centroid** (`teaching_target_geometry`) — same as Advanced |
| Detect people | YOLO person boxes → padded seat regions; fallback to grid |
| Board confirm | Tap to place amber box (required for real analysis) |
| Canvas coords | Regions map to `object-fit: contain` image area (not letterbox bars) |
| Save gates | ≥1 seat + target ROI required |

## Placement → geometry

| Camera placement | Seat band | Default board | Facing vector |
|---|---|---|---|
| **Behind the class** | Lower/mid frame | Top strip | Toward top (board in view) |
| **Facing the students** | People only (no board box) | *None* — `facing_mode=toward_camera` | Looking at lens = oriented |
| **Left side** | Rightish half | Left strip | Toward left |
| **Right side** | Leftish half | Right strip | Toward right |

If the amber box is wrong for your room, **tap the real board** — that click updates the facing vector for analysis.

## Honest limits (not bugs)

- **Not full 360° / SLAM** — pick the viewpoint that matches the fixed view you will analyze.
- **Side cameras** vary (board front vs side wall) — presets are starts; confirm with a tap.
- **Back-of-room** often sees backs of heads — Tier-1 body cues; Tier-2 faces may be sparse.
- **One person** at a desk → often `insufficient_coverage` (coverage gate ~5 seats) unless you lower `min_usable_seats` for solo tests.
- **Empty frame detect** → keeps seat grid for that viewpoint.

## Lecturer steps

1. Snap webcam / upload still  
2. Pick viewpoint → Detect people **or** seat grid  
3. Tap board if needed → Save  

## API

- `POST /rooms/calibrate/suggest`  
- `POST /rooms/calibrate/detect` (multipart)  
