# 智能浇花系统 — 启动指南

## 第一步：固件烧录

1. 安装 [PlatformIO](https://platformio.org/)（VS Code插件）
2. 打开 `firmware/` 目录
3. **修改 `src/config.h`**：
   - 填入你的WiFi名称和密码
   - 填入Mac的局域网IP（终端运行 `ifconfig | grep "inet 192"`）
4. 连接ESP32，点击 PlatformIO "Upload"

## 第二步：传感器校准（重要！）

烧录后打开串口监视器（115200波特率），观察输出：
- 传感器悬空（干燥空气）→ 记录 raw 值，填入 `MOISTURE_DRY_ADC`
- 传感器插入清水 → 记录 raw 值，填入 `MOISTURE_WET_ADC`
- 重新烧录固件

## 第三步：启动 MQTT Broker

```bash
cd backend
docker-compose up -d
```

## 第四步：启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 第五步：启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173

## 第六步：添加植物

在网页界面点击 "+" → 选择植物类型 → 填入昵称和设备ID → 确认

---

## 验证系统正常运行

串口监视器应看到：
```
[WiFi] 连接成功! IP: 192.168.x.x
[MQTT] 已连接 broker, rc=0
[SENSOR] 湿度: 42.3%  (raw: 2156)
```

网页Dashboard应显示植物卡片和实时湿度。

---

## 目录结构

```
智能浇花/
├── firmware/          ESP32 固件 (PlatformIO)
├── backend/           Python FastAPI 后端
└── frontend/          Vue 3 网页前端
```
