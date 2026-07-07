# 模型说明

## 1. 默认模型选择

RDK X3 默认使用 D-Robotics 官方 RDK Model Zoo 的 Bernoulli2 YOLOv5n 检测模型：

```text
models/yolov5n_tag_v7.0_detect_640x640_bernoulli2_nv12.bin
```

原因：

- RDK X3 官方 Model Zoo 明确提供 Bernoulli2 平台 YOLOv5 `.bin` 模型。
- YOLOv5n 体积小，适合比赛现场实时演示。
- 模型输入为 640 x 640 NV12，适合 RDK X3 摄像头链路。

可选模型：

```text
models/yolov5s_tag_v7.0_detect_640x640_bernoulli2_nv12.bin
```

YOLOv5s 检测能力更强，但推理负载更高。现场演示优先保证稳定帧率时建议使用 YOLOv5n。

## 2. 下载与校验

Windows：

```powershell
.\scripts\download_models.ps1
```

Linux / RDK：

```bash
bash scripts/download_models.sh
```

模型文件来自：

```text
https://archive.d-robotics.cc/downloads/rdk_model_zoo/rdk_x3/
```

下载后会生成：

```text
models/SHA256SUMS
```

## 3. 目标类别映射

官方模型是 COCO 80 类模型。本项目将适合水面垃圾演示的类别映射到比赛 UI 和控制逻辑：

| COCO 类别 | 项目 ID | UI 标签 | 用途 |
| --- | --- | --- | --- |
| `bottle` | `plastic_bottle` | 塑料瓶 | 主要目标 |
| `cup` | `paper_cup` | 纸杯 | 主要目标 |
| `sports ball` / `orange` | `orange_ball` | 球状漂浮物 | 调试目标 |
| `handbag` / `backpack` | `black_bag` | 塑料袋 | 替代袋状目标 |

映射在 `src/lakerboat/config.py` 的 `DEFAULT_TARGET_CLASSES` 中，也可以在 YAML 中覆盖。

## 4. 后续自训练方向

如果需要针对真实漂浮垃圾进一步优化，可以：

1. 采集水池和人工湖场景下的瓶子、纸杯、泡沫块、塑料袋图片。
2. 使用 YOLO 格式标注数据集。
3. 基于 Ultralytics YOLOv5n/YOLOv5s 微调。
4. 导出 ONNX 并使用 D-Robotics 工具链量化为 Bernoulli2 `.bin`。
5. 替换 `config/rdk_x3.yaml` 中的 `detector.model_path`。

本仓库默认不伪造自训练结果；当前权重来自官方公开模型，便于复现。
