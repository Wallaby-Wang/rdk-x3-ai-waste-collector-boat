from lakerboat.config import ControlConfig
from lakerboat.control import VisualServoController
from lakerboat.schema import Detection


def test_search_when_no_target():
    controller = VisualServoController(ControlConfig())
    decision = controller.update([], frame_size=(640, 480), now=10.0)
    assert decision.navigation.state == "SEARCH"
    assert decision.control.left > 0
    assert decision.control.right < 0


def test_align_left_when_target_is_left():
    controller = VisualServoController(ControlConfig())
    detection = Detection("plastic_bottle", "塑料瓶", 0.9, (80, 160, 160, 260))
    decision = controller.update([detection], frame_size=(640, 480), now=10.0)
    assert decision.navigation.state == "ALIGN"
    assert "左" in decision.navigation.heading
    assert decision.control.left < decision.control.right


def test_approach_when_target_centered():
    controller = VisualServoController(ControlConfig())
    detection = Detection("plastic_bottle", "塑料瓶", 0.9, (260, 160, 380, 320))
    decision = controller.update([detection], frame_size=(640, 480), now=10.0)
    assert decision.navigation.state in {"LOCKED", "APPROACH"}
    assert decision.control.left > 0
    assert decision.control.right > 0


def test_collect_when_target_area_is_large():
    controller = VisualServoController(ControlConfig())
    detection = Detection("plastic_bottle", "塑料瓶", 0.9, (170, 80, 470, 360))
    decision = controller.update([detection], frame_size=(640, 480), now=10.0)
    assert decision.navigation.state == "COLLECT"
    assert decision.control.pump is True
