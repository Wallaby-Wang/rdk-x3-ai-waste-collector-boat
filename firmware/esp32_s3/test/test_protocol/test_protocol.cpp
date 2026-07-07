#include <Arduino.h>
#include <unity.h>

#include "protocol.h"

void test_parse_full_frame() {
  ControlCommand command;
  TEST_ASSERT_TRUE(parseControlFrame("<A,51,-25,ALIGN,2,0>", command));
  TEST_ASSERT_EQUAL(51, command.left);
  TEST_ASSERT_EQUAL(-25, command.right);
  TEST_ASSERT_EQUAL_STRING("ALIGN", command.state.c_str());
  TEST_ASSERT_EQUAL(2, command.light);
  TEST_ASSERT_FALSE(command.pump);
}

void test_parse_collect_frame() {
  ControlCommand command;
  TEST_ASSERT_TRUE(parseControlFrame("<A,72,72,COLLECT,2,1>", command));
  TEST_ASSERT_EQUAL(72, command.left);
  TEST_ASSERT_EQUAL(72, command.right);
  TEST_ASSERT_TRUE(command.pump);
}

void test_parse_legacy_stop() {
  ControlCommand command;
  TEST_ASSERT_TRUE(parseControlFrame("STOP", command));
  TEST_ASSERT_EQUAL(0, command.left);
  TEST_ASSERT_EQUAL(0, command.right);
  TEST_ASSERT_EQUAL_STRING("STOP", command.state.c_str());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_parse_full_frame);
  RUN_TEST(test_parse_collect_frame);
  RUN_TEST(test_parse_legacy_stop);
  UNITY_END();
}

void loop() {}
