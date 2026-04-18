import dayjs from 'dayjs'

export function getTimeOfDay() {
  const h = new Date().getHours()
  if (h >= 5 && h < 9)   return 'morning'
  if (h >= 9 && h < 12)  return 'forenoon'
  if (h >= 12 && h < 14) return 'noon'
  if (h >= 14 && h < 18) return 'afternoon'
  if (h >= 18 && h < 21) return 'evening'
  return 'night'
}

export function getSeason() {
  const m = new Date().getMonth() + 1
  if (m >= 3 && m <= 5)  return 'spring'
  if (m >= 6 && m <= 8)  return 'summer'
  if (m >= 9 && m <= 11) return 'autumn'
  return 'winter'
}

export function getSeasonEmoji(season) {
  return { spring: '🌸', summer: '☀️', autumn: '🍂', winter: '❄️' }[season] ?? '🌿'
}

export function getTimeGreeting(time) {
  return {
    morning:   '清晨好 🌅 植物们刚刚醒来',
    forenoon:  '上午好 ☀️ 是浇水的好时机',
    noon:      '正午注意 🌞 避免烈日暴晒',
    afternoon: '下午好 🌤️ 检查一下土壤吧',
    evening:   '傍晚好 🌇 植物准备休息了',
    night:     '夜深了 🌙 植物们在安静成长',
  }[time] ?? '你好 🌿'
}

// 植物角色情绪 — 感知时间、季节、昵称
export function getPlantMood(status, nickname, timeOfDay, season) {
  const name = nickname || '我'
  const tod = timeOfDay || getTimeOfDay()
  const s = season || getSeason()

  const moods = {
    ok: [
      `${name}今天状态超好！🥰`,
      `土壤刚刚好，阳光也不错 ✨`,
      tod === 'morning'  ? `早安！${name}精神满满 🌅` :
      tod === 'night'    ? `夜深了，${name}要去睡觉啦 🌙` :
      tod === 'noon'     ? `正午有点热，给我遮遮光吧 ☀️` :
      s === 'spring'     ? `春天真美，${name}在努力生长 🌸` :
      s === 'summer'     ? `夏天好热，但${name}很开心 🌞` :
      s === 'autumn'     ? `秋风凉凉，${name}状态绝佳 🍂` :
                           `冬天我在默默积蓄力量 ❄️`,
      `谢谢你的照顾，好幸福 🌱`,
    ],
    dry: [
      `${name}有点渴了... 能给点水吗 🥺`,
      `土壤开始变干，记得浇水哦 😢`,
      tod === 'morning'  ? `早安，今天能先喝点水吗 💧` :
      tod === 'evening'  ? `傍晚了，还没喝水呢... 😔` :
      s === 'summer'     ? `夏天蒸发太快了，好渴啊 🥵` :
                           `水分少了，有点不舒服 😣`,
    ],
    critical_dry: [
      `救命！${name}快渴死了！！😫`,
      `叶子都要卷起来了，快来救我 😭`,
      `水...水...需要水... 🚨`,
      tod === 'night'    ? `都夜里了还没水喝，好委屈 😭` :
      s === 'summer'     ? `夏天高温缺水，根都要枯了！💀` :
                           `紧急！${name}严重缺水请立刻浇水！`,
    ],
    wet: [
      `${name}水喝够了，先消化一下 😌`,
      `不需要水啦，让我慢慢吸收`,
      s === 'winter'     ? `冬天水分多了点，注意别积水 🧊` :
                           `土壤湿润，暂时不渴 💦`,
    ],
    critical_wet: [
      `${name}被淹了！求求停止浇水 😰`,
      `根系快要窒息了，太湿了 😱`,
      `积水严重，快帮我排排水 💀`,
    ],
    unknown: [
      `${name}在等待传感器数据... 💤`,
      `信号好像断了，有点迷失 📡`,
    ],
  }
  const list = moods[status] ?? moods.unknown
  return list[Math.floor(Date.now() / 60000) % list.length]
}

