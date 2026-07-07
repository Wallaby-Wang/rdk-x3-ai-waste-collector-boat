#pragma once

// RDK X3 UART3 Pin 8 TX -> ESP32-S3 GPIO18 RX
// RDK X3 UART3 Pin 10 RX <- ESP32-S3 GPIO17 TX
// RDK X3 Pin 6 GND must share ground with ESP32-S3.
static constexpr int UART_RX_PIN = 18;
static constexpr int UART_TX_PIN = 17;
static constexpr unsigned long UART_BAUD = 115200;

// TB6612FNG dual motor driver.
static constexpr int PIN_STBY = 4;
static constexpr int PIN_AIN1 = 5;
static constexpr int PIN_AIN2 = 6;
static constexpr int PIN_PWMA = 7;
static constexpr int PIN_BIN1 = 15;
static constexpr int PIN_BIN2 = 16;
static constexpr int PIN_PWMB = 8;

static constexpr int LEFT_PWM_CHANNEL = 0;
static constexpr int RIGHT_PWM_CHANNEL = 1;
static constexpr int PWM_FREQ = 20000;
static constexpr int PWM_RESOLUTION = 8;
static constexpr int PWM_MAX = 255;

// WS2812B state strip. The report uses 8 LEDs for low-brightness display.
static constexpr int PIN_WS2812 = 10;
static constexpr int LED_COUNT = 8;
static constexpr int LED_BRIGHTNESS = 40;

// The first hardware build powers the pump directly.
// Set to a GPIO number if a MOSFET pump switch is added later.
static constexpr int PIN_PUMP = -1;

static constexpr unsigned long COMMAND_TIMEOUT_MS = 900;
