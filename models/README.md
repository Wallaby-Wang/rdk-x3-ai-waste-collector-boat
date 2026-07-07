# Model Assets

This project uses D-Robotics official RDK X3 Bernoulli2 YOLOv5 BPU models.

Default runtime model:

- `yolov5n_tag_v7.0_detect_640x640_bernoulli2_nv12.bin`

Optional higher-capacity model:

- `yolov5s_tag_v7.0_detect_640x640_bernoulli2_nv12.bin`

The models are downloaded by `scripts/download_models.ps1` or `scripts/download_models.sh`.
Checksums are written to `models/SHA256SUMS`.

Source:

- https://github.com/D-Robotics/rdk_model_zoo/tree/rdk_x3/demos/detect/YOLOv5
- https://archive.d-robotics.cc/downloads/rdk_model_zoo/rdk_x3/
