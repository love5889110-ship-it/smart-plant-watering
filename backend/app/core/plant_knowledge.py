import json
from datetime import datetime
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent.parent / "data" / "plant_database.json"
_profiles: dict = {}

def _load():
    global _profiles
    data = json.loads(_DB_PATH.read_text(encoding="utf-8"))
    _profiles = {p["id"]: p for p in data["plants"]}

_load()

def get_profile(profile_id: str) -> dict | None:
    return _profiles.get(profile_id)

def list_profiles() -> list[dict]:
    return list(_profiles.values())

def get_season() -> str:
    month = datetime.now().month
    if month in (3, 4, 5):   return "spring"
    if month in (6, 7, 8):   return "summer"
    if month in (9, 10, 11): return "autumn"
    return "winter"

def get_seasonal_threshold(profile_id: str) -> dict:
    """返回季节修正后的湿度阈值"""
    profile = get_profile(profile_id)
    if not profile:
        return {}
    season = get_season()
    mult = profile["seasonal_multipliers"][season]
    base = profile["moisture_thresholds"]
    # 季节系数影响目标区间，不影响绝对安全值
    target_mid = (base["target_low"] + base["target_high"]) / 2
    half_range = (base["target_high"] - base["target_low"]) / 2
    adjusted_low = max(base["critical_low"] + 2, target_mid - half_range * mult)
    adjusted_high = min(base["critical_high"] - 2, target_mid + half_range * mult)
    return {
        "critical_low": base["critical_low"],
        "target_low": round(adjusted_low, 1),
        "target_high": round(adjusted_high, 1),
        "critical_high": base["critical_high"],
        "season": season,
        "multiplier": mult,
    }

def calc_duration(profile_id: str, current_moisture: float) -> int:
    """根据缺水程度计算浇水秒数"""
    profile = get_profile(profile_id)
    if not profile:
        return 8
    thresholds = get_seasonal_threshold(profile_id)
    target_mid = (thresholds["target_low"] + thresholds["target_high"]) / 2
    deficit = max(0, target_mid - current_moisture)
    base_sec = profile["watering"]["base_duration_seconds"]
    mult = thresholds["multiplier"]
    duration = int(base_sec * (deficit / 25.0) * mult)
    return max(5, min(30, duration))
