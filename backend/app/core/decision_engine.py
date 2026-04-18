"""
多因子智能浇水决策引擎
因子：湿度缺口 × 季节系数 × 时段适宜性 × 植物策略 × 健康趋势 × 最近浇水间隔
每个因子都有独立分值和说明，最终合并得出决策建议。
"""
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from .plant_knowledge import get_seasonal_threshold, get_profile, get_season


@dataclass
class Factor:
    name: str         # 因子名称（中文）
    key: str          # 英文key
    score: float      # -1.0 ~ 1.0，负=阻止浇水，正=建议浇水，0=中立
    level: str        # "pass" / "warn" / "block" / "boost"
    detail: str       # 用于前端展示的解释文字


@dataclass
class WateringDecision:
    should_water: bool
    duration_seconds: int
    reason: str
    urgency: str        # "none" / "normal" / "urgent"
    factors: list[Factor] = field(default_factory=list)
    final_score: float = 0.0
    strategy_note: str = ""  # 该植物策略的核心说明


def get_time_of_day() -> str:
    h = datetime.now().hour
    if 5 <= h < 9:   return "morning"
    if 9 <= h < 12:  return "forenoon"
    if 12 <= h < 14: return "noon"
    if 14 <= h < 18: return "afternoon"
    if 18 <= h < 21: return "evening"
    return "night"


def _factor_moisture(current: float, thresholds: dict, profile: dict) -> tuple[Factor, str]:
    """湿度缺口因子"""
    c_lo = thresholds["critical_low"]
    t_lo = thresholds["target_low"]
    t_hi = thresholds["target_high"]
    c_hi = thresholds["critical_high"]
    urgency = "none"

    if current <= c_lo:
        f = Factor("湿度", "moisture", 1.0, "boost",
                   f"当前湿度 {current:.0f}% 低于紧急阈值 {c_lo}%，必须立即浇水")
        urgency = "urgent"
    elif current <= t_lo:
        deficit_ratio = (t_lo - current) / (t_lo - c_lo)
        score = 0.5 + deficit_ratio * 0.4
        f = Factor("湿度", "moisture", round(score, 2), "warn",
                   f"当前湿度 {current:.0f}%，低于目标下限 {t_lo}%，建议补水")
        urgency = "normal"
    elif current >= c_hi:
        f = Factor("湿度", "moisture", -1.0, "block",
                   f"当前湿度 {current:.0f}% 超过过湿阈值 {c_hi}%，禁止浇水")
    elif current >= t_hi:
        f = Factor("湿度", "moisture", -0.5, "warn",
                   f"当前湿度 {current:.0f}% 已超适宜上限 {t_hi}%，暂无需浇水")
    else:
        f = Factor("湿度", "moisture", 0.0, "pass",
                   f"当前湿度 {current:.0f}% 处于适宜区间 {t_lo}~{t_hi}%")

    return f, urgency


def _factor_season(thresholds: dict) -> Factor:
    """季节系数因子"""
    season = thresholds["season"]
    mult = thresholds["multiplier"]
    names = {"spring": "春季", "summer": "夏季", "autumn": "秋季", "winter": "冬季"}
    sn = names.get(season, season)

    if mult >= 1.3:
        return Factor("季节", "season", 0.3, "boost",
                      f"{sn}蒸发旺盛（需水系数 ×{mult}），植物需水量大")
    elif mult <= 0.4:
        return Factor("季节", "season", -0.3, "warn",
                      f"{sn}休眠期（需水系数 ×{mult}），大幅减少浇水")
    elif mult <= 0.6:
        return Factor("季节", "season", -0.15, "warn",
                      f"{sn}需水量偏低（系数 ×{mult}），适度控水")
    else:
        return Factor("季节", "season", 0.0, "pass",
                      f"{sn}正常需水期（系数 ×{mult}）")


def _factor_time_of_day(time_of_day: str, strategy: str) -> Factor:
    """时段适宜性因子"""
    if time_of_day == "morning" or time_of_day == "forenoon":
        return Factor("时段", "time_of_day", 0.25, "boost",
                      f"{'清晨' if time_of_day=='morning' else '上午'}是最佳浇水窗口，蒸发慢、根系吸收好")
    elif time_of_day == "noon":
        return Factor("时段", "time_of_day", -0.2, "warn",
                      "正午高温浇水易灼伤根系，建议等到傍晚")
    elif time_of_day == "night":
        return Factor("时段", "time_of_day", -0.1, "warn",
                      "深夜浇水土壤散热慢，易滋生细菌；非紧急情况建议等到清晨")
    else:
        tod_name = {'afternoon': '下午', 'evening': '傍晚'}.get(time_of_day, time_of_day)
        return Factor("时段", "time_of_day", 0.0, "pass",
                      f"当前时段（{tod_name}）浇水无明显影响")


def _factor_strategy(profile: dict) -> Factor:
    """植物浇水策略因子"""
    strategy = profile["watering"]["strategy"]
    name_zh = profile["name_zh"]
    if strategy == "keep_moist":
        return Factor("植物策略", "strategy", 0.15, "boost",
                      f"{name_zh} 保湿策略：土壤应保持持续湿润，不宜让其变干")
    elif strategy == "dry_between":
        sensitivity = profile["sensitivity"]["overwater"]
        if sensitivity == "very_high":
            return Factor("植物策略", "strategy", -0.2, "warn",
                          f"{name_zh} 干透浇透策略：两次浇水间需让表层土略干，极怕积水")
        return Factor("植物策略", "strategy", -0.1, "warn",
                      f"{name_zh} 干透浇透策略：需等上次水分充分消耗")
    else:
        return Factor("植物策略", "strategy", 0.0, "pass",
                      f"{name_zh} 标准策略：按湿度阈值正常执行")


