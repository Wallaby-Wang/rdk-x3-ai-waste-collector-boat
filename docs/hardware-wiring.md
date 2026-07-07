# 硬件接线说明

本项目采用上下位机协同结构。RDK X3 负责摄像头、AI 推理和自动驾驶决策；ESP32-S3 负责实时 GPIO/PWM、电机驱动和灯带反馈。

## 1. RDK X3 与 ESP32-S3 UART

| RDK X3 | ESP32-S3 | 说明 |
| --- | --- | --- |
| 40Pin Pin 8 UART TX | GPIO18 RX | RDK 发送控制命令 |
| 40Pin Pin 10 UART RX | GPIO17 TX | ESP32 状态回传，可选但建议接 |
| 40Pin Pin 6 GND | GND | 两块板必须共地 |

注意：

- UART 为 3.3V TTL，不需要电平转换。
- 两套电源正极不互接，只连接 GND 作为通信参考地。

## 2. ESP32-S3 与 TB6612FNG

| ESP32-S3 | TB6612FNG | 说明 |
| --- | --- | --- |
| GPIO4 | STBY | 驱动使能，运行时拉高 |
| GPIO5 | AIN1 | 左电机方向 |
| GPIO6 | AIN2 | 左电机方向 |
| GPIO7 | PWMA | 左电机 PWM |
| GPIO15 | BIN1 | 右电机方向 |
| GPIO16 | BIN2 | 右电机方向 |
| GPIO8 | PWMB | 右电机 PWM |
| 3.3V | VCC | TB6612 逻辑电源 |
| GND | GND | 控制共地 |

电机电源：

- `VM` 接 7.4V 执行电池。
- `VCC` 接 ESP32-S3 3.3V 逻辑电源。
- `VM` 与 `VCC` 不可混接。

## 3. WS2812B 状态灯

| ESP32-S3 | WS2812B | 说明 |
| --- | --- | --- |
| GPIO10 | DIN | 单总线数据 |
| 5V | 5V | 灯带供电 |
| GND | GND | 与 ESP32 共地 |

颜色含义：

| 状态 | 颜色 | 含义 |
| --- | --- | --- |
| SEARCH | 绿色 | 搜索/巡航 |
| LOCKED / ALIGN / APPROACH / COLLECT | 蓝色 | 已识别目标并自动接近 |
| STOP / ERROR | 红色 | 停止、异常或需要人工干预 |

## 4. 水泵

第一版实物中水泵默认接执行侧 5V 电源，上电后用于辅助导流，不由 ESP32 直接开关。

固件保留 `PIN_PUMP`：

```cpp
static constexpr int PIN_PUMP = -1;
```

后续若增加 MOSFET 开关，将 `-1` 改成实际 GPIO，即可由串口帧中的 `pump` 字段控制。
