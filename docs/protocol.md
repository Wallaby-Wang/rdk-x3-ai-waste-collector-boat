# 协议说明

本项目有两层接口：

- 浏览器 UI 与 RDK X3 后端之间使用 HTTP/JSON/MJPEG。
- RDK X3 与 ESP32-S3 之间使用 115200 bps UART。

## 1. HTTP 接口

### `GET /api/status`

返回 UI 直接使用的状态对象：

```json
{
  "camera": {
    "status": "running",
    "measured_fps": 20.0,
    "frame_count": 1,
    "last_frame_age_sec": 0.1
  },
  "serial": {
    "mode": "direct",
    "status": "open",
    "last_command": "<A,51,89,APPROACH,2,0>"
  },
  "control": {
    "left": 20,
    "right": 35,
    "pump": false
  },
  "light": {
    "enabled": true,
    "color": "blue",
    "hardware_status": "open"
  },
  "navigation": {
    "state": "APPROACH",
    "heading": "前进接近",
    "primary_target": "塑料瓶",
    "error_x": -0.08,
    "area_ratio": 0.14
  },
  "detections": [
    {
      "id": "plastic_bottle",
      "label": "塑料瓶",
      "confidence": 0.81,
      "bbox": [120, 90, 260, 320]
    }
  ]
}
```

### `GET /stream.mjpg`

返回 multipart MJPEG 视频流。后端会在画面中绘制检测框和标签。

### `POST /api/control/stop`

立即进入 `STOP` 状态并向 ESP32-S3 下发停车命令。

## 2. UART 主协议

格式：

```text
<A,left,right,state,light,pump>\n
```

字段：

| 字段 | 范围 | 说明 |
| --- | --- | --- |
| `left` | -255..255 | 左推进电机 PWM，负数为反转 |
| `right` | -255..255 | 右推进电机 PWM，负数为反转 |
| `state` | 文本 | `SEARCH`、`ALIGN`、`APPROACH` 等状态 |
| `light` | 0..3 | 0 关灯，1 绿，2 蓝，3 红 |
| `pump` | 0/1 | 水泵开关请求 |

例子：

```text
<A,51,89,APPROACH,2,0>
<A,-48,138,ALIGN,2,0>
<A,72,72,COLLECT,2,1>
<A,0,0,STOP,3,0>
```

ESP32-S3 会回传状态：

```text
<S,state,left,right,pump>
```

## 3. 兼容短命令

固件兼容调试阶段短命令：

```text
SEARCH
LEFT
RIGHT
FORWARD
COLLECT
STOP
```

这些命令用于串口助手单测；正式运行建议使用完整 `<A,...>` 帧。
