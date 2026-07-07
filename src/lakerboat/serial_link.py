from __future__ import annotations

from dataclasses import dataclass, field

from .config import SerialConfig
from .schema import ControlOutput, LightOutput, NavigationOutput, SerialStatus, clamp_int


LIGHT_CODES = {
    "off": 0,
    "green": 1,
    "blue": 2,
    "red": 3,
}

LEGACY_COMMANDS = {
    "SEARCH": "SEARCH",
    "RETRY": "SEARCH",
    "LOCKED": "FORWARD",
    "ALIGN": "LEFT",
    "APPROACH": "FORWARD",
    "COLLECT": "COLLECT",
    "STOP": "STOP",
    "ERROR": "STOP",
}


def scale_motor(value: int, source_max: int = 100, target_max: int = 255) -> int:
    return clamp_int((value / max(1, source_max)) * target_max, -target_max, target_max)


def format_control_frame(
    control: ControlOutput, navigation: NavigationOutput, light: LightOutput, source_max: int = 100
) -> str:
    left = scale_motor(control.left, source_max=source_max)
    right = scale_motor(control.right, source_max=source_max)
    light_code = LIGHT_CODES.get(light.color, 0) if light.enabled else 0
    pump = 1 if control.pump else 0
    return f"<A,{left},{right},{navigation.state},{light_code},{pump}>\n"


def format_legacy_command(navigation: NavigationOutput) -> str:
    if navigation.state == "ALIGN":
        return "LEFT\n" if navigation.error_x < 0 else "RIGHT\n"
    return f"{LEGACY_COMMANDS.get(navigation.state, 'STOP')}\n"


@dataclass(slots=True)
class SerialClient:
    config: SerialConfig
    max_motor: int = 100
    status: SerialStatus = field(init=False)
    _serial: object | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        self.status = SerialStatus(mode="mock", status="disabled", last_command="")
        if not self.config.enabled:
            return
        if self.config.dry_run:
            self.status = SerialStatus(mode="mock", status="open", last_command="")
            return

        try:
            import serial  # type: ignore

            self._serial = serial.Serial(
                self.config.port,
                self.config.baudrate,
                timeout=self.config.timeout_sec,
                write_timeout=self.config.timeout_sec,
            )
            self.status = SerialStatus(mode="direct", status="open", last_command="")
        except Exception as exc:  # pragma: no cover - depends on hardware
            self.status = SerialStatus(mode="direct", status=f"error: {exc}", last_command="")

    def write(self, control: ControlOutput, navigation: NavigationOutput, light: LightOutput) -> str:
        frame = format_control_frame(control, navigation, light, source_max=self.max_motor)
        self.status.last_command = frame.strip()
        if self._serial is not None:  # pragma: no cover - depends on hardware
            try:
                self._serial.write(frame.encode("utf-8"))
                self.status.status = "open"
            except Exception as exc:
                self.status.status = f"error: {exc}"
        return frame

    def close(self) -> None:
        if self._serial is not None:  # pragma: no cover - depends on hardware
            self._serial.close()
        if self.config.enabled:
            self.status.status = "closed"
