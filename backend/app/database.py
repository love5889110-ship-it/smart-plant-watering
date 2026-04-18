from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./data/watering.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class PlantInstance(Base):
    __tablename__ = "plants"
    id = Column(Integer, primary_key=True)
    profile_id = Column(String, nullable=False)   # blueberry / rhododendron / general
    nickname = Column(String, nullable=False)
    device_id = Column(String, nullable=False)    # esp32_plant_01
    health_score = Column(Integer, default=100)
    last_watered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, nullable=False)
    device_id = Column(String, nullable=False)
    moisture_pct = Column(Float, nullable=False)
    moisture_raw = Column(Integer, nullable=False)
    wifi_rssi = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class WateringEvent(Base):
    __tablename__ = "watering_events"
    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, nullable=False)
    device_id = Column(String, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    trigger_type = Column(String, default="threshold")  # threshold/manual/schedule
    moisture_before = Column(Float, nullable=True)
    moisture_after = Column(Float, nullable=True)
    reason = Column(String, nullable=True)
    decision_factors = Column(Text, nullable=True)   # JSON: 决策因子详情
    final_score = Column(Float, nullable=True)        # 综合得分
    started_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
