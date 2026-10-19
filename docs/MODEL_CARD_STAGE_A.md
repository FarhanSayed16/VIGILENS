# Model card — Stage A (rules TTOI system)

| | |
|---|---|
| **System** | VIGILENS Stage A metrics pipeline |
| **Date** | 18 October 2026 |
| **Type** | Hybrid: pretrained detectors + **hand-written geometric rules** (not a trained engagement classifier) |

---

## Components

| Stage | Component | Training |
|---|---|---|
| Person / pose | Ultralytics **YOLOv8-pose** (COCO pretrained) | None by us |
| Face / head pose | **MediaPipe Face Landmarker** + solvePnP | None by us |
| Seat assign | Polygon IoU / centroid rules | Config only |
| TTOI / coverage / declines | `aggregation.py` + `drop_events.py` + `configs/default.yaml` | Thresholds, not weights |

---

## Intended use

- Post-lecture, **class-level** orientation trends for lecturer reflection  
- Consented local video; purge raw media after analysis  

## Out of scope

- Individual scoring, emotion AI, attendance, grading/discipline  
- Claims of measuring learning or true attention  

---

## Inputs / outputs

- **In:** MP4 (or stream) + room seat ROIs + teaching-target ROI + topics/modes  
- **Out:** 30s windows (`ttoi_pct`, coverage, quality flags), candidate decline events, CSV aggregates  

## Performance notes

- Short public samples often yield `insufficient_coverage` — correct honesty behaviour  
- Classroom accuracy requires operator pilot with enough occupied seats (optional Section B in [`PILOT_SESSION.md`](./PILOT_SESSION.md))  
- Threshold start values: [`THRESHOLDS.md`](./THRESHOLDS.md)

## Ethics / privacy

No face crops or embeddings stored by default. See [`PRIVACY_REVIEW_PHASE23.md`](./PRIVACY_REVIEW_PHASE23.md).

## Versioning

Rules + YAML thresholds are the “model.” Bump `configs/default.yaml` and note in [`THRESHOLDS.md`](./THRESHOLDS.md) when retuning.
