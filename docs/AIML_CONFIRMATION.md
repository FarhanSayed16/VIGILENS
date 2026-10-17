# VIGILENS — AI/ML & Image Processing Plan (Confirmation)

| | |
|---|---|
| **Status** | **Locked confirmation for AIML scope** |
| **Date** | 17 October 2026 |
| **Based on** | `docs/VIGILENS_COMPLETE_IDEA.md` §3.1, §6, §8, §9, Phase 1 |
| **Audience** | You — clear yes/no on models, what you give vs what I build |

> Frontend / backend / DB will be planned later.  
> **This file only confirms the vision / ML side.**

---

## 1. One-line confirmation

**You do NOT need to hand me custom-trained ML models.**  
MVP uses **two public pretrained models** that download automatically when we install packages.  
The “intelligence” of VIGILENS MVP is mostly **our code** (geometry rules + TTOI + coverage), not a model we train from scratch.

---

## 2. What ML / CV pieces do we need?

### MVP — required (I set these up in code)

| # | What | Exact model / library | Do you give me weights? | Who installs / wires it? |
|---|---|---|---|---|
| 1 | Find people + body pose in the classroom | **YOLOv8-pose** (`yolov8n-pose` or `yolov8s-pose`) via Ultralytics | **No** — first run auto-downloads official COCO pretrained weights | **Me** (pip + code) |
| 2 | Head yaw/pitch when face is large enough | **MediaPipe Face Landmarker** (Task API) + `solvePnP` | **No** — comes with MediaPipe / Google’s published bundle | **Me** (pip + code) |
| 3 | Video read / frame sample | **OpenCV** | N/A | **Me** |
| 4 | Class engagement proxy | **TTOI** — our rule-based math on pose angles | N/A — **not a neural net** | **Me** (Python logic) |
| 5 | Trust filter | **Coverage %** — when camera can’t see enough seats | N/A — rules | **Me** |
| 6 | “When did the room shift?” | **Candidate decline detection** — smooth + baseline drop | N/A — rules | **Me** |

### MVP — explicitly NOT needed

| Thing | Status |
|---|---|
| Custom YOLO trained on your classroom | **Not needed for MVP** |
| Emotion / boredom / confusion models | **Out of scope forever for product claim** |
| Face recognition / student ID | **Forbidden** |
| SlowFast / I3D / VideoMAE as main product model | **No** (research notebook only later) |
| Hugging Face “engagement” checkpoints (e.g. DAiSEE) | **No** |
| You buying / uploading model files to me | **No** |

### Phase 2 — optional later (after MVP works)

| What | When | Do you give models? |
|---|---|---|
| Phone detection (YOLO `cell phone` class) | Phase 2 | No — same Ultralytics family |
| Eye/yawn cues (EAR/MAR from MediaPipe) | Phase 2, near seats only | No |
| OpenVINO action model (writing / hand-raise comparison) | Optional Phase 2 | No — download from Open Model Zoo; I wire it |
| Small sklearn/XGBoost classifier on **geometry features** | Only after we label local lectures | **You help label video**, not give a pretrained model |

---

## 3. Do you have to separately give me models?

### Short answer: **No for MVP.**

| You provide | I handle |
|---|---|
| A machine with Python 3.10+ (GPU nice, CPU OK for demos) | Install `ultralytics`, `mediapipe`, `opencv-python` |
| Internet once so YOLO/MediaPipe weights can download | Pin versions, paths under `models/` (gitignored) |
| Later: a few **consented classroom video clips** to test/tune | Pipeline code, thresholds, TTOI, decline logic |
| Later (Phase 2): help **label** windows if we train Stage-B | Optional small classifier — only if it beats rules |

**You do not need to:**
- Find or buy YOLO/MediaPipe weight files yourself  
- Train anything before we start  
- Give me a dataset on day one to “start ML”

---

## 4. What exactly is the AIML work? (what I build)

Think of it as a **pipeline**, not “train one big AI.”

