# Quick room calibration

The lecturer does not draw a seat for every chair. Quick setup only records where the camera sits and, for a fixed room camera, which way the board is.

## What is solid (by design)

| Piece | Behavior |
|---|---|
| Viewpoint presets | 4 placements. They do not create a seat grid. |
| Faces | At Start, a face with both eyes that holds still for about 2 seconds becomes `P1`, `P2`, … |
| Facing | A fixed room camera uses the amber board box only to aim “faced the front”. A phone uses toward-camera. |
| Empty chairs | Not shown. No grey placeholder tiles. |
| Save | A room can be saved with zero seats. |

## Placement → direction

| Camera placement | Board box | What counts as facing the front |
|---|---|---|
| **Behind the class** | Top strip | Toward that box |
| **Facing the students** | None | Looking at the lens |
| **Left side** | Left strip | Toward that box |
| **Right side** | Right strip | Toward that box |

If the amber box is wrong, tap the real board. That click updates direction. It still does not create seats.

## Honest limits

- The first 15 seconds are for registration. A later stable face can still join.
- Waving the phone shows a live face box and “hold still”. It does not lock a seat.
- Someone who looks down keeps their slot as unobservable. The slot is not deleted.
- This is not attendance. No names, no face crops, nothing kept for the next lecture.

## Lecturer steps

1. Snap a frame or skip straight to the lecture if you already know the camera.
2. Pick the viewpoint. Save the room.
3. Start the lecture and hold the camera still until the status says people are registered.

## API

- `POST /rooms/calibrate/suggest` returns direction and an empty seat list.
- `POST /rooms/calibrate/detect` does not turn people or a grid into seats.
