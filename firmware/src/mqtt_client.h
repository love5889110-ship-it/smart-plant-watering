#pragma once
#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include "config.h"

// 初始化WiFi + MQTT连接
void mqtt_init();

// 必须在loop()中调用，维持连接
void mqtt_update();

// 发布传感器数据到MQTT
void mqtt_publish_sensor(float moisture_pct, int moisture_raw, bool pump_running);

// 发布水泵状态确认
void mqtt_publish_pump_status(bool running, unsigned long duration_ms);

// 是否已连接MQTT
bool mqtt_is_connected();

// 外部注册浇水指令回调（由main.cpp实现）
extern void on_pump_command(unsigned long duration_ms, const char* reason);