```text
Video (upload / webcam / phone)
        │
        ▼
   Sample frames (~1–2 fps)          ← OpenCV
        │
        ▼
   Detect people + pose              ← YOLOv8-pose (pretrained)
        │
        ▼
   Map each person → seat region     ← our geometry (you draw seats once)
        │
        ▼
   If face big enough → head pose    ← MediaPipe Face Landmarker (pretrained)
        │
        ▼
   Per seat: facing board? head down? hand up? unobservable?
                                         ← RULES (thresholds in config)
        │
        ▼
   Every 30 seconds:
      TTOI + Coverage + secondary rates
                                         ← OUR MATH (not a trained model)
        │
        ▼
   Smooth → flag candidate declines
                                         ← OUR LOGIC
```

### Capability tiers (honest about camera distance)

| Tier | When | What we use |
|---|---|---|
| **Tier 1 — Body** | Face tiny / far seat | YOLO pose only (torso / shoulders / hand raise) |
| **Tier 2 — Head** | Face ≳ ~80–100 px wide | MediaPipe yaw/pitch |
| **Tier 3** | Very close face | Not required for MVP claims |

---

## 5. Training — yes or no?

| Stage | Train something? | When |
|---|---|---|
| **A — MVP (now)** | **No training.** Pretrained YOLO + MediaPipe + rules | Start here |
| **B — After pilot** | Maybe a **tiny** classifier on features we already compute | Only if labels exist and it beats rules on **our** lectures |
| **R — Research** | Optional notebook on public OUC-CGE dataset | Parallel; does **not** replace product path |

**Locked:** Do **not** fine-tune YOLO first. Highest ROI is rules → then maybe Stage B on local labels.

---

## 6. What YOU must still do for AIML to succeed (non-model)

These are **not** “give me a model” — they are project inputs:

1. **Camera / video** — laptop webcam, phone stream, or MP4 of a real/scripted class  
2. **Room calibration** — seat polygons + board/screen ROI (UI later; JSON config is enough at first)  
3. **Confirm wording with professor** — we measure **TTOI (orientation)**, not “attention” or “boredom”  
4. **Later validation** — annotators watch clips and say if orientation looks right (not train YOLO)

Without classroom video, I can still write the full pipeline and test on stock/scripted clips; claims about *your* lectures need your footage.

---

## 7. MVP AIML success criteria (confirm this is the goal)

When Phase 1 vision is “done,” we should be able to:

1. Load a short classroom clip  
2. Run YOLO-pose (+ MediaPipe where faces are large)  
3. Produce a **TTOI timeline** every 30 s  
4. Show **coverage** and grey out low-trust windows  
5. Flag **candidate orientation declines** (not “attention dropped”)  
6. Respect modes later (e.g. note-taking → head-down is OK)

Frontend/backend wiring can come after this core works.

---

## 8. Your confirmation checklist

Please treat these as **yes** unless you say otherwise:

- [x] MVP models = **YOLOv8-pose + MediaPipe Face Landmarker only**  
- [x] **No custom model files from you** for MVP  
- [x] **No emotion / face-ID / engagement CNN** as product  
- [x] TTOI + coverage + declines = **our code**, not a black-box “attention model”  
- [x] Training (if any) = **optional Stage B later**, after local labels  
- [x] I implement the vision worker; you provide machine + video + seat/target setup when we test  

---

## 9. Bottom line

| Question | Answer |
|---|---|
| What models do we need? | **YOLOv8-pose** + **MediaPipe Face Landmarker** (MVP) |
| Do I give you models separately? | **No** — they download via packages |
| Can you (the agent) do the AIML work alone? | **Yes for code + setup**; you supply **PC + test video + seat/board regions** when we run real tests |
| What is the main AIML aim? | Class-level **TTOI timeline** with **coverage** and **candidate declines** — observable orientation, not mind-reading |
| Train first? | **No** — rules on pretrained pose first |

If this matches what you want, reply **“AIML confirmed”** and we treat this file as the locked vision plan while frontend/backend stay for later.
