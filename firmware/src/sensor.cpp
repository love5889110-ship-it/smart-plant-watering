#include "sensor.h"

void sensor_init() {
    pinMode(MOISTURE_SENSOR_PIN, INPUT);
}

int sensor_read_raw() {
    // 取10次采样平均，消除ADC噪声
    long sum = 0;
    for (int i = 0; i < 10; i++) {
        sum += analogRead(MOISTURE_SENSOR_PIN);
        delay(5);
    }
    return (int)(sum / 10);
}

float sensor_read_moisture_pct() {
    int raw = sensor_read_raw();
    // 将ADC值映射到湿度百分比
    // DRY_ADC → 0%，WET_ADC → 100%
    float pct = (float)(MOISTURE_DRY_ADC - raw) / (MOISTURE_DRY_ADC - MOISTURE_WET_ADC) * 100.0f;
    // 限制在 0~100 范围内
    if (pct < 0.0f) pct = 0.0f;
    if (pct > 100.0f) pct = 100.0f;
    return pct;
}
