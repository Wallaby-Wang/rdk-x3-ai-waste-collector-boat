from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any


BBox = tuple[int, int, int, int]


def clamp_int(value: float | int, low: int, high: int) -> int:
    return max(low, min(high, int(round(value))))


@dataclass(slots=True, frozen=True)
class Detection:
    id: str
    label: str
    confidence: float
    bbox: BBox
    class_id: int | None = None
    raw_label: str | None = None
    priority: float = 1.0

    @property
    def area(self) -> int:
        x1, y1, x2, y2 = self.bbox
        return max(0, x2 - x1) * max(0, y2 - y1)

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def to_status(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "confidence": round(float(self.confidence), 4),
            "bbox": list(self.bbox),
        }


@dataclass(slots=True, frozen=True)
class ControlOutput:
    left: int = 0
    right: int = 0
    pump: bool = False

    def limited(self, max_abs: int = 100) -> "ControlOutput":
        return ControlOutput(
            left=clamp_int(self.left, -max_abs, max_abs),
            right=clamp_int(self.right, -max_abs, max_abs),
            pump=self.pump,
        )

    def to_status(self) -> dict[str, Any]:
        return {"left": self.left, "right": self.right, "pump": self.pump}


@dataclass(slots=True, frozen=True)
class LightOutput:
    enabled: bool = False
    color: str = "green"
    hardware_status: str = "mock"

    def to_status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "color": self.color,
            "hardware_status": self.hardware_status,
        }


@dataclass(slots=True, frozen=True)
class NavigationOutput:
    state: str = "SEARCH"
    heading: str = "巡航搜索"
    primary_target: str = ""
    error_x: float = 0.0
    area_ratio: float = 0.0
    manual_action: str | None = None

    def to_status(self) -> dict[str, Any]:
        data = {
            "state": self.state,
            "heading": self.heading,
            "primary_target": self.primary_target,
            "error_x": round(self.error_x, 4),
            "area_ratio": round(self.area_ratio, 4),
        }
        if self.manual_action:
            data["manual_action"] = self.manual_action
        return data


@dataclass(slots=True, frozen=True)
class Decision:
    navigation: NavigationOutput
    control: ControlOutput
    light: LightOutput


@dataclass(slots=True)
class CameraStatus:
    status: str = "starting"
    measured_fps: float = 0.0
    frame_count: int = 0
    last_frame_age_sec: float = 999.0

    def to_status(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "measured_fps": round(self.measured_fps, 2),
            "frame_count": self.frame_count,
            "last_frame_age_sec": round(self.last_frame_age_sec, 3),
        }


@dataclass(slots=True)
class SerialStatus:
    mode: str = "mock"
    status: str = "closed"
    last_command: str = ""

    def to_status(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "status": self.status,
            "last_command": self.last_command,
        }


@dataclass(slots=True)
class BoatStatus:
    camera: CameraStatus = field(default_factory=CameraStatus)
    serial: SerialStatus = field(default_factory=SerialStatus)
    control: ControlOutput = field(default_factory=ControlOutput)
    light: LightOutput = field(default_factory=LightOutput)
    navigation: NavigationOutput = field(default_factory=NavigationOutput)
    detections: list[Detection] = field(default_factory=list)
    updated_at: float = field(default_factory=time)

    def to_status(self) -> dict[str, Any]:
        return {
            "camera": self.camera.to_status(),
            "serial": self.serial.to_status(),
            "control": self.control.to_status(),
            "light": self.light.to_status(),
            "navigation": self.navigation.to_status(),
            "detections": [item.to_status() for item in self.detections],
            "updated_at": round(self.updated_at, 3),
        }
