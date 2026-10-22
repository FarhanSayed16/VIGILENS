# Vision worker

## Layout (Phase 16+)

| Module | Role |
|---|---|
| `fake_worker.py` | Phase 11 synthetic windows/events (`USE_FAKE_WORKER=true`) |
| `config.py` | Load `configs/default.yaml` |
| `capture.py` | MP4 / webcam / RTSP-HTTP ingest + ~1–2 fps sampling |
| `regions.py` | Seat polygons, target centroid, yaw' helpers |
| `vision_yolo.py` | YOLOv8-pose persons + keypoints |
| `seat_mapping.py` | Person → seat assign + N_expected calibration |
| `debug_overlay.py` | Local-only seat/person debug draw |
| `vision_mediapipe.py` | Face Landmarker Task API + solvePnP yaw/pitch |
| `features.py` | Tier-1 / Tier-2 fuse; unobservable when neither |
| `aggregation.py` | 30s windows → TTOI / coverage / quality gates |
| `drop_events.py` | Candidate orientation declines (smooth + baseline) |
| `metrics_pipeline.py` | Features → windows + events (offline) |
| `pilot_validation.py` | Human marks CSV + ±30s decline compare (Phase 22) |
| `jobs.py` | Fake / offline metrics / real (Phase 20) entrypoints |

## Install

```bash
# Prefer Python 3.10–3.12
pip install -r worker/requirements.txt
```

Pinned: OpenCV, NumPy, PyYAML, Ultralytics, MediaPipe.

## Smoke

From repo root:

```powershell
$env:PYTHONPATH = "D:\VIGILENS"
python worker/scripts/smoke_capture.py      # Phase 16 ingest
python worker/scripts/smoke_yolo_seats.py   # Phase 17 YOLO + seats + overlay
python worker/scripts/smoke_head_pose.py    # Phase 18 MediaPipe yaw/pitch + signs
python worker/scripts/smoke_ttoi.py         # Phase 19 TTOI + declines → schema JSON
python worker/scripts/smoke_real_job.py     # Phase 20 real job on short clip
python worker/scripts/eval_thresholds.py    # Phase 21 scripted threshold eval
python worker/scripts/pilot_dry_run.py      # Phase 22 pilot validation dry-run
python worker/scripts/compare_declines.py --human marks.csv --machine events.json
pytest tests/unit -q                       # aggregation / decline / thresholds / pilot
```

Outputs under `uploads/_smoke/` (gitignored). First YOLO run downloads `yolov8n-pose.pt`;
first MediaPipe run downloads `models/face_landmarker.task`.

## Backend integration

`job_service` calls `jobs.run_real_job` by default (`USE_FAKE_WORKER=false`).
Set `USE_FAKE_WORKER=true` for CI / Checkpoint A (synthetic TTOI, no GPU).
Optional `WORKER_MAX_FRAMES` caps sampling for local smokes.
Same `JobContract` / `WorkerResultPayload` schema either way.
