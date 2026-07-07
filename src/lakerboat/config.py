from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class CameraConfig:
    mode: str = "mock"
    device: int | str = 0
    width: int = 640
    height: int = 480
    fps: int = 20
    gstreamer: str | None = None


@dataclass(slots=True)
class DetectorConfig:
    mode: str = "mock"
    model_path: str = "models/yolov5n_tag_v7.0_detect_640x640_bernoulli2_nv12.bin"
    conf_threshold: float = 0.35
    iou_threshold: float = 0.45
    classes_num: int = 80
    anchors: list[int] = field(
        default_factory=lambda: [
            10,
            13,
            16,
            30,
            33,
            23,
            30,
            61,
            62,
            45,
            59,
            119,
            116,
            90,
            156,
            198,
            373,
            326,
        ]
    )
    strides: list[int] = field(default_factory=lambda: [8, 16, 32])
    target_classes: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(slots=True)
class ControlConfig:
    frame_width: int = 640
    frame_height: int = 480
    align_deadband: float = 0.18
    approach_area_ratio: float = 0.12
    collect_area_ratio: float = 0.22
    target_lost_timeout_sec: float = 1.2
    search_left: int = 34
    search_right: int = -28
    approach_speed: int = 58
    collect_speed: int = 28
    turn_speed: int = 54
    min_confidence: float = 0.35
    steer_gain: float = 44.0
    max_motor: int = 100


@dataclass(slots=True)
class SerialConfig:
    enabled: bool = False
    port: str = "/dev/ttyS3"
    baudrate: int = 115200
    timeout_sec: float = 0.02
    dry_run: bool = True


@dataclass(slots=True)
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    poll_ms: int = 700
    ui_path: str = "ui/Target-UI.html"
    logo_path: str = "ui/Logo.png"


@dataclass(slots=True)
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    control: ControlConfig = field(default_factory=ControlConfig)
    serial: SerialConfig = field(default_factory=SerialConfig)
    server: ServerConfig = field(default_factory=ServerConfig)


DEFAULT_TARGET_CLASSES: dict[str, dict[str, Any]] = {
    "bottle": {"id": "plastic_bottle", "label": "塑料瓶", "priority": 1.0},
    "cup": {"id": "paper_cup", "label": "纸杯", "priority": 0.95},
    "sports ball": {"id": "orange_ball", "label": "球状漂浮物", "priority": 0.8},
    "orange": {"id": "orange_ball", "label": "球状漂浮物", "priority": 0.7},
    "handbag": {"id": "black_bag", "label": "塑料袋", "priority": 0.75},
    "backpack": {"id": "black_bag", "label": "塑料袋", "priority": 0.7},
}


def _deep_update(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def _dataclass_to_dict(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return {key: _dataclass_to_dict(getattr(obj, key)) for key in obj.__dataclass_fields__}
    if isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _dataclass_to_dict(value) for key, value in obj.items()}
    return obj


def load_config(path: str | Path | None = None) -> AppConfig:
    data = _dataclass_to_dict(AppConfig())
    data["detector"]["target_classes"] = DEFAULT_TARGET_CLASSES.copy()

    if path:
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with config_path.open("r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh) or {}
        _deep_update(data, loaded)

    return AppConfig(
        camera=CameraConfig(**data["camera"]),
        detector=DetectorConfig(**data["detector"]),
        control=ControlConfig(**data["control"]),
        serial=SerialConfig(**data["serial"]),
        server=ServerConfig(**data["server"]),
    )
