#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

#include "board_config.h"
#include "protocol.h"

HardwareSerial RdkSerial(1);
Adafruit_NeoPixel strip(LED_COUNT, PIN_WS2812, NEO_GRB + NEO_KHZ800);

ControlCommand currentCommand;
unsigned long lastCommandAt = 0;
String lineBuffer;

void setMotor(int value, int in1, int in2, int pwmPin, int channel) {
  value = clampPwm(value);
  if (value > 0) {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
  } else if (value < 0) {
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
  } else {
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
  }
  ledcWrite(channel, abs(value));
}

void applyLight(int code) {
  uint32_t color = strip.Color(0, 0, 0);
  if (code == 1) color = strip.Color(0, 120, 0);
  if (code == 2) color = strip.Color(0, 0, 140);
  if (code == 3) color = strip.Color(150, 0, 0);
  for (int i = 0; i < LED_COUNT; ++i) {
    strip.setPixelColor(i, color);
  }
  strip.show();
}

void applyCommand(const ControlCommand& command) {
  digitalWrite(PIN_STBY, HIGH);
  setMotor(command.left, PIN_AIN1, PIN_AIN2, PIN_PWMA, LEFT_PWM_CHANNEL);
  setMotor(command.right, PIN_BIN1, PIN_BIN2, PIN_PWMB, RIGHT_PWM_CHANNEL);
  applyLight(command.light);
  if (PIN_PUMP >= 0) {
    digitalWrite(PIN_PUMP, command.pump ? HIGH : LOW);
  }
}

void stopActuators() {
  ControlCommand stop;
  stop.left = 0;
  stop.right = 0;
  stop.state = "STOP";
  stop.light = 3;
  stop.valid = true;
  currentCommand = stop;
  applyCommand(currentCommand);
}

void sendStatus() {
  RdkSerial.print("<S,");
  RdkSerial.print(currentCommand.state);
  RdkSerial.print(',');
  RdkSerial.print(currentCommand.left);
  RdkSerial.print(',');
  RdkSerial.print(currentCommand.right);
  RdkSerial.print(',');
  RdkSerial.print(currentCommand.pump ? 1 : 0);
  RdkSerial.println('>');
}

void setup() {
  pinMode(PIN_STBY, OUTPUT);
  pinMode(PIN_AIN1, OUTPUT);
  pinMode(PIN_AIN2, OUTPUT);
  pinMode(PIN_BIN1, OUTPUT);
  pinMode(PIN_BIN2, OUTPUT);
  if (PIN_PUMP >= 0) pinMode(PIN_PUMP, OUTPUT);

  ledcSetup(LEFT_PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcSetup(RIGHT_PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(PIN_PWMA, LEFT_PWM_CHANNEL);
  ledcAttachPin(PIN_PWMB, RIGHT_PWM_CHANNEL);

  strip.begin();
  strip.setBrightness(LED_BRIGHTNESS);
  strip.show();

  Serial.begin(115200);
  RdkSerial.begin(UART_BAUD, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
  stopActuators();
  lastCommandAt = millis();
  Serial.println("Laker ESP32-S3 motor bridge ready");
}

void loop() {
  while (RdkSerial.available()) {
    char ch = static_cast<char>(RdkSerial.read());
    if (ch == '\n' || ch == '\r') {
      ControlCommand parsed;
      if (parseControlFrame(lineBuffer, parsed)) {
        currentCommand = parsed;
        applyCommand(currentCommand);
        lastCommandAt = millis();
        sendStatus();
      }
      lineBuffer = "";
    } else if (lineBuffer.length() < 96) {
      lineBuffer += ch;
    } else {
      lineBuffer = "";
    }
  }

  if (millis() - lastCommandAt > COMMAND_TIMEOUT_MS) {
    stopActuators();
    lastCommandAt = millis();
    sendStatus();
  }
}
