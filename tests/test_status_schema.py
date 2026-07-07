from lakerboat.schema import BoatStatus, Detection


def test_status_shape_matches_dashboard_contract():
    status = BoatStatus()
    status.detections = [Detection("plastic_bottle", "塑料瓶", 0.81, (1, 2, 3, 4))]
    data = status.to_status()
    assert set(data) >= {"camera", "serial", "control", "light", "navigation", "detections"}
    assert data["detections"][0]["label"] == "塑料瓶"
    assert data["detections"][0]["bbox"] == [1, 2, 3, 4]
