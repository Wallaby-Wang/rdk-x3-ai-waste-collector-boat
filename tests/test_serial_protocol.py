from lakerboat.schema import ControlOutput, LightOutput, NavigationOutput
from lakerboat.serial_link import format_control_frame, format_legacy_command, scale_motor


def test_scale_motor_to_esp32_pwm_range():
    assert scale_motor(100) == 255
    assert scale_motor(-100) == -255
    assert scale_motor(20) == 51


def test_format_full_control_frame():
    frame = format_control_frame(
        ControlOutput(left=20, right=35, pump=False),
        NavigationOutput(state="APPROACH", heading="前进接近"),
        LightOutput(enabled=True, color="blue"),
    )
    assert frame == "<A,51,89,APPROACH,2,0>\n"


def test_legacy_align_direction():
    left = format_legacy_command(NavigationOutput(state="ALIGN", heading="左转微调", error_x=-0.3))
    right = format_legacy_command(NavigationOutput(state="ALIGN", heading="右转微调", error_x=0.3))
    assert left == "LEFT\n"
    assert right == "RIGHT\n"
