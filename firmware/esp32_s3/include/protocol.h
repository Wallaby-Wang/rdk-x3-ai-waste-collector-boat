#pragma once

#include <Arduino.h>

struct ControlCommand {
  int left = 0;
  int right = 0;
  String state = "STOP";
  int light = 3;
  bool pump = false;
  bool valid = false;
};

inline int clampPwm(int value) {
  if (value > 255) return 255;
  if (value < -255) return -255;
  return value;
}

inline ControlCommand legacyCommand(const String& line) {
  ControlCommand command;
  command.valid = true;
  command.pump = false;
  command.light = 1;

  if (line == "SEARCH") {
    command.left = 86;
    command.right = -71;
    command.state = "SEARCH";
  } else if (line == "LEFT") {
    command.left = -48;
    command.right = 138;
    command.state = "ALIGN";
    command.light = 2;
  } else if (line == "RIGHT") {
    command.left = 138;
    command.right = -48;
    command.state = "ALIGN";
    command.light = 2;
  } else if (line == "FORWARD") {
    command.left = 148;
    command.right = 148;
    command.state = "APPROACH";
    command.light = 2;
  } else if (line == "COLLECT") {
    command.left = 72;
    command.right = 72;
    command.state = "COLLECT";
    command.light = 2;
    command.pump = true;
  } else if (line == "STOP") {
    command.left = 0;
    command.right = 0;
    command.state = "STOP";
    command.light = 3;
  } else {
    command.valid = false;
  }

  return command;
}

inline bool parseControlFrame(String line, ControlCommand& out) {
  line.trim();
  if (line.length() == 0) return false;

  if (!line.startsWith("<")) {
    out = legacyCommand(line);
    return out.valid;
  }

  if (!line.endsWith(">")) return false;
  line = line.substring(1, line.length() - 1);

  int firstComma = line.indexOf(',');
  if (firstComma < 0 || line.substring(0, firstComma) != "A") return false;

  String fields[6];
  int fieldIndex = 0;
  int start = firstComma + 1;
  while (fieldIndex < 6) {
    int comma = line.indexOf(',', start);
    if (comma < 0) {
      fields[fieldIndex++] = line.substring(start);
      break;
    }
    fields[fieldIndex++] = line.substring(start, comma);
    start = comma + 1;
  }
  if (fieldIndex < 3) return false;

  ControlCommand command;
  command.left = clampPwm(fields[0].toInt());
  command.right = clampPwm(fields[1].toInt());
  command.state = fields[2].length() ? fields[2] : "AUTO";
  command.light = fieldIndex >= 4 ? fields[3].toInt() : 2;
  command.pump = fieldIndex >= 5 ? fields[4].toInt() != 0 : false;
  command.valid = true;
  out = command;
  return true;
}
