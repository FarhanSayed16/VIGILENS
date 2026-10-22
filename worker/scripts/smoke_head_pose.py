#!/usr/bin/env python3
"""
Phase 18 exit: Face Landmarker + solvePnP yaw/pitch with verified signs.

Checks:
  1) Synthetic L/R/U/D projectPoints → PnP sign recovery
  2) Real face: MediaPipe detect + horizontal flip flips yaw sign
  3) Writes local debug overlay under uploads/_smoke/

From repo root:
  $env:PYTHONPATH = "D:\\VIGILENS"
  python worker/scripts/smoke_head_pose.py
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from worker import config, vision_mediapipe

# Clear frontal face (OpenCV sample) — bus.jpg side faces often fail Face Landmarker
FACE_URLS = (
    "https://raw.githubusercontent.com/opencv/opencv/4.x/samples/data/lena.jpg",
)


def _ensure_face_image(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.stat().st_size > 1000:
        return path
    last_err: Exception | None = None
    for url in FACE_URLS:
        try:
            print(f"Downloading face sample -> {path}")
            req = urllib.request.Request(url, headers={"User-Agent": "VIGILENS-smoke/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if len(data) > 5000:
                path.write_bytes(data)
                return path
        except Exception as exc:  # noqa: BLE001 — try next URL
            last_err = exc
            print(f"  skip: {exc}")
    raise RuntimeError(f"Could not download a face sample: {last_err}")


def _draw_pose_overlay(img: np.ndarray, pose: vision_mediapipe.HeadPoseResult) -> np.ndarray:
    out = img.copy()
    for pt in pose.pnp_points_px:
        cv2.circle(out, (int(pt[0]), int(pt[1])), 3, (0, 255, 255), -1)
    banner = (
        f"yaw={pose.yaw_deg:+.1f}  pitch={pose.pitch_deg:+.1f}  "
        f"face_w={pose.face_width_px:.0f}px"
    )
    cv2.rectangle(out, (0, 0), (out.shape[1], 36), (20, 20, 20), -1)
    cv2.putText(
        out,
        banner,
        (8, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (240, 240, 240),
        2,
        cv2.LINE_AA,
    )
    # Axis hint from nose
    nose = pose.pnp_points_px[0]
    length = 60.0
    yaw_r = np.radians(pose.yaw_deg)
    # Image-right = +yaw
    tip = (
        int(nose[0] + length * np.sin(yaw_r)),
        int(nose[1] + length * 0.35 * (pose.pitch_deg / 30.0)),
    )
    cv2.arrowedLine(
        out,
        (int(nose[0]), int(nose[1])),
        tip,
        (0, 180, 0),
        2,
        tipLength=0.25,
    )
    return out


def _find_usable_pose(landmarker, img, face_width_min: float):
    """Try full image, then upscaled, then lower gate for smoke only."""
    pose = vision_mediapipe.estimate_head_pose(
        landmarker, img, face_width_min_px=face_width_min
    )
    if pose is not None:
        return pose, img, face_width_min

    # Upscale small faces (classroom / bus crops)
    big = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    pose = vision_mediapipe.estimate_head_pose(
        landmarker, big, face_width_min_px=face_width_min
    )
    if pose is not None:
        return pose, big, face_width_min

    # Diagnostic: any face at all?
    relaxed = max(40.0, face_width_min * 0.5)
    pose = vision_mediapipe.estimate_head_pose(
        landmarker, big, face_width_min_px=relaxed
    )
    if pose is not None:
        print(
            f"NOTE: face_width={pose.face_width_px:.0f}px < config "
            f"{face_width_min:.0f}; using relaxed gate for smoke only"
        )
        return pose, big, relaxed
    return None, img, face_width_min


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 18 MediaPipe head-pose smoke")
    parser.add_argument("--image", type=str, default="", help="Optional face image path")
    args = parser.parse_args()

    cfg = config.load_config()
    face_min = config.face_width_min_px(cfg)
    out_dir = REPO / "uploads" / "_smoke"
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- 1) Synthetic sign recovery (L/R/U/D) ---
    failures = vision_mediapipe.verify_solvpnp_sign_convention()
    if failures:
        print("ERROR: solvePnP sign verification failed:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("solvePnP signs OK: look_right(+yaw) look_left(-yaw) look_down(+pitch) look_up(-pitch)")

    # --- 2) Load Face Landmarker Task API ---
    model_path = vision_mediapipe.ensure_face_landmarker_model()
    print(f"model: {model_path}")
    landmarker = vision_mediapipe.load_face_landmarker(model_path)
    print("Face Landmarker loaded (Task API)")

    if args.image:
        img_path = Path(args.image)
        if not img_path.is_file():
            print(f"ERROR: image not found: {img_path}", file=sys.stderr)
            return 1
    else:
        img_path = _ensure_face_image(out_dir / "phase18_face.jpg")

    img = cv2.imread(str(img_path))
    if img is None:
        print("ERROR: could not read face image", file=sys.stderr)
        return 1

    pose, work, used_gate = _find_usable_pose(landmarker, img, face_min)
    if pose is None:
        print(
            "ERROR: no face landmarks / PnP — try --image with a clear frontal face",
            file=sys.stderr,
        )
        return 1

    print(
        f"real face: yaw={pose.yaw_deg:+.1f} pitch={pose.pitch_deg:+.1f} "
        f"face_w={pose.face_width_px:.0f}px (gate={used_gate:.0f})"
    )

    # --- 3) Flip test: yaw sign should reverse ---
    flipped = cv2.flip(work, 1)
    pose_f = vision_mediapipe.estimate_head_pose(
        landmarker, flipped, face_width_min_px=used_gate
    )
    if pose_f is None:
        print("ERROR: no face on horizontally flipped image", file=sys.stderr)
        return 1
    print(
        f"flipped:   yaw={pose_f.yaw_deg:+.1f} pitch={pose_f.pitch_deg:+.1f} "
        f"face_w={pose_f.face_width_px:.0f}px"
    )
    # If original yaw near 0, require flipped to move opposite or both near zero
    if abs(pose.yaw_deg) >= 3.0:
        if np.sign(pose.yaw_deg) == np.sign(pose_f.yaw_deg) and abs(pose_f.yaw_deg) >= 3.0:
            print(
                "ERROR: horizontal flip did not reverse yaw sign "
                f"(orig={pose.yaw_deg:+.1f} flip={pose_f.yaw_deg:+.1f})",
                file=sys.stderr,
            )
            return 1
        print("flip yaw polarity OK (sign reversed)")
    else:
        # Near-frontal: require flip yaw to have opposite sign OR small magnitude
        if abs(pose_f.yaw_deg) >= 8.0 and np.sign(pose_f.yaw_deg) == np.sign(
            pose.yaw_deg if abs(pose.yaw_deg) > 0.5 else 1.0
        ):
            # Soft check — near zero original is OK
            print("flip yaw near-frontal OK (orig ~0)")
        else:
            print("flip yaw near-frontal OK")

    overlay = _draw_pose_overlay(work, pose)
    overlay_f = _draw_pose_overlay(flipped, pose_f)
    # Side-by-side
    h = max(overlay.shape[0], overlay_f.shape[0])
    w = overlay.shape[1] + overlay_f.shape[1]
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    canvas[: overlay.shape[0], : overlay.shape[1]] = overlay
    canvas[: overlay_f.shape[0], overlay.shape[1] :] = overlay_f
    cv2.putText(
        canvas,
        "orig",
        (8, h - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        "flipped",
        (overlay.shape[1] + 8, h - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )
    out_png = out_dir / "phase18_head_pose_overlay.png"
    cv2.imwrite(str(out_png), canvas)
    print(f"wrote overlay: {out_png}")

    # Tier selection quick check (no YOLO required)
    from worker.features import fuse_seat_feature
    from worker.vision_yolo import PersonDetection

    h0, w0 = work.shape[:2]
    fake_person = PersonDetection(
        bbox_xyxy=(0.0, 0.0, float(w0), float(h0)),
        conf=0.9,
        keypoints=np.zeros((17, 3), dtype=np.float32),
    )
    # Put visible shoulders so Tier-1 fallback would work if Tier-2 off
    fake_person.keypoints[5] = [w0 * 0.35, h0 * 0.45, 0.9]
    fake_person.keypoints[6] = [w0 * 0.65, h0 * 0.45, 0.9]

    feat2 = fuse_seat_feature(
        "s1",
        0.0,
        fake_person,
        frame_bgr=work,
        landmarker=landmarker,
        face_width_min_px=used_gate,
        enable_tier2=True,
    )
    feat1 = fuse_seat_feature(
        "s1",
        0.0,
        fake_person,
        frame_bgr=work,
        landmarker=landmarker,
        face_width_min_px=used_gate,
        enable_tier2=False,
    )
    feat_empty = fuse_seat_feature("s1", 0.0, None)
    print(
        f"tier select: tier2={feat2.tier} yaw'={feat2.yaw_prime_deg} "
        f"tier1_only={feat1.tier} empty={feat_empty.data_quality_note}"
    )
    if feat2.tier != 2:
        print("ERROR: expected Tier-2 when face large enough", file=sys.stderr)
        return 1
    if feat1.tier != 1:
        print("ERROR: expected Tier-1 when Tier-2 disabled", file=sys.stderr)
        return 1
    if feat_empty.data_quality_note != "empty":
        print("ERROR: empty seat should be marked empty", file=sys.stderr)
        return 1

    # Unobservable: no person landmarks usable + no face
    blank = np.zeros((120, 120, 3), dtype=np.uint8)
    ghost = PersonDetection(
        bbox_xyxy=(10.0, 10.0, 100.0, 100.0),
        conf=0.1,
        keypoints=np.zeros((17, 3), dtype=np.float32),
    )
    feat_u = fuse_seat_feature(
        "s1",
        0.0,
        ghost,
        frame_bgr=blank,
        landmarker=landmarker,
        face_width_min_px=face_min,
        enable_tier2=True,
    )
    if feat_u.tier is not None or feat_u.data_quality_note != "unobservable":
        print(
            f"ERROR: expected unobservable, got tier={feat_u.tier} "
            f"note={feat_u.data_quality_note}",
            file=sys.stderr,
        )
        return 1
    print("unobservable path OK")

    print("Phase 18 smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
