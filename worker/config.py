"""Load shared vision thresholds from configs/default.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Repo root = parent of worker/
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "default.yaml"


def resolve_config_path(path: Optional[str | Path] = None) -> Path:
    """Resolve config path against repo root when relative / missing from CWD."""
    if path is None or str(path).strip() == "":
        return DEFAULT_CONFIG_PATH
    cfg_path = Path(path)
    if cfg_path.is_file():
        return cfg_path.resolve()
    anchored = (REPO_ROOT / cfg_path).resolve()
    if anchored.is_file():
        return anchored
    if DEFAULT_CONFIG_PATH.is_file():
        return DEFAULT_CONFIG_PATH
    return cfg_path


def load_config(path: Optional[str | Path] = None) -> Dict[str, Any]:
    """
    Read YAML config. Returns nested dict with sampling, orientation, etc.
    Relative paths resolve from repo root (safe when API cwd is backend/).
    """
    cfg_path = resolve_config_path(path)
    if not cfg_path.is_file():
        raise FileNotFoundError(
            f"Config not found: {cfg_path} (tried repo default {DEFAULT_CONFIG_PATH})"
        )
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {cfg_path}")
    return data


def sampling_fps(config: Optional[Dict[str, Any]] = None) -> float:
    cfg = config if config is not None else load_config()
    fps = float((cfg.get("sampling") or {}).get("frames_per_second", 1.5))
    return max(0.1, min(fps, 30.0))


def window_seconds(config: Optional[Dict[str, Any]] = None) -> float:
    cfg = config if config is not None else load_config()
    return float((cfg.get("sampling") or {}).get("window_seconds", 30.0))


def yaw_threshold_deg(config: Optional[Dict[str, Any]] = None) -> float:
    cfg = config if config is not None else load_config()
    return float((cfg.get("orientation") or {}).get("yaw_threshold_deg", 30.0))


def tier1_yaw_threshold_deg(config: Optional[Dict[str, Any]] = None) -> float:
    cfg = config if config is not None else load_config()
    return float(
        (cfg.get("orientation") or {}).get("tier1_yaw_threshold_deg", 45.0)
    )


def pitch_down_threshold_deg(config: Optional[Dict[str, Any]] = None) -> float:
    cfg = config if config is not None else load_config()
    return float(
        (cfg.get("orientation") or {}).get("pitch_down_threshold_deg", 20.0)
    )


def face_width_min_px(config: Optional[Dict[str, Any]] = None) -> float:
    cfg = config if config is not None else load_config()
    return float((cfg.get("orientation") or {}).get("face_width_min_px", 80.0))


def min_coverage_pct(config: Optional[Dict[str, Any]] = None) -> float:
    cfg = config if config is not None else load_config()
    return float((cfg.get("coverage") or {}).get("min_coverage_pct", 70.0))


def min_usable_seats(config: Optional[Dict[str, Any]] = None) -> int:
    cfg = config if config is not None else load_config()
    return int((cfg.get("coverage") or {}).get("min_usable_seats", 5))


def resolve_model_path(path: str | Path | None) -> Path:
    """
    Resolve model weights relative to repo root (never process CWD).

    Relative names like ``yolov8n-pose.pt`` must not pick up a copy under
    ``backend/`` just because uvicorn's cwd makes ``Path.is_file()`` true.
    """
    if path is None or str(path).strip() == "":
        return REPO_ROOT / "models" / "face_landmarker.task"
    p = Path(path)
    if p.is_absolute():
        return p.resolve() if p.is_file() else p
    candidate = (REPO_ROOT / p).resolve()
    if candidate.is_file():
        return candidate
    by_name = (REPO_ROOT / "models" / p.name).resolve()
    if by_name.is_file():
        return by_name
    # Legacy: weights previously auto-downloaded into the API cwd
    cwd_hit = (Path.cwd() / p.name).resolve()
    if cwd_hit.is_file():
        return cwd_hit
    # Default download / missing path under models/
    return by_name
