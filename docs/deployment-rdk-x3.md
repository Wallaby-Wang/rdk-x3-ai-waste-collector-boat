# RDK X3 部署说明

本文说明如何把 RDK X3 端服务部署到真实船体。无硬件调试请先使用 `config/demo.yaml`。

## 1. 系统准备

推荐环境：

- RDK X3 / RDK X3 Module
- Ubuntu 20.04 或 Ubuntu 22.04 RDK 系统
- IMX219 MIPI 摄像头或兼容 V4L2 摄像头
- RDK 系统已包含 `hobot_dnn.pyeasy_dnn`
- Python 3.10+

安装基础依赖：

```bash
sudo apt update
sudo apt install -y git python3-pip python3-opencv
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

如果 OpenCV 已由 RDK 系统提供，不需要安装 `opencv-python-headless`。

## 2. 下载模型

```bash
bash scripts/download_models.sh
cat models/SHA256SUMS
```

检查模型能否被 RDK BPU runtime 加载：

```bash
python3 scripts/rdk_model_smoke.py
```

如果提示 `hobot_dnn.pyeasy_dnn is only available on the RDK X3 runtime`，说明当前不是 RDK X3 板端环境。

## 3. 摄像头检查

常规 V4L2 摄像头：

```bash
ls /dev/video*
python3 - <<'PY'
import cv2
cap = cv2.VideoCapture(0)
ok, frame = cap.read()
print("ok=", ok, "shape=", None if frame is None else frame.shape)
PY
```

如果 RDK 镜像需要 GStreamer 管线，请在 `config/rdk_x3.yaml` 的 `camera.gstreamer` 中填写，并保持 `camera.mode: opencv`。

## 4. 串口检查

默认配置：

- RDK X3 UART3 TX Pin 8 -> ESP32-S3 GPIO18 RX
- RDK X3 UART3 RX Pin 10 <- ESP32-S3 GPIO17 TX
- RDK X3 Pin 6 GND -> ESP32-S3 GND
- 波特率：115200

检查串口设备：

```bash
ls /dev/ttyS* /dev/ttyUSB* 2>/dev/null
```

如果设备名不同，修改 `config/rdk_x3.yaml`：

```yaml
serial:
  port: /dev/ttyS3
  baudrate: 115200
```

## 5. 启动服务

```bash
lakerboat run --config config/rdk_x3.yaml
```

浏览器打开：

```text
http://<rdk-ip>:8000
```

UI 会自动读取：

- `/stream.mjpg` 实时视频
- `/api/status` 控制、检测、FPS、串口和灯带状态

## 6. 常见问题

### 页面打开但没有画面

先切换到 demo：

```bash
lakerboat run --config config/demo.yaml
```

如果 demo 正常，问题通常在摄像头驱动或 `camera.device`。

### 状态显示硬件异常

检查 `serial.dry_run` 是否为 `false`，并确认 RDK 与 ESP32-S3 只共地，不共接两套电源正极。

### 模型无法加载

确认使用的是 RDK X3 Bernoulli2 模型：

```text
models/yolov5n_tag_v7.0_detect_640x640_bernoulli2_nv12.bin
```

不要把 RDK X5 Bayes-e 模型放到 X3 配置中。

## 7. systemd 可选服务

创建 `/etc/systemd/system/lakerboat.service`：

```ini
[Unit]
Description=Laker RDK X3 AI waste collector boat
After=network.target

[Service]
WorkingDirectory=/home/sunrise/rdk-x3-ai-waste-collector-boat
ExecStart=/usr/bin/python3 -m lakerboat run --config config/rdk_x3.yaml
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now lakerboat
sudo journalctl -u lakerboat -f
```
