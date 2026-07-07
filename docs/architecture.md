# 软件架构

## RDK X3 端

`src/lakerboat` 分为几个稳定边界：

- `camera.py`：真实摄像头或 mock 画面输入。
- `detection.py`：RDK YOLOv5 BPU 推理或 mock detection。
- `control.py`：目标选择与视觉伺服状态机。
- `serial_link.py`：RDK 到 ESP32-S3 的 UART 帧编码与发送。
- `runtime.py`：采集、推理、控制、推流的后台循环。
- `app.py`：FastAPI HTTP、MJPEG 和 UI 注入。

## 状态机

| 状态 | 触发条件 | 输出 |
| --- | --- | --- |
| SEARCH | 无可信目标或目标长时间丢失 | 低速差速搜索，绿灯 |
| LOCKED | 发现目标但距离较远 | 低速前进并轻微修正，蓝灯 |
| ALIGN | 横向误差超过阈值 | 左/右差速转向，蓝灯 |
| APPROACH | 目标居中且面积达到接近阈值 | 前进接近，蓝灯 |
| COLLECT | 目标面积达到收集阈值 | 低速推进，水泵请求开启，蓝灯 |
| RETRY | 刚丢失目标 | 短暂搜索重试，蓝灯 |
| STOP | 人工急停或固件超时 | 电机停转，红灯 |
| ERROR | 预留异常状态 | 停车，红灯 |

## UI 接入

`ui/Target-UI.html` 是比赛展示大屏。后端返回 `/` 时会注入：

```js
window.LeftDashboard.configure({
  statusUrl: "/api/status",
  streamUrl: "/stream.mjpg",
  logoSrc: "/Logo.png",
  pollMs: 700
});
```

这样既保留现有 UI 文件，又让大屏能够接真实后端。