// 行动建议 — 今日需要做什么（浇水/晒太阳/施肥提醒）
export function getActionAdvice(plant, timeOfDay, season) {
  const advice = []
  const status = plant.status
  const lastWatered = plant.last_watered_at ? dayjs(plant.last_watered_at) : null
  const hoursSinceWater = lastWatered ? dayjs().diff(lastWatered, 'hour') : 999
  const tod = timeOfDay || getTimeOfDay()
  const s = season || getSeason()

  // 浇水建议
  if (status === 'critical_dry')
    advice.push({ icon: '🚨', text: `${plant.nickname || '植物'}紧急缺水，立刻浇！`, action: 'water', urgent: true, plant_id: plant.id })
  else if (status === 'dry' && tod === 'morning')
    advice.push({ icon: '💧', text: `${plant.nickname || '植物'}有些干，早晨浇水最好`, action: 'water', urgent: false, plant_id: plant.id })
  else if (status === 'dry')
    advice.push({ icon: '💧', text: `${plant.nickname || '植物'}需要补水了`, action: 'water', urgent: false, plant_id: plant.id })
  else if (status === 'critical_wet')
    advice.push({ icon: '🚫', text: `${plant.nickname || '植物'}积水严重，停止浇水`, action: null, urgent: true })

  // 时段建议
  if (tod === 'noon' && s === 'summer')
    advice.push({ icon: '⛱️', text: '正午烈日，帮植物遮遮光', action: null })
  if (tod === 'morning' && s !== 'winter')
    advice.push({ icon: '🌅', text: '早晨适合给植物吹吹新鲜空气', action: null })
  if (tod === 'evening' && status === 'ok')
    advice.push({ icon: '🌙', text: '晚上适合观察叶片状态', action: null })

  // 季节建议
  if (s === 'spring')
    advice.push({ icon: '🌱', text: '春季生长旺盛，可以考虑追肥', action: 'fertilize' })
  if (s === 'summer' && tod !== 'noon')
    advice.push({ icon: '☀️', text: '夏季蒸发快，每天检查土壤湿度', action: null })
  if (s === 'autumn')
    advice.push({ icon: '🍂', text: '秋季减少浇水，准备越冬', action: null })
  if (s === 'winter' && status !== 'critical_dry')
    advice.push({ icon: '❄️', text: '冬季休眠期，大幅减少浇水', action: null })

  // 晒太阳
  if ((tod === 'morning' || tod === 'forenoon') && s !== 'summer')
    advice.push({ icon: '☀️', text: '上午阳光温和，适合晒太阳', action: 'sunlight' })

  // 健康告警
  if (plant.health_score < 50)
    advice.push({ icon: '🏥', text: `${plant.nickname || '植物'}健康分低，检查根系和土壤`, action: null, urgent: true })

  // 长时间未浇水
  if (hoursSinceWater > 72 && status === 'ok')
    advice.push({ icon: '📅', text: `${Math.round(hoursSinceWater)}小时未浇水，土壤该检查了`, action: null })

  return advice.slice(0, 4)
}

// 背景渐变
export function getBgGradient(timeOfDay, season) {
  if (timeOfDay === 'night')   return 'linear-gradient(to bottom, #0f172a, #1e1b4b)'
  if (timeOfDay === 'morning') return 'linear-gradient(to bottom, #431407, #7c2d12)'
  if (timeOfDay === 'evening') return 'linear-gradient(to bottom, #2e1065, #7c2d12)'
  if (season === 'winter')     return 'linear-gradient(to bottom, #172554, #164e63)'
  if (season === 'summer')     return 'linear-gradient(to bottom, #14532d, #78350f)'
  if (season === 'autumn')     return 'linear-gradient(to bottom, #7c2d12, #78350f)'
  return 'linear-gradient(to bottom, #14532d, #134e4a)'
}

// 季节漂浮粒子配置
export function getSeasonParticles(season, timeOfDay) {
  if (timeOfDay === 'night') return [{ emoji: '⭐', count: 8 }, { emoji: '🌙', count: 2 }]
  if (timeOfDay === 'morning') return [{ emoji: '🌅', count: 3 }, { emoji: '✨', count: 5 }]
  return {
    spring: [{ emoji: '🌸', count: 6 }, { emoji: '🌿', count: 4 }],
    summer: [{ emoji: '☀️', count: 3 }, { emoji: '🌻', count: 4 }, { emoji: '🦋', count: 2 }],
    autumn: [{ emoji: '🍂', count: 7 }, { emoji: '🍁', count: 4 }],
    winter: [{ emoji: '❄️', count: 8 }, { emoji: '⛄', count: 2 }],
  }[season] ?? [{ emoji: '🌿', count: 5 }]
}

export function getCardGradient(status) {
  return {
    ok:           'linear-gradient(135deg, #15803d, #0f766e)',
    dry:          'linear-gradient(135deg, #b45309, #c2410c)',
    critical_dry: 'linear-gradient(135deg, #b91c1c, #9f1239)',
    wet:          'linear-gradient(135deg, #1d4ed8, #0e7490)',
    critical_wet: 'linear-gradient(135deg, #1e3a8a, #3730a3)',
    unknown:      'linear-gradient(135deg, #374151, #1f2937)',
  }[status] ?? 'linear-gradient(135deg, #374151, #1f2937)'
}

// 水位填充颜色
export function getWaterColor(status) {
  return {
    ok:           'rgba(34,197,94,0.5)',
    dry:          'rgba(245,158,11,0.45)',
    critical_dry: 'rgba(239,68,68,0.5)',
    wet:          'rgba(96,165,250,0.55)',
    critical_wet: 'rgba(37,99,235,0.6)',
    unknown:      'rgba(107,114,128,0.3)',
  }[status] ?? 'rgba(107,114,128,0.3)'
}

export function getHeaderGradient(status) {
  return {
    ok:           'linear-gradient(to bottom, #14532d, #134e4a)',
    dry:          'linear-gradient(to bottom, #92400e, #b45309)',
    critical_dry: 'linear-gradient(to bottom, #7f1d1d, #9f1239)',
    wet:          'linear-gradient(to bottom, #1e3a8a, #164e63)',
    critical_wet: 'linear-gradient(to bottom, #1e1b4b, #1e3a8a)',
    unknown:      'linear-gradient(to bottom, #1f2937, #111827)',
  }[status] ?? 'linear-gradient(to bottom, #1f2937, #111827)'
}
