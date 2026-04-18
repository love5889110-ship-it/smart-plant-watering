#pragma once
#include <Arduino.h>
#include "config.h"

// 初始化传感器引脚
void sensor_init();

// 读取湿度百分比（0-100），内部取10次平均
float sensor_read_moisture_pct();

// 读取原始ADC值（用于调试/校准）
int sensor_read_raw();
