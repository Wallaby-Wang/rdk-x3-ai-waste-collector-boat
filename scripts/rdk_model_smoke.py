from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Load an RDK X3 BPU model with hobot_dnn.")
    parser.add_argument(
        "model",
        nargs="?",
        default="models/yolov5n_tag_v7.0_detect_640x640_bernoulli2_nv12.bin",
    )
    args = parser.parse_args()
    model_path = Path(args.model)
    if not model_path.exists():
        raise SystemExit(f"Model file not found: {model_path}")

    try:
        from hobot_dnn import pyeasy_dnn as dnn  # type: ignore
    except Exception as exc:
        raise SystemExit("hobot_dnn.pyeasy_dnn is only available on the RDK X3 runtime.") from exc

    models = dnn.load(str(model_path))
    model = models[0]
    print(f"loaded: {model_path}")
    for idx, tensor in enumerate(model.inputs):
        print(f"input[{idx}] name={tensor.name} shape={tensor.properties.shape} dtype={tensor.properties.dtype}")
    for idx, tensor in enumerate(model.outputs):
        print(f"output[{idx}] name={tensor.name} shape={tensor.properties.shape} dtype={tensor.properties.dtype}")


if __name__ == "__main__":
    main()
