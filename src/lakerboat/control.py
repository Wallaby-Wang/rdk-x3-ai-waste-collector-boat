from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from .config import ControlConfig
from .schema import ControlOutput, Decision, Detection, LightOutput, NavigationOutput, clamp_int


@dataclass(slots=True)
class TargetGeometry:
    detection: Detection
    error_x: float
    area_ratio: float


def choose_primary_target(
    detections: list[Detection], frame_size: tuple[int, int], min_confidence: float
) -> TargetGeometry | None:
    width, height = frame_size
    frame_area = max(1, width * height)
    candidates: list[TargetGeometry] = []
    for detection in detections:
        if detection.confidence < min_confidence:
            continue
        cx, _ = detection.center
        error_x = ((cx / max(1, width)) - 0.5) * 2.0
        area_ratio = detection.area / frame_area
        candidates.append(TargetGeometry(detection, error_x, area_ratio))

    if not candidates:
        return None

    def score(target: TargetGeometry) -> float:
        center_bonus = 1.0 - min(1.0, abs(target.error_x))
        return (
            target.detection.confidence * 1.7
            + target.area_ratio * 2.6
            + center_bonus * 0.35
        ) * target.detection.priority

    return max(candidates, key=score)


class VisualServoController:
    """Small-water-area visual servo state machine.

    The controller intentionally keeps the algorithm explainable: one primary
    target, one horizontal image error, one area-based distance proxy, and a
    small number of states that match the project report.
    """

    def __init__(self, config: ControlConfig) -> None:
        self.config = config
        self._state = "SEARCH"
        self._last_seen_at = 0.0
        self._manual_stop = False

    @property
    def state(self) -> str:
        return self._state

    def stop(self) -> None:
        self._manual_stop = True
        self._state = "STOP"

    def resume(self) -> None:
        self._manual_stop = False
        self._state = "SEARCH"

    def update(
        self,
        detections: list[Detection],
        frame_size: tuple[int, int] | None = None,
        now: float | None = None,
    ) -> Decision:
        now = monotonic() if now is None else now
        frame_size = frame_size or (self.config.frame_width, self.config.frame_height)

        if self._manual_stop:
            return self._decision("STOP", "人工停止", "", 0.0, 0.0, 0, 0, "red", False)

        target = choose_primary_target(detections, frame_size, self.config.min_confidence)
        if target is None:
            lost_for = now - self._last_seen_at if self._last_seen_at else 999.0
            self._state = "RETRY" if lost_for < self.config.target_lost_timeout_sec else "SEARCH"
            if self._state == "RETRY":
                return self._decision("RETRY", "目标丢失重试", "", 0.0, 0.0, 22, -22, "blue", False)
            return self._decision(
                "SEARCH",
                "巡航搜索",
                "",
                0.0,
                0.0,
                self.config.search_left,
                self.config.search_right,
                "green",
                False,
            )

        self._last_seen_at = now
        error = target.error_x
        area = target.area_ratio
        label = target.detection.label

        if area >= self.config.collect_area_ratio:
            self._state = "COLLECT"
            return self._decision(
                "COLLECT",
                "低速收集",
                label,
                error,
                area,
                self.config.collect_speed,
                self.config.collect_speed,
                "blue",
                True,
            )

        if abs(error) > self.config.align_deadband:
            self._state = "ALIGN"
            if error < 0:
                left = -self.config.turn_speed * 0.35
                right = self.config.turn_speed
                heading = "左转微调"
            else:
                left = self.config.turn_speed
                right = -self.config.turn_speed * 0.35
                heading = "右转微调"
            return self._decision("ALIGN", heading, label, error, area, left, right, "blue", False)

        self._state = "APPROACH" if area >= self.config.approach_area_ratio else "LOCKED"
        correction = self.config.steer_gain * error
        base = self.config.approach_speed if self._state == "APPROACH" else self.config.approach_speed * 0.72
        left = base + correction
        right = base - correction
        heading = "前进接近" if self._state == "APPROACH" else "目标锁定"
        return self._decision(self._state, heading, label, error, area, left, right, "blue", False)

    def _decision(
        self,
        state: str,
        heading: str,
        primary_target: str,
        error_x: float,
        area_ratio: float,
        left: float,
        right: float,
        light_color: str,
        pump: bool,
    ) -> Decision:
        control = ControlOutput(
            left=clamp_int(left, -self.config.max_motor, self.config.max_motor),
            right=clamp_int(right, -self.config.max_motor, self.config.max_motor),
            pump=pump,
        )
        light = LightOutput(enabled=True, color=light_color, hardware_status="open")
        nav = NavigationOutput(
            state=state,
            heading=heading,
            primary_target=primary_target,
            error_x=error_x,
            area_ratio=area_ratio,
        )
        return Decision(navigation=nav, control=control, light=light)
