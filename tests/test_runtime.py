from lakerboat.config import AppConfig
from lakerboat.runtime import BoatRuntime
from lakerboat.schema import ControlOutput, Decision, LightOutput, NavigationOutput


class RecordingSerial:
    def __init__(self) -> None:
        self.commands = []

    def write(self, control, navigation, light) -> None:
        self.commands.append((control, navigation, light))


def make_decision(state: str = "APPROACH") -> Decision:
    return Decision(
        navigation=NavigationOutput(state=state),
        control=ControlOutput(left=20, right=20),
        light=LightOutput(enabled=True, color="blue"),
    )


def test_runtime_throttles_regular_control_frames():
    runtime = BoatRuntime(AppConfig())
    recorder = RecordingSerial()
    runtime.serial = recorder
    runtime.config.serial.control_hz = 10

    runtime._write_control_if_due(make_decision(), now=10.0)
    runtime._write_control_if_due(make_decision(), now=10.05)
    runtime._write_control_if_due(make_decision(), now=10.11)

    assert len(recorder.commands) == 2


def test_runtime_sends_stop_immediately():
    runtime = BoatRuntime(AppConfig())
    recorder = RecordingSerial()
    runtime.serial = recorder
    runtime.config.serial.control_hz = 1

    runtime._write_control_if_due(make_decision(), now=10.0)
    runtime._write_control_if_due(make_decision("STOP"), now=10.01)

    assert [command[1].state for command in recorder.commands] == ["APPROACH", "STOP"]
