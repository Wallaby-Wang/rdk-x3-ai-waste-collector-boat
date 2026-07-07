from __future__ import annotations

import threading
from time import monotonic, sleep, time

from .camera import create_frame_source, encode_jpeg
from .config import AppConfig
from .control import VisualServoController
from .detection import create_detector
from .schema import BoatStatus, CameraStatus
from .serial_link import SerialClient


class BoatRuntime:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.controller = VisualServoController(config.control)
        self.serial = SerialClient(config.serial, max_motor=config.control.max_motor)
        self.frame_source = create_frame_source(config.camera)
        self.detector = create_detector(config.detector)
        self.status = BoatStatus(serial=self.serial.status)
        self.latest_jpeg = encode_jpeg(None)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._frame_timestamps: list[float] = []

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="lakerboat-runtime", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self.frame_source.close()
        self.serial.close()

    def emergency_stop(self) -> None:
        self.controller.stop()
        decision = self.controller.update([], now=monotonic())
        self.serial.write(decision.control, decision.navigation, decision.light)
        with self._lock:
            self.status.control = decision.control
            self.status.navigation = decision.navigation
            self.status.light = decision.light
            self.status.serial = self.serial.status
            self.status.updated_at = time()

    def get_status(self) -> dict:
        with self._lock:
            return self.status.to_status()

    def get_latest_jpeg(self) -> bytes:
        with self._lock:
            return self.latest_jpeg

    def _loop(self) -> None:
        delay = max(0.01, 1.0 / max(1, self.config.camera.fps))
        while not self._stop.is_set():
            start = monotonic()
            self.step()
            elapsed = monotonic() - start
            sleep(max(0.0, delay - elapsed))

    def step(self) -> None:
        frame = self.frame_source.read()
        now = monotonic()
        if frame is None:
            decision = self.controller.update([], now=now)
            camera = CameraStatus(status="waiting", measured_fps=0.0, frame_count=self.status.camera.frame_count)
            detections = []
            jpeg = encode_jpeg(None)
        else:
            detections = self.detector.detect(frame)
            height, width = frame.shape[:2]
            decision = self.controller.update(detections, frame_size=(width, height), now=now)
            jpeg = encode_jpeg(frame, detections)
            self._frame_timestamps.append(now)
            self._frame_timestamps = [stamp for stamp in self._frame_timestamps if now - stamp <= 2.0]
            fps = len(self._frame_timestamps) / max(0.001, self._frame_timestamps[-1] - self._frame_timestamps[0] or 1.0)
            camera = CameraStatus(
                status="running",
                measured_fps=fps,
                frame_count=self.status.camera.frame_count + 1,
                last_frame_age_sec=0.0,
            )

        self.serial.write(decision.control, decision.navigation, decision.light)
        with self._lock:
            self.status.camera = camera
            self.status.serial = self.serial.status
            self.status.control = decision.control
            self.status.navigation = decision.navigation
            self.status.light = decision.light
            self.status.detections = detections
            self.status.updated_at = time()
            self.latest_jpeg = jpeg
