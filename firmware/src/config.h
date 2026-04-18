#pragma once

// ============================================================
// WiFi 配置 — 修改成你家的WiFi
// ============================================================
#define WIFI_SSID     "ChinaNet-1802"
#define WIFI_PASSWORD "110970999"

// ============================================================
// MQTT Broker — Mac的局域网IP（在Mac终端运行 ifconfig 查看）
// ============================================================
#define MQTT_BROKER_IP   "192.168.1.28"
#define MQTT_BROKER_PORT 1883
#define DEVICE_ID        "esp32_plant_01"

// ============================================================
// 引脚定义
// ============================================================
#define MOISTURE_SENSOR_PIN  34   // GPIO34 (ADC1_CH6) — 湿度传感器黄线
#define PUMP_PIN             25   // GPIO25 — 控制MOSFET Gate（经220Ω电阻）
#define LED_PIN              2    // 内置LED

// ============================================================
// 湿度传感器校准值（需要运行校准程序后填入）
// 默认值适用于大多数电容式传感器 V1.2
// ============================================================
#define MOISTURE_DRY_ADC  2800   // 传感器在干燥空气中的ADC读数
#define MOISTURE_WET_ADC  1200   // 传感器完全插入水中的ADC读数

// ============================================================
// 安全参数
// ============================================================
#define MAX_PUMP_DURATION_MS    30000UL   // 水泵单次最长30秒
#define MIN_PUMP_INTERVAL_MS         0UL   // 测试模式：无间隔限制
#define SENSOR_SAMPLE_MS        30000UL   // 每30秒采样一次
#define MQTT_RECONNECT_MS        5000UL   // MQTT断线5秒后重连
#define OFFLINE_FALLBACK_MS   1800000UL   // WiFi断30分钟切换本地模式

// ============================================================
// MQTT 话题
// ============================================================
#define TOPIC_SENSOR    "plant/" DEVICE_ID "/sensor"
#define TOPIC_PUMP_CMD  "plant/" DEVICE_ID "/pump/cmd"
#define TOPIC_PUMP_ACK  "plant/" DEVICE_ID "/pump/status"
#define TOPIC_HEARTBEAT "plant/" DEVICE_ID "/heartbeat"

// ============================================================
// 本地兜底阈值（WiFi离线时使用）
// ============================================================
#define LOCAL_MOISTURE_LOW   35   // 低于此值触发浇水
#define LOCAL_PUMP_DURATION  8000 // 本地模式浇水8秒
