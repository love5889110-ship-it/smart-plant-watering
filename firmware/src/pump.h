#pragma once
#include <Arduino.h>
#include "config.h"

// 初始化水泵引脚
void pump_init();

// 启动水泵，持续 duration_ms 毫秒（最长受MAX_PUMP_DURATION_MS限制）
void pump_start(unsigned long duration_ms);

// 立即停止水泵
void pump_stop();

// 是否正在运行
bool pump_is_running();

// 必须在loop()中调用，处理超时自动停泵
void pump_update();

// 上次停泵时间戳（ms）
unsigned long pump_last_stop_time();
