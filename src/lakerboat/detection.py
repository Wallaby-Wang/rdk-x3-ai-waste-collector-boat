from __future__ import annotations

from abc import ABC, abstractmethod
from math import sin
from time import monotonic
from typing import Any

from .config import DetectorConfig
from .schema import Detection


COCO_NAMES = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]


class Detector(ABC):
    @abstractmethod
    def detect(self, frame: Any) -> list[Detection]:
        raise NotImplementedError


class MockDetector(Detector):
    """Deterministic moving target for UI and CI demonstration."""

    def __init__(self, config: DetectorConfig) -> None:
        self.config = config
        self.started_at = monotonic()
        self.targets = [
            ("plastic_bottle", "塑料瓶", "bottle", 0.86, 1.0),
            ("paper_cup", "纸杯", "cup", 0.79, 0.95),
            ("black_bag", "塑料袋", "handbag", 0.73, 0.75),
        ]

    def detect(self, frame: Any) -> list[Detection]:
        height = getattr(frame, "shape", [480, 640])[0]
        width = getattr(frame, "shape", [480, 640])[1]
        phase = monotonic() - self.started_at
        cx = int(width * (0.5 + 0.32 * sin(phase / 2.4)))
        cy = int(height * 0.54)
        box_w = int(width * (0.12 + 0.04 * (1 + sin(phase / 3.1))))
        box_h = int(height * 0.18)
        idx = int(phase / 8) % len(self.targets)
        target_id, label, raw, confidence, priority = self.targets[idx]
        return [
            Detection(
                id=target_id,
                label=label,
                raw_label=raw,
                confidence=confidence,
                bbox=(
                    max(0, cx - box_w // 2),
                    max(0, cy - box_h // 2),
                    min(width - 1, cx + box_w // 2),
                    min(height - 1, cy + box_h // 2),
                ),
                priority=priority,
            )
        ]


class RDKYoloV5Detector(Detector):
    """YOLOv5 detector for D-Robotics RDK X3 Bernoulli2 BPU models."""

    def __init__(self, config: DetectorConfig) -> None:
        self.config = config
        self._np, self._cv2, self._dnn = self._imports()
        self.model = self._dnn.load(config.model_path)
        input_shape = self.model[0].inputs[0].properties.shape
        self.model_input_height = int(input_shape[2])
        self.model_input_width = int(input_shape[3])
        self._build_grids()

    @staticmethod
    def _imports() -> tuple[Any, Any, Any]:
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
            from hobot_dnn import pyeasy_dnn as dnn  # type: ignore
        except Exception as exc:  # pragma: no cover - requires RDK runtime
            raise RuntimeError(
                "RDK YOLO mode requires OpenCV, NumPy and hobot_dnn.pyeasy_dnn on the RDK X3."
            ) from exc
        return np, cv2, dnn

    def detect(self, frame: Any) -> list[Detection]:
        input_tensor = self._bgr_to_nv12(frame)
        outputs = [tensor.buffer for tensor in self.model[0].forward(input_tensor)]
        return self._postprocess(outputs, frame.shape[1], frame.shape[0])

    def _build_grids(self) -> None:
        np = self._np
        anchors = np.array(self.config.anchors).reshape(3, -1)
        self.grids = []
        self.anchor_grids = []
        for idx, stride in enumerate(self.config.strides):
            width = self.model_input_width // stride
            height = self.model_input_height // stride
            yy, xx = np.meshgrid(np.arange(height), np.arange(width), indexing="ij")
            grid = np.stack((xx, yy), axis=-1).reshape(-1, 2)
            self.grids.append(np.tile(grid, (3, 1)))
            self.anchor_grids.append(np.tile(anchors[idx], width * height).reshape(-1, 2))

    def _bgr_to_nv12(self, frame: Any) -> Any:
        np, cv2 = self._np, self._cv2
        resized = cv2.resize(
            frame,
            (self.model_input_width, self.model_input_height),
            interpolation=cv2.INTER_NEAREST,
        )
        area = self.model_input_height * self.model_input_width
        yuv420p = cv2.cvtColor(resized, cv2.COLOR_BGR2YUV_I420).reshape((area * 3 // 2,))
        y = yuv420p[:area]
        uv_planar = yuv420p[area:].reshape((2, area // 4))
        uv_packed = uv_planar.transpose((1, 0)).reshape((area // 2,))
        nv12 = np.zeros_like(yuv420p)
        nv12[:area] = y
        nv12[area:] = uv_packed
        return nv12

    def _postprocess(self, outputs: list[Any], image_width: int, image_height: int) -> list[Detection]:
        np, cv2 = self._np, self._cv2
        boxes = []
        scores = []
        class_ids = []
        for output, stride, grid, anchors in zip(
            outputs, self.config.strides, self.grids, self.anchor_grids, strict=False
        ):
            pred = output.reshape((-1, 5 + self.config.classes_num))
            objectness = _sigmoid_np(np, pred[:, 4])
            class_conf = _sigmoid_np(np, pred[:, 5:])
            best_class = np.argmax(class_conf, axis=1)
            best_score = objectness * class_conf[np.arange(class_conf.shape[0]), best_class]
            keep = np.flatnonzero(best_score >= self.config.conf_threshold)
            if keep.size == 0:
                continue
            xy = (_sigmoid_np(np, pred[keep, 0:2]) * 2.0 + grid[keep] - 0.5) * stride
            wh = (_sigmoid_np(np, pred[keep, 2:4]) * 2.0) ** 2 * anchors[keep]
            xyxy = np.concatenate([xy - wh / 2.0, xy + wh / 2.0], axis=1)
            boxes.extend(xyxy.tolist())
            scores.extend(best_score[keep].tolist())
            class_ids.extend(best_class[keep].tolist())

        if not boxes:
            return []

        indices = cv2.dnn.NMSBoxes(boxes, scores, self.config.conf_threshold, self.config.iou_threshold)
        if len(indices) == 0:
            return []

        x_scale = image_width / self.model_input_width
        y_scale = image_height / self.model_input_height
        detections: list[Detection] = []
        for raw_index in np.array(indices).reshape(-1):
            x1, y1, x2, y2 = boxes[int(raw_index)]
            class_id = int(class_ids[int(raw_index)])
            raw_label = COCO_NAMES[class_id] if class_id < len(COCO_NAMES) else str(class_id)
            mapped = self.config.target_classes.get(raw_label)
            if mapped is None:
                continue
            detections.append(
                Detection(
                    id=str(mapped.get("id", raw_label)),
                    label=str(mapped.get("label", raw_label)),
                    confidence=float(scores[int(raw_index)]),
                    bbox=(
                        int(max(0, x1 * x_scale)),
                        int(max(0, y1 * y_scale)),
                        int(min(image_width - 1, x2 * x_scale)),
                        int(min(image_height - 1, y2 * y_scale)),
                    ),
                    class_id=class_id,
                    raw_label=raw_label,
                    priority=float(mapped.get("priority", 1.0)),
                )
            )
        return detections


def _sigmoid_np(np: Any, value: Any) -> Any:
    return 1.0 / (1.0 + np.exp(-value))


def create_detector(config: DetectorConfig) -> Detector:
    if config.mode == "rdk_yolov5":
        return RDKYoloV5Detector(config)
    if config.mode == "mock":
        return MockDetector(config)
    raise ValueError(f"Unsupported detector mode: {config.mode}")