def _factor_interval(last_watered_at: Optional[datetime], min_interval_hours: int) -> tuple[Factor, bool]:
    """浇水间隔因子，返回 (factor, is_blocked)"""
    if last_watered_at is None:
        return Factor("浇水间隔", "interval", 0.1, "pass", "从未浇水，可以浇"), False

    elapsed_h = (datetime.utcnow() - last_watered_at).total_seconds() / 3600
    remaining_h = min_interval_hours - elapsed_h

    if elapsed_h < min_interval_hours:
        return Factor("浇水间隔", "interval", -1.0, "block",
                      f"距上次浇水仅 {elapsed_h:.1f}h，最短间隔 {min_interval_hours}h，还需等待 {remaining_h:.1f}h"), True

    if elapsed_h > min_interval_hours * 4:
        return Factor("浇水间隔", "interval", 0.2, "boost",
                      f"距上次浇水已 {elapsed_h:.0f}h，土壤应已充分消耗水分"), False

    return Factor("浇水间隔", "interval", 0.0, "pass",
                  f"距上次浇水 {elapsed_h:.1f}h，间隔正常"), False


def _factor_health(health_score: int, recent_moisture_trend: list[float]) -> Factor:
    """健康趋势因子"""
    if health_score < 40:
        return Factor("健康趋势", "health", 0.2, "warn",
                      f"健康分 {health_score}分（较低），植物需要更精心的水分管理")
    elif health_score >= 85:
        return Factor("健康趋势", "health", -0.05, "pass",
                      f"健康分 {health_score}分，当前养护策略效果很好，无需激进调整")
    else:
        return Factor("健康趋势", "health", 0.0, "pass",
                      f"健康分 {health_score}分，状态正常")


def _calc_duration(profile: dict, thresholds: dict, current_moisture: float) -> int:
    """计算浇水时长，考虑植物策略"""
    target_mid = (thresholds["target_low"] + thresholds["target_high"]) / 2
    deficit = max(0, target_mid - current_moisture)
    base_sec = profile["watering"]["base_duration_seconds"]
    mult = thresholds["multiplier"]
    duration = int(base_sec * (deficit / 25.0) * mult)
    return max(5, min(30, duration))


def decide(
    profile_id: str,
    current_moisture: float,
    last_watered_at: Optional[datetime],
    health_score: int = 70,
    recent_moisture_list: Optional[list[float]] = None,
) -> WateringDecision:
    profile = get_profile(profile_id)
    if not profile:
        return WateringDecision(False, 0, "unknown_plant", "none")

    thresholds = get_seasonal_threshold(profile_id)
    time_of_day = get_time_of_day()
    min_interval = profile["watering"]["min_interval_hours"]
    strategy_note = profile["watering"]["notes"]

    factors: list[Factor] = []

    # --- 各因子评估 ---
    f_moisture, urgency = _factor_moisture(current_moisture, thresholds, profile)
    factors.append(f_moisture)

    f_season = _factor_season(thresholds)
    factors.append(f_season)

    f_time = _factor_time_of_day(time_of_day, profile["watering"]["strategy"])
    factors.append(f_time)

    f_strategy = _factor_strategy(profile)
    factors.append(f_strategy)

    f_interval, is_interval_blocked = _factor_interval(last_watered_at, min_interval)
    factors.append(f_interval)

    f_health = _factor_health(health_score, recent_moisture_list or [])
    factors.append(f_health)

    # --- 否决检查（block级因子直接否决） ---
    for f in factors:
        if f.level == "block":
            # 过湿block 或 间隔block
            if f.key == "moisture":
                return WateringDecision(False, 0, "moisture_too_high", "none", factors, -1.0, strategy_note)
            if f.key == "interval" and urgency != "urgent":
                # 紧急干旱可以突破间隔限制
                return WateringDecision(False, 0, "too_soon", "none", factors, -1.0, strategy_note)

    # --- 加权求和 ---
    weights = {
        "moisture":    0.45,
        "season":      0.15,
        "time_of_day": 0.10,
        "strategy":    0.15,
        "interval":    0.10,
        "health":      0.05,
    }
    final_score = sum(f.score * weights.get(f.key, 0.1) for f in factors)
    final_score = round(final_score, 3)

    # --- 决策 ---
    if urgency == "urgent":
        duration = _calc_duration(profile, thresholds, current_moisture)
        return WateringDecision(True, duration, "critical_dry", "urgent", factors, final_score, strategy_note)

    if final_score >= 0.15:
        duration = _calc_duration(profile, thresholds, current_moisture)
        return WateringDecision(True, duration, "moisture_low", "normal", factors, final_score, strategy_note)

    return WateringDecision(False, 0, "moisture_ok", "none", factors, final_score, strategy_note)


def calc_health_score(readings_7d: list[float], watering_events_7d: int, profile_id: str) -> int:
    if not readings_7d:
        return 50
    thresholds = get_seasonal_threshold(profile_id)
    if not thresholds:
        return 50

    lo, hi = thresholds["target_low"], thresholds["target_high"]
    c_lo, c_hi = thresholds["critical_low"], thresholds["critical_high"]

    in_range = sum(1 for m in readings_7d if lo <= m <= hi)
    drought_hits = sum(1 for m in readings_7d if m <= c_lo)
    flood_hits = sum(1 for m in readings_7d if m >= c_hi)

    consistency = int((in_range / len(readings_7d)) * 60)
    drought_penalty = min(30, drought_hits * 5)
    flood_penalty = min(10, flood_hits * 5)

    score = consistency + 40 - drought_penalty - flood_penalty
    return max(0, min(100, score))
