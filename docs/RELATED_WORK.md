# Related work — honesty note

**VIGILENS does not claim to be the first classroom computer-vision engagement system.**

Many projects use YOLO, pose, face landmarks, or dashboards to estimate “attention” or “engagement.” Overlap is expected. Differentiation for this MVP is product framing and engineering, not invention of the idea.

---

## How we stay distinct

| Prior pattern | Our stance |
|---|---|
| Per-student attention / concentration scores | **Class-level only** — no identity, no individual grades |
| Emotion / expression → engagement | **Rejected** as primary claim |
| Live alert “gotcha” products | **Reflective** post-lecture timeline first |
| Dashboards without uncertainty | **Coverage / insufficient evidence** as a first-class output |
| Attendance / face ID | **Never** |

Primary metric: **TTOI** (Teaching-Target Orientation Index) with topic markers and candidate declines — see [`VIGILENS_COMPLETE_IDEA.md`](./VIGILENS_COMPLETE_IDEA.md) §3.1.

---

## Reuse

- **YOLOv8-pose** and **MediaPipe Face Landmarker** are pretrained third-party models (licenses apply).  
- Open-source classroom demos may inform engineering patterns; **do not copy** attendance/ID/emotion designs; check licenses.  
- Stage-A TTOI is **rule-based geometric** — not a proprietary neural “engagement net.”

---

## Citation posture for reports

Prefer: *“VIGILENS builds on established pose/face tooling and prior classroom CV research; it contributes a privacy-preserving lecturer workflow centered on TTOI, coverage gating, and topic-linked declines.”*

Avoid: *“First system to detect student attention.”*
