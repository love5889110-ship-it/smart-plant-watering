#pragma once
#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// 初始化BLE服务
void ble_init();

// 更新湿度通知（有手机连接时自动推送）
void ble_update_moisture(float moisture_pct, bool pump_running);

// 是否有手机通过蓝牙连接
bool ble_is_connected();

// 外部实现：收到蓝牙浇水指令
extern void on_pump_command(unsigned long duration_ms, const char* reason);
