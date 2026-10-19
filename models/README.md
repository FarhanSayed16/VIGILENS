# Model weights & first-run setup

Do **not** commit large weight files (`*.pt`, `*.task`, `*.onnx` are gitignored).

MVP uses **pretrained** models only — no classroom training required.

---

## What downloads automatically

| Model | How | Where it lands |
|---|---|---|
| **YOLOv8-pose** (`yolov8n-pose.pt` default) | Ultralytics on first `YOLO(...)` call | Ultralytics cache and/or cwd |
| **MediaPipe Face Landmarker** | `worker.vision_mediapipe.ensure_face_landmarker_model` | Prefer `models/face_landmarker.task` |

Optional: copy `yolov8n-pose.pt` into this folder for a predictable local path (`worker` resolves via `resolve_model_path`).

---

## One-time setup

```powershell
# From repo root, with worker deps installed
pip install -r worker/requirements.txt
$env:PYTHONPATH = "D:\VIGILENS;D:\VIGILENS\backend"

# Triggers YOLO download + short real job
python worker/scripts/smoke_real_job.py

# Or head-pose only (Face Landmarker .task)
python worker/scripts/smoke_head_pose.py
```

Offline / air-gapped: pre-copy weights into `models/` from a machine that already ran the smokes.

---

## Config

Vision thresholds and model name hints: `configs/default.yaml` · [`docs/THRESHOLDS.md`](../docs/THRESHOLDS.md) · [`docs/AIML_CONFIRMATION.md`](../docs/AIML_CONFIRMATION.md).

Stage-A “model card” (rules + detectors): [`docs/MODEL_CARD_STAGE_A.md`](../docs/MODEL_CARD_STAGE_A.md).

---

## Privacy

`store_face_crops` / embeddings remain **off**. Weights here are detectors only, not student embeddings.
