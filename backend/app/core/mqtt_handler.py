import json
import threading
import paho.mqtt.client as mqtt
from datetime import datetime

from ..database import SessionLocal, SensorReading, WateringEvent, PlantInstance
from .decision_engine import decide
from .plant_knowledge import get_profile

_mqtt_client: mqtt.Client | None = None

def _on_connect(client, userdata, flags, rc):
    print(f"[MQTT] 已连接 broker, rc={rc}")
    client.subscribe("plant/+/sensor")
    client.subscribe("plant/+/pump/status")
    client.subscribe("plant/+/heartbeat")

def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic = msg.topic

        if "/sensor" in topic:
            _handle_sensor(client, payload)
        elif "/heartbeat" in topic:
            _handle_heartbeat(payload)
    except Exception as e:
        print(f"[MQTT] 消息处理错误: {e}")

def _handle_sensor(client: mqtt.Client, data: dict):
    device_id = data.get("device_id", "")
    moisture = data.get("moisture_pct", 0)
    raw = data.get("moisture_raw", 0)
    rssi = data.get("wifi_rssi", None)

    db = SessionLocal()
    try:
        # 查找绑定该设备的植物
        plant = db.query(PlantInstance).filter_by(device_id=device_id).first()
        if not plant:
            print(f"[MQTT] 未知设备: {device_id}，忽略数据")
            return

        # 存储传感器读数
        reading = SensorReading(
            plant_id=plant.id,
            device_id=device_id,
            moisture_pct=moisture,
            moisture_raw=raw,
            wifi_rssi=rssi,
            timestamp=datetime.utcnow(),
        )
        db.add(reading)

        # 决策引擎判断是否浇水
        profile = get_profile(plant.profile_id)
        min_interval = profile["watering"]["min_interval_hours"] if profile else 1
        decision = decide(plant.profile_id, moisture, plant.last_watered_at, min_interval)

        if decision.should_water:
            # 发送MQTT浇水指令
            cmd = json.dumps({
                "command": "water",
                "duration_ms": decision.duration_seconds * 1000,
                "reason": decision.reason,
                "plant_id": plant.id,
            })
            client.publish(f"plant/{device_id}/pump/cmd", cmd, qos=0)
            print(f"[ENGINE] 触发浇水: {plant.nickname} {decision.duration_seconds}s ({decision.reason})")

            # 记录浇水事件
            event = WateringEvent(
                plant_id=plant.id,
                device_id=device_id,
                duration_seconds=decision.duration_seconds,
                trigger_type="threshold",
                moisture_before=moisture,
                reason=decision.reason,
            )
            db.add(event)
            plant.last_watered_at = datetime.utcnow()

        db.commit()
    finally:
        db.close()

def _handle_heartbeat(data: dict):
    online = data.get("online", True)
    device_id = data.get("device_id", "")
    status = "在线" if online else "离线"
    print(f"[HEARTBEAT] {device_id}: {status}")

def start_mqtt(broker_host: str = "localhost", broker_port: int = 1883):
    global _mqtt_client
    _mqtt_client = mqtt.Client(client_id="plant_server")
    _mqtt_client.on_connect = _on_connect
    _mqtt_client.on_message = _on_message
    _mqtt_client.connect(broker_host, broker_port, keepalive=60)
    thread = threading.Thread(target=_mqtt_client.loop_forever, daemon=True)
    thread.start()
    print(f"[MQTT] 已启动, 连接到 {broker_host}:{broker_port}")

def publish_pump_command(device_id: str, duration_ms: int, reason: str = "manual"):
    if _mqtt_client:
        cmd = json.dumps({"command": "water", "duration_ms": duration_ms, "reason": reason})
        _mqtt_client.publish(f"plant/{device_id}/pump/cmd", cmd, qos=0)
