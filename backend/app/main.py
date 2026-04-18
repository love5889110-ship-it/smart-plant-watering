import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel

from .database import init_db, get_db, PlantInstance, SensorReading, WateringEvent
from .core.plant_knowledge import list_profiles, get_profile, get_seasonal_threshold
from .core.decision_engine import calc_health_score, decide
from .core.mqtt_handler import start_mqtt, publish_pump_command

app = FastAPI(title="智能浇花系统", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    start_mqtt()


# ============================================================
# 植物档案 CRUD
# ============================================================
class PlantCreate(BaseModel):
    profile_id: str
    nickname: str
    device_id: str

@app.get("/api/plant-profiles")
def get_plant_profiles():
    return list_profiles()

@app.get("/api/plants")
def get_plants(db: Session = Depends(get_db)):
    plants = db.query(PlantInstance).all()
    result = []
    for p in plants:
        latest = db.query(SensorReading)\
            .filter_by(plant_id=p.id)\
            .order_by(SensorReading.timestamp.desc())\
            .first()
        profile = get_profile(p.profile_id)
        result.append({
            "id": p.id,
            "nickname": p.nickname,
            "profile_id": p.profile_id,
            "profile_name": profile["name_zh"] if profile else p.profile_id,
            "emoji": profile["emoji"] if profile else "🌿",
            "device_id": p.device_id,
            "health_score": p.health_score,
            "last_watered_at": p.last_watered_at,
            "current_moisture": latest.moisture_pct if latest else None,
            "last_seen": latest.timestamp if latest else None,
        })
    return result

@app.post("/api/plants", status_code=201)
def create_plant(body: PlantCreate, db: Session = Depends(get_db)):
    if not get_profile(body.profile_id):
        raise HTTPException(400, f"未知植物类型: {body.profile_id}")
    plant = PlantInstance(
        profile_id=body.profile_id,
        nickname=body.nickname,
        device_id=body.device_id,
    )
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return {"id": plant.id, "message": "植物创建成功"}

@app.get("/api/plants/{plant_id}")
def get_plant_detail(plant_id: int, db: Session = Depends(get_db)):
    plant = db.query(PlantInstance).get(plant_id)
    if not plant:
        raise HTTPException(404, "植物不存在")
    profile = get_profile(plant.profile_id)
    thresholds = get_seasonal_threshold(plant.profile_id)
    since = datetime.utcnow() - timedelta(days=7)
    readings = db.query(SensorReading)\
        .filter(SensorReading.plant_id == plant_id,
                SensorReading.timestamp >= since)\
        .order_by(SensorReading.timestamp.asc()).all()
    events = db.query(WateringEvent)\
        .filter(WateringEvent.plant_id == plant_id,
                WateringEvent.started_at >= since)\
        .order_by(WateringEvent.started_at.desc()).all()
    moisture_list = [r.moisture_pct for r in readings]
    health = calc_health_score(moisture_list, len(events), plant.profile_id)
    plant.health_score = health
    db.commit()

    # 当前实时决策分析
    latest = db.query(SensorReading).filter_by(plant_id=plant_id)\
        .order_by(SensorReading.timestamp.desc()).first()
    decision_data = None
    if latest:
        dec = decide(
            plant.profile_id,
            latest.moisture_pct,
            plant.last_watered_at,
            health,
            moisture_list[-20:] if moisture_list else [],
        )
        decision_data = {
            "should_water": dec.should_water,
            "duration_seconds": dec.duration_seconds,
            "reason": dec.reason,
            "urgency": dec.urgency,
            "final_score": dec.final_score,
            "strategy_note": dec.strategy_note,
            "factors": [
                {
                    "name": f.name,
                    "key": f.key,
                    "score": f.score,
                    "level": f.level,
                    "detail": f.detail,
                }
                for f in dec.factors
            ],
        }

    # 完整养护记录（含决策因子）
    care_events = []
    for e in events:
        factors_parsed = None
        if e.decision_factors:
            try:
                factors_parsed = json.loads(e.decision_factors)
            except Exception:
                pass
        care_events.append({
            "id": e.id,
            "t": e.started_at,
            "d": e.duration_seconds,
            "r": e.reason,
            "trigger": e.trigger_type,
            "moisture_before": e.moisture_before,
            "moisture_after": e.moisture_after,
            "final_score": e.final_score,
            "factors": factors_parsed,
        })

    return {
        "id": plant.id,
        "nickname": plant.nickname,
        "profile": profile,
        "thresholds": thresholds,
        "health_score": health,
        "last_watered_at": plant.last_watered_at,
        "readings": [{"t": r.timestamp, "m": r.moisture_pct} for r in readings],
        "watering_events": care_events,
        "decision": decision_data,
    }


# ============================================================
# 手动浇水
# ============================================================
class WaterCommand(BaseModel):
    duration_seconds: int = 10

@app.post("/api/plants/{plant_id}/water")
def manual_water(plant_id: int, body: WaterCommand, db: Session = Depends(get_db)):
    plant = db.query(PlantInstance).get(plant_id)
    if not plant:
        raise HTTPException(404, "植物不存在")
    duration_ms = min(body.duration_seconds * 1000, 30000)
    publish_pump_command(plant.device_id, duration_ms, reason="manual")
    latest = db.query(SensorReading).filter_by(plant_id=plant_id)\
        .order_by(SensorReading.timestamp.desc()).first()
    moisture_now = latest.moisture_pct if latest else None

    # 记录决策过程
    dec = decide(
        plant.profile_id,
        moisture_now or 50,
        plant.last_watered_at,
        plant.health_score or 70,
    )
    factors_json = json.dumps(
        [{"name": f.name, "key": f.key, "score": f.score, "level": f.level, "detail": f.detail}
         for f in dec.factors],
        ensure_ascii=False,
    )

    event = WateringEvent(
        plant_id=plant.id,
        device_id=plant.device_id,
        duration_seconds=body.duration_seconds,
        trigger_type="manual",
        moisture_before=moisture_now,
        reason="manual",
        decision_factors=factors_json,
        final_score=dec.final_score,
    )
    db.add(event)
    plant.last_watered_at = datetime.utcnow()
    db.commit()
    return {"message": f"已发送浇水指令: {body.duration_seconds}秒"}


# ============================================================
# 实时决策分析（独立接口）
# ============================================================
@app.get("/api/plants/{plant_id}/decision")
def get_decision(plant_id: int, db: Session = Depends(get_db)):
    """获取当前多因子浇水决策分析"""
    plant = db.query(PlantInstance).get(plant_id)
    if not plant:
        raise HTTPException(404, "植物不存在")
    latest = db.query(SensorReading).filter_by(plant_id=plant_id)\
        .order_by(SensorReading.timestamp.desc()).first()
    if not latest:
        raise HTTPException(404, "暂无传感器数据")

    since = datetime.utcnow() - timedelta(days=7)
    readings = db.query(SensorReading)\
        .filter(SensorReading.plant_id == plant_id,
                SensorReading.timestamp >= since)\
        .order_by(SensorReading.timestamp.asc()).all()
    moisture_list = [r.moisture_pct for r in readings]

    dec = decide(
        plant.profile_id,
        latest.moisture_pct,
        plant.last_watered_at,
        plant.health_score or 70,
        moisture_list[-20:],
    )
    return {
        "should_water": dec.should_water,
        "duration_seconds": dec.duration_seconds,
        "reason": dec.reason,
        "urgency": dec.urgency,
        "final_score": dec.final_score,
        "strategy_note": dec.strategy_note,
        "factors": [
            {"name": f.name, "key": f.key, "score": f.score, "level": f.level, "detail": f.detail}
            for f in dec.factors
        ],
        "current_moisture": latest.moisture_pct,
        "checked_at": datetime.utcnow(),
    }


# ============================================================
# 传感器历史
# ============================================================
@app.get("/api/plants/{plant_id}/readings")
def get_readings(plant_id: int, hours: int = 24, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=hours)
    readings = db.query(SensorReading)\
        .filter(SensorReading.plant_id == plant_id,
                SensorReading.timestamp >= since)\
        .order_by(SensorReading.timestamp.asc()).all()
    return [{"timestamp": r.timestamp, "moisture_pct": r.moisture_pct} for r in readings]


# ============================================================
# 养护记录（全量，含决策详情）
# ============================================================
@app.get("/api/plants/{plant_id}/care-log")
def get_care_log(plant_id: int, days: int = 30, db: Session = Depends(get_db)):
    plant = db.query(PlantInstance).get(plant_id)
    if not plant:
        raise HTTPException(404, "植物不存在")
    since = datetime.utcnow() - timedelta(days=days)
    events = db.query(WateringEvent)\
        .filter(WateringEvent.plant_id == plant_id,
                WateringEvent.started_at >= since)\
        .order_by(WateringEvent.started_at.desc()).all()
    result = []
    for e in events:
        factors_parsed = None
        if e.decision_factors:
            try:
                factors_parsed = json.loads(e.decision_factors)
            except Exception:
                pass
        result.append({
            "id": e.id,
            "started_at": e.started_at,
            "duration_seconds": e.duration_seconds,
            "trigger_type": e.trigger_type,
            "reason": e.reason,
            "moisture_before": e.moisture_before,
            "moisture_after": e.moisture_after,
            "final_score": e.final_score,
            "factors": factors_parsed,
        })
    return result


# ============================================================
# 总览 Dashboard
# ============================================================
@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    plants = db.query(PlantInstance).all()
    summary = []
    for p in plants:
        latest = db.query(SensorReading).filter_by(plant_id=p.id)\
            .order_by(SensorReading.timestamp.desc()).first()
        profile = get_profile(p.profile_id)
        thresholds = get_seasonal_threshold(p.profile_id)
        moisture = latest.moisture_pct if latest else None
        status = "unknown"
        if moisture is not None and thresholds:
            if moisture <= thresholds["critical_low"]:    status = "critical_dry"
            elif moisture <= thresholds["target_low"]:    status = "dry"
            elif moisture >= thresholds["critical_high"]: status = "critical_wet"
            elif moisture >= thresholds["target_high"]:   status = "wet"
            else:                                         status = "ok"
        summary.append({
            "id": p.id,
            "nickname": p.nickname,
            "emoji": profile["emoji"] if profile else "🌿",
            "current_moisture": moisture,
            "health_score": p.health_score,
            "status": status,
            "last_watered_at": p.last_watered_at,
            "thresholds": thresholds,
            "profile_name": profile["name_zh"] if profile else p.profile_id,
        })
    return {"plants": summary, "timestamp": datetime.utcnow()}
