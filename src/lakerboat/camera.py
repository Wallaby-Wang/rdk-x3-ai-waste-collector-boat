from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from math import sin
from time import monotonic
from typing import Any

from .config import CameraConfig
from .schema import Detection


PLACEHOLDER_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
    "2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAA"
    "AAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/ASP/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/ASP/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/Al//xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//2gAMAwEAAgADAAAAEP/EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQMBAT8QH//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QH//EABQQAQAAAAAAAAAAAAAAAAAAABD/2gAIAQEAAT8QH//Z"
)


class FrameSource(ABC):
    @abstractmethod
    def read(self) -> Any | None:
        raise NotImplementedError

    def close(self) -> None:
        return None


class OpenCVFrameSource(FrameSource):
    def __init__(self, config: CameraConfig) -> None:
        try:
            import cv2  # type: ignore
        except Exception as exc:  # pragma: no cover - environment-specific
            raise RuntimeError("OpenCV is required for real camera mode.") from exc
        self._cv2 = cv2
        source = config.gstreamer or config.device
        if config.gstreamer:
            self.capture = cv2.VideoCapture(source, cv2.CAP_GSTREAMER)
        else:
            self.capture = cv2.VideoCapture(source)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)
        self.capture.set(cv2.CAP_PROP_FPS, config.fps)

    def read(self) -> Any | None:
        ok, frame = self.capture.read()
        return frame if ok else None

    def close(self) -> None:
        self.capture.release()


class MockFrameSource(FrameSource):
    def __init__(self, config: CameraConfig) -> None:
        self.config = config
        self.started_at = monotonic()

    def read(self) -> Any | None:
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
        except Exception:
            return None

        width = self.config.width
        height = self.config.height
        t = monotonic() - self.started_at
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (228, 238, 246)
        for y in range(40, height, 64):
            cv2.line(frame, (0, y), (width, y + int(10 * sin(t))), (190, 215, 235), 2)
        cx = int(width * (0.5 + 0.32 * sin(t / 2.4)))
        cy = int(height * 0.54)
        cv2.rectangle(frame, (cx - 42, cy - 34), (cx + 42, cy + 34), (35, 90, 45), -1)
        cv2.putText(
            frame,
            "MOCK WATER TARGET",
            (22, 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (18, 86, 160),
            2,
            cv2.LINE_AA,
        )
        return frame


def create_frame_source(config: CameraConfig) -> FrameSource:
    if config.mode == "opencv":
        return OpenCVFrameSource(config)
    if config.mode == "mock":
        return MockFrameSource(config)
    raise ValueError(f"Unsupported camera mode: {config.mode}")


def encode_jpeg(frame: Any, detections: list[Detection] | None = None) -> bytes:
    if frame is None:
        return PLACEHOLDER_JPEG
    try:
        import cv2  # type: ignore
    except Exception:
        return PLACEHOLDER_JPEG

    rendered = frame.copy()
    for detection in detections or []:
        x1, y1, x2, y2 = detection.bbox
        cv2.rectangle(rendered, (x1, y1), (x2, y2), (20, 117, 255), 2)
        label = f"{detection.label} {detection.confidence:.2f}"
        cv2.putText(rendered, label, (x1, max(22, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (20, 117, 255), 2)
    ok, encoded = cv2.imencode(".jpg", rendered, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
    return encoded.tobytes() if ok else PLACEHOLDER_JPEG
