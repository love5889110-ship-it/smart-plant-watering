<template>
  <div class="min-h-screen pb-10 relative overflow-hidden">
    <div class="fixed inset-0 -z-10 transition-all duration-1000"
         :style="{ background: headerGradient }"></div>

    <!-- 返回 -->
    <div class="absolute top-12 left-4 z-10">
      <button @click="$router.back()"
              class="bg-white/20 backdrop-blur text-white rounded-2xl p-3 active:scale-90 transition-transform">
        ‹
      </button>
    </div>

    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <div class="text-white text-center">
        <div class="text-5xl animate-bounce mb-3">🌱</div>
        <div class="text-white/60">加载中...</div>
      </div>
    </div>

    <div v-else-if="plant">
      <!-- Hero -->
      <div class="pt-16 pb-8 px-5 text-center text-shadow">
        <div class="relative inline-block mb-4">
          <div class="text-8xl select-none"
               :class="{ 'animate-bounce': watering, 'animate-pulse': plant.status === 'critical_dry' }">
            {{ plantFace }}
          </div>
        </div>
        <div class="text-white font-bold text-2xl">{{ plant.nickname }}</div>
        <div class="text-white/90 text-sm mt-0.5">
          {{ plant.profile?.name_zh }} · Lv.{{ level }} {{ levelLabel }}
        </div>
        <div class="inline-block mt-3 bg-white/25 backdrop-blur rounded-2xl px-4 py-2 max-w-xs">
          <div class="text-white text-sm font-medium">{{ mood }}</div>
        </div>
        <div class="flex items-center justify-center gap-2 mt-3">
          <span class="bg-white/20 text-white text-xs rounded-full px-3 py-1">{{ statusText }}</span>
          <span class="bg-white/20 text-white text-xs rounded-full px-3 py-1">{{ seasonEmoji }} {{ seasonName }}</span>
          <span class="bg-white/20 text-white text-xs rounded-full px-3 py-1">{{ timeLabel }}</span>
        </div>
      </div>

      <!-- 内容区 -->
      <div class="bg-gray-50 rounded-t-[2rem] min-h-screen px-4 pt-5 space-y-4">

        <!-- 核心数据 -->
        <div class="bg-white rounded-3xl shadow-sm p-5">
          <div class="grid grid-cols-3 divide-x divide-gray-100">
            <div class="text-center pr-3">
              <div class="text-3xl font-bold" :style="{ color: moistureColor }">
                {{ currentMoisture !== null ? Math.round(currentMoisture) + '%' : '--' }}
              </div>
              <div class="text-gray-500 text-xs mt-1">当前湿度</div>
            </div>
            <div class="text-center px-3">
              <div class="text-3xl font-bold" :style="{ color: healthColorVal }">{{ plant.health_score }}</div>
              <div class="text-gray-500 text-xs mt-1">健康评分</div>
            </div>
            <div class="text-center pl-3">
              <div class="text-3xl font-bold text-purple-500">{{ level }}</div>
              <div class="text-gray-500 text-xs mt-1">养成等级</div>
            </div>
          </div>
          <div class="mt-4">
            <div class="flex justify-between text-xs text-gray-600 mb-1.5">
              <span>🔴 {{ plant.thresholds.critical_low }}%</span>
              <span class="text-green-500 font-medium">✅ {{ plant.thresholds.target_low }}~{{ plant.thresholds.target_high }}%</span>
              <span>🔵 {{ plant.thresholds.critical_high }}%</span>
            </div>
            <div class="relative h-4 bg-gray-100 rounded-full overflow-hidden">
              <div class="absolute inset-y-0 bg-green-100 rounded-full"
                   :style="{ left: plant.thresholds.target_low + '%', width: (plant.thresholds.target_high - plant.thresholds.target_low) + '%' }"></div>
              <div v-if="currentMoisture !== null"
                   class="absolute top-0.5 bottom-0.5 w-3 rounded-full shadow-md transition-all duration-1000"
                   :style="{ left: `calc(${Math.max(2,Math.min(97,currentMoisture))}% - 6px)`, background: moistureColor }"></div>
            </div>
          </div>
        </div>

        <!-- 智能决策面板 -->
        <div v-if="decision" class="bg-white rounded-3xl shadow-sm p-5">
          <div class="font-semibold text-gray-800 mb-1 flex items-center gap-2">
            <span>🧠</span> 智能决策分析
          </div>
          <div class="text-xs text-gray-400 mb-4">综合6个因子实时推算浇水建议</div>

          <div class="rounded-2xl p-4 mb-4 flex items-center gap-3"
               :class="decision.urgency === 'urgent' ? 'bg-red-50 border border-red-100'
                     : decision.should_water ? 'bg-blue-50 border border-blue-100'
                     : 'bg-green-50 border border-green-100'">
            <div class="text-3xl">{{ decisionIcon }}</div>
            <div class="flex-1">
              <div class="font-semibold text-sm"
                   :class="decision.urgency === 'urgent' ? 'text-red-700' : decision.should_water ? 'text-blue-700' : 'text-green-700'">
                {{ decisionVerdict }}
              </div>
              <div class="text-xs text-gray-500 mt-0.5">综合得分 {{ Math.round(decision.final_score * 100) }}分</div>
            </div>
          </div>

          <div class="space-y-2">
            <div v-for="f in decisionFactors" :key="f.key"
                 class="flex items-start gap-3 p-3 rounded-xl bg-gray-50">
              <div class="text-base w-6 text-center flex-shrink-0">{{ factorIcon(f.level) }}</div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-0.5">
                  <span class="text-xs font-semibold text-gray-700">{{ f.name }}</span>
                  <span class="text-xs px-1.5 py-0.5 rounded-full font-medium"
                        :class="factorTagClass(f.level)">{{ factorLevelLabel(f.level) }}</span>
                </div>
                <div class="text-xs text-gray-500">{{ f.detail }}</div>
              </div>
              <div class="text-xs font-mono flex-shrink-0"
                   :class="f.score > 0 ? 'text-blue-500' : f.score < 0 ? 'text-red-400' : 'text-gray-400'">
                {{ f.score > 0 ? '+' : '' }}{{ Math.round(f.score * 100) }}
              </div>
            </div>
          </div>

          <div class="mt-4 bg-green-50 rounded-2xl p-3 text-xs text-green-700 leading-relaxed">
            💬 {{ decision.strategy_note }}
          </div>
        </div>

        <!-- 手动浇水 -->
        <div class="bg-white rounded-3xl shadow-sm p-5">
          <div class="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span>💧</span> 手动浇水
          </div>
          <div class="flex gap-2 mb-4">
            <button v-for="sec in [3,5,10,15,30]" :key="sec"
                    @click="waterDuration = sec"
                    class="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all active:scale-95"
                    :class="waterDuration === sec ? 'bg-blue-500 text-white shadow-lg shadow-blue-200' : 'bg-gray-100 text-gray-600'">
              {{ sec }}s
            </button>
          </div>
          <button @click="manualWater" :disabled="watering"
                  class="w-full py-4 rounded-2xl font-semibold text-base transition-all active:scale-95"
                  :class="watering ? 'bg-blue-100 text-blue-400' : 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg shadow-blue-200'">
            <span v-if="watering" class="flex items-center justify-center gap-2">
              <span class="inline-block animate-spin">💧</span> 浇水中...
            </span>
            <span v-else>💧 浇水 {{ waterDuration }} 秒</span>
          </button>
          <div class="text-center text-xs text-gray-500 mt-2">
            上次浇水：{{ formatTime(plant.last_watered_at) }}
          </div>
        </div>

        <!-- 智能设置 -->
        <div class="bg-white rounded-3xl shadow-sm p-5">
          <div class="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span>⚙️</span> 智能设置
          </div>

          <!-- 自动浇水开关 -->
          <div class="flex items-center justify-between py-3 border-b border-gray-100">
            <div>
              <div class="text-sm font-medium text-gray-700">自动浇水</div>
              <div class="text-xs text-gray-400">综合评分超过阈值时自动执行</div>
            </div>
            <button @click="toggleAutoWater"
                    class="relative w-12 h-6 rounded-full transition-all duration-300"
                    :class="settings.auto_water_enabled ? 'bg-green-500' : 'bg-gray-200'">
              <div class="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-all duration-300"
                   :class="settings.auto_water_enabled ? 'left-6' : 'left-0.5'"></div>
            </button>
          </div>

          <!-- 自动浇水细项设置 -->
          <div v-if="settings.auto_water_enabled" class="space-y-5 mt-4 pb-4 border-b border-gray-100">
            <!-- 触发灵敏度 -->
            <div>
              <div class="flex justify-between items-center mb-2">
                <div>
                  <div class="text-sm font-medium text-gray-700">触发灵敏度</div>
                  <div class="text-xs text-gray-400">综合评分超过此值自动浇水</div>
                </div>
                <span class="text-sm font-bold text-blue-600">{{ Math.round(settings.auto_water_threshold * 100) }}分</span>
              </div>
              <input type="range" min="5" max="80" step="5"
                     :value="Math.round(settings.auto_water_threshold * 100)"
                     @change="updateSetting('auto_water_threshold', $event.target.value / 100)"
                     class="w-full accent-blue-500" />
              <div class="flex justify-between text-xs text-gray-400 mt-1">
                <span>5（最灵敏）</span><span>80（最保守）</span>
              </div>
            </div>

            <!-- 单次浇水时长 -->
            <div>
              <div class="flex justify-between items-center mb-2">
                <div>
                  <div class="text-sm font-medium text-gray-700">单次浇水时长</div>
                  <div class="text-xs text-gray-400">
                    {{ settings.custom_duration_seconds ? '自定义' : `由决策引擎自动计算（植物基准 ${settings.default_duration_seconds}秒）` }}
                  </div>
                </div>
                <span class="text-sm font-bold text-blue-600">{{ settings.custom_duration_seconds ? settings.custom_duration_seconds + '秒' : '自动' }}</span>
              </div>
              <div class="flex gap-2 flex-wrap">
                <button @click="updateSetting('custom_duration_seconds', null)"
                        class="text-xs px-3 py-1.5 rounded-xl transition-all"
                        :class="!settings.custom_duration_seconds ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-500'">自动</button>
                <button v-for="sec in [5,8,10,15,20,30]" :key="sec"
                        @click="updateSetting('custom_duration_seconds', sec)"
                        class="text-xs px-3 py-1.5 rounded-xl transition-all"
                        :class="settings.custom_duration_seconds === sec ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-500'">{{ sec }}s</button>
              </div>
            </div>

            <!-- 最短间隔 -->
            <div>
              <div class="flex justify-between items-center mb-2">
                <div>
                  <div class="text-sm font-medium text-gray-700">最短浇水间隔</div>
                  <div class="text-xs text-gray-400">{{ settings.custom_min_interval_hours != null ? '自定义' : `植物特性默认 ${settings.default_min_interval_hours}小时` }}</div>
                </div>
                <span class="text-sm font-bold text-blue-600">{{ settings.custom_min_interval_hours != null ? settings.custom_min_interval_hours + '小时' : '默认' }}</span>
              </div>
              <div class="flex gap-2 flex-wrap">
                <button @click="updateSetting('custom_min_interval_hours', null)"
                        class="text-xs px-3 py-1.5 rounded-xl transition-all"
                        :class="settings.custom_min_interval_hours == null ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-500'">默认</button>
                <button v-for="h in [1,2,4,6,12,24]" :key="h"
                        @click="updateSetting('custom_min_interval_hours', h)"
                        class="text-xs px-3 py-1.5 rounded-xl transition-all"
                        :class="settings.custom_min_interval_hours === h ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-500'">{{ h }}h</button>
              </div>
            </div>
          </div>

          <!-- 植物特性 -->
          <div class="mt-4 pb-4 border-b border-gray-100">
            <div class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <span>{{ plant.profile?.emoji }}</span> {{ plant.profile?.name_zh }} 养护特性
            </div>
            <div class="grid grid-cols-2 gap-2 mb-3">
              <div class="bg-gray-50 rounded-xl p-3">
                <div class="text-xs text-gray-400 mb-1">浇水策略</div>
                <div class="text-sm font-semibold text-gray-700">{{ strategyLabel }}</div>
              </div>
              <div class="bg-gray-50 rounded-xl p-3">
                <div class="text-xs text-gray-400 mb-1">干旱敏感度</div>
                <div class="text-sm font-semibold" :class="sensitivityColor(plant.profile?.sensitivity?.drought)">
                  {{ sensitivityLabel(plant.profile?.sensitivity?.drought) }}
                </div>
              </div>
              <div class="bg-gray-50 rounded-xl p-3">
                <div class="text-xs text-gray-400 mb-1">积水敏感度</div>
                <div class="text-sm font-semibold" :class="sensitivityColor(plant.profile?.sensitivity?.overwater)">
                  {{ sensitivityLabel(plant.profile?.sensitivity?.overwater) }}
                </div>
              </div>
              <div class="bg-gray-50 rounded-xl p-3">
                <div class="text-xs text-gray-400 mb-1">默认浇水间隔</div>
                <div class="text-sm font-semibold text-gray-700">{{ settings.default_min_interval_hours }} 小时</div>
              </div>
            </div>
            <!-- 适宜湿度区间 -->
            <div class="bg-gray-50 rounded-xl p-3">
              <div class="text-xs text-gray-400 mb-2">湿度阈值（当前季节调整后）</div>
              <div class="flex items-center gap-1 text-xs">
                <span class="text-red-500 font-medium">危 {{ plant.thresholds.critical_low }}%</span>
                <div class="flex-1 h-3 bg-gray-200 rounded-full relative mx-1 overflow-hidden">
                  <div class="absolute inset-y-0 bg-orange-200 rounded-full"
                       :style="{ left: plant.thresholds.critical_low + '%', width: (plant.thresholds.target_low - plant.thresholds.critical_low) + '%' }"></div>
                  <div class="absolute inset-y-0 bg-green-300 rounded-full"
                       :style="{ left: plant.thresholds.target_low + '%', width: (plant.thresholds.target_high - plant.thresholds.target_low) + '%' }"></div>
                  <div class="absolute inset-y-0 bg-blue-200 rounded-full"
                       :style="{ left: plant.thresholds.target_high + '%', width: (plant.thresholds.critical_high - plant.thresholds.target_high) + '%' }"></div>
                </div>
                <span class="text-blue-500 font-medium">危 {{ plant.thresholds.critical_high }}%</span>
              </div>
              <div class="flex justify-between text-xs text-gray-400 mt-1 px-1">
                <span>建议 &lt;{{ plant.thresholds.target_low }}%</span>
                <span class="text-green-600 font-medium">适宜 {{ plant.thresholds.target_low }}~{{ plant.thresholds.target_high }}%</span>
                <span>过湿 &gt;{{ plant.thresholds.target_high }}%</span>
              </div>
            </div>
          </div>

          <!-- 季节需水系数 -->
          <div class="mt-4">
            <div class="text-sm font-semibold text-gray-700 mb-3">四季需水系数</div>
            <div class="grid grid-cols-4 gap-2">
              <div v-for="(item, idx) in seasonMultipliers" :key="idx"
                   class="rounded-xl p-2.5 text-center border-2 transition-all"
                   :class="item.current ? 'border-green-400 bg-green-50' : 'border-transparent bg-gray-50'">
                <div class="text-lg">{{ item.emoji }}</div>
                <div class="text-xs text-gray-500 mt-0.5">{{ item.name }}</div>
                <div class="text-sm font-bold mt-1" :class="item.current ? 'text-green-600' : 'text-gray-600'">×{{ item.mult }}</div>
                <div class="text-xs mt-0.5" :class="item.mult >= 1.3 ? 'text-orange-500' : item.mult <= 0.4 ? 'text-blue-400' : 'text-gray-400'">
                  {{ item.mult >= 1.3 ? '需水旺' : item.mult <= 0.4 ? '休眠省' : item.mult <= 0.7 ? '适度减' : '正常' }}
                </div>
                <div v-if="item.current" class="text-xs text-green-600 font-medium mt-0.5">当前</div>
              </div>
            </div>
            <div class="mt-3 text-xs text-gray-400 bg-gray-50 rounded-xl p-3 leading-relaxed">
              💡 季节系数会调整目标湿度区间宽窄，系数越大目标湿度越高，浇水更频繁。不影响紧急安全阈值。
            </div>
          </div>
        </div>



        <!-- 湿度趋势 -->
        <div class="bg-white rounded-3xl shadow-sm p-5">
          <div class="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <span>📈</span> 近7天湿度
          </div>
          <div v-if="chartReadings.length === 0" class="text-center py-8 text-gray-400 text-sm">暂无数据</div>
          <Line v-else :data="chartData" :options="chartOptions" style="max-height:200px" />
        </div>

        <!-- 养护记录 -->
        <div class="bg-white rounded-3xl shadow-sm p-5">
          <div class="font-semibold text-gray-800 mb-1 flex items-center gap-2">
            <span>📋</span> 养护记录
          </div>
          <div class="text-xs text-gray-400 mb-4">每次浇水的决策过程完整可查</div>

          <div v-if="!careEvents.length" class="text-center py-6 text-gray-400 text-sm">暂无记录</div>

          <div v-for="(e, idx) in careEvents" :key="e.id"
               class="py-2.5" :class="idx < careEvents.length - 1 ? 'border-b border-gray-50' : ''">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0"
                   :class="e.trigger === 'manual' ? 'bg-blue-50' : 'bg-green-50'">
                <span class="text-sm">{{ e.trigger === 'manual' ? '👆' : '🤖' }}</span>
              </div>
              <div class="flex-1">
                <div class="text-sm font-medium text-gray-700">{{ reasonLabel(e.r) }}</div>
                <div class="text-xs text-gray-400">{{ formatTime(e.t) }}</div>
              </div>
              <div class="text-right">
                <div class="text-sm font-medium text-blue-500">{{ e.d }}秒</div>
                <div v-if="e.moisture_before != null" class="text-xs text-gray-400">浇前 {{ Math.round(e.moisture_before) }}%</div>
              </div>
            </div>

            <!-- 决策因子 -->
            <div v-if="e.factors && e.factors.length" class="ml-12 mt-1">
              <button @click="e._open = !e._open"
                      class="text-xs text-blue-500 flex items-center gap-1">
                {{ e._open ? '▾' : '▸' }} 查看决策过程
                <span v-if="e.final_score != null" class="text-gray-400">（综合分 {{ Math.round(e.final_score * 100) }}）</span>
              </button>
              <div v-if="e._open" class="mt-2 space-y-1.5">
                <div v-for="f in e.factors" :key="f.key"
                     class="flex items-start gap-2 bg-gray-50 rounded-xl px-3 py-2">
                  <span class="text-xs flex-shrink-0">{{ factorIcon(f.level) }}</span>
                  <div class="flex-1 text-xs text-gray-500">
                    <span class="font-medium text-gray-600">{{ f.name }}：</span>{{ f.detail }}
                  </div>
                  <span class="text-xs font-mono flex-shrink-0"
                        :class="f.score > 0 ? 'text-blue-400' : f.score < 0 ? 'text-red-400' : 'text-gray-400'">
                    {{ f.score > 0 ? '+' : '' }}{{ Math.round(f.score * 100) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 养护贴士 -->
        <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-3xl p-5 border border-green-100 mb-4">
          <div class="font-semibold text-green-800 mb-2">🌿 {{ plant.profile?.name_zh }} 养护小贴士</div>
          <div class="text-sm text-green-700 leading-relaxed">{{ plant.profile?.watering?.notes }}</div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip } from 'chart.js'
import { getTimeOfDay, getSeason, getSeasonEmoji, getPlantMood, getActionAdvice, getHeaderGradient } from '../utils/plant.js'

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip)

const route = useRoute()
const plant = ref(null)
const loading = ref(true)
const watering = ref(false)
const waterDuration = ref(5)
const settings = ref({
  auto_water_enabled: true,
  auto_water_threshold: 0.15,
  custom_duration_seconds: null,
  custom_min_interval_hours: null,
  default_min_interval_hours: 1,
  default_duration_seconds: 10,
})

const timeOfDay = getTimeOfDay()
const season = getSeason()
const seasonEmoji = getSeasonEmoji(season)
const seasonName = { spring: '春季', summer: '夏季', autumn: '秋季', winter: '冬季' }[season]
const timeLabel = { morning: '清晨', forenoon: '上午', noon: '正午', afternoon: '下午', evening: '傍晚', night: '夜间' }[timeOfDay]

const currentMoisture = computed(() => {
  const r = plant.value?.readings
  return r?.length ? r[r.length - 1].m : null
})

const level = computed(() => Math.max(1, Math.min(5, Math.floor((plant.value?.health_score ?? 0) / 20))))
const levelLabel = computed(() => ['','幼苗','成长','茁壮','旺盛','满级'][level.value])
const mood = computed(() => getPlantMood(plant.value?.status, plant.value?.nickname))
const headerGradient = computed(() => getHeaderGradient(plant.value?.status))

const plantFace = computed(() => ({
  ok:'🌿', dry:'🥀', critical_dry:'🌵', wet:'🌊', critical_wet:'😰', unknown:'🌱'
})[plant.value?.status] ?? '🌱')

const statusText = computed(() => ({
  ok:'😊 状态良好', dry:'😕 有点渴', critical_dry:'😫 紧急缺水',
  wet:'😌 水分充足', critical_wet:'😰 过湿', unknown:'💤 等待数据'
})[plant.value?.status] ?? '未知')

const moistureColor = computed(() => {
  const m = currentMoisture.value, t = plant.value?.thresholds
  if (m === null || !t) return '#9ca3af'
  if (m < t.critical_low) return '#ef4444'
  if (m < t.target_low)   return '#f97316'
  if (m > t.critical_high) return '#3b82f6'
  return '#22c55e'
})

const healthColorVal = computed(() => {
  const s = plant.value?.health_score ?? 0
  return s >= 80 ? '#22c55e' : s >= 60 ? '#f97316' : '#ef4444'
})

// 决策数据
const decision = computed(() => plant.value?.decision ?? null)
const decisionFactors = computed(() => decision.value?.factors ?? [])
const decisionIcon = computed(() => {
  if (!decision.value) return '💤'
  if (decision.value.urgency === 'urgent') return '🚨'
  if (decision.value.should_water) return '💧'
  return '✅'
})
const decisionVerdict = computed(() => {
  if (!decision.value) return '等待数据'
  if (decision.value.urgency === 'urgent') return `紧急！建议立即浇水 ${decision.value.duration_seconds}秒`
  if (decision.value.should_water) return `建议浇水约 ${decision.value.duration_seconds}秒`
  return '暂时无需浇水，状态良好'
})

// 养护记录（预处理，确保 factors 是数组，_open 控制展开）
const careEvents = computed(() =>
  (plant.value?.watering_events ?? []).slice(0, 10).map(e => ({
    ...e,
    factors: Array.isArray(e.factors) ? e.factors : [],
    _open: false,
  }))
)

function factorIcon(level) {
  return { boost: '🟢', pass: '⚪', warn: '🟡', block: '🔴' }[level] ?? '⚪'
}
function factorLevelLabel(level) {
  return { boost: '促进', pass: '正常', warn: '注意', block: '阻止' }[level] ?? level
}
function factorTagClass(level) {
  return {
    boost: 'bg-green-100 text-green-700',
    pass:  'bg-gray-100 text-gray-500',
    warn:  'bg-yellow-100 text-yellow-700',
    block: 'bg-red-100 text-red-600',
  }[level] ?? 'bg-gray-100 text-gray-500'
}

const chartReadings = computed(() => plant.value?.readings ?? [])
const chartData = computed(() => ({
  labels: chartReadings.value.map(r => {
    const d = new Date(r.t)
    return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
  }),
  datasets: [{
    label: '湿度',
    data: chartReadings.value.map(r => r.m),
    borderColor: '#22c55e',
    backgroundColor: 'rgba(34,197,94,0.08)',
    fill: true, tension: 0.4, pointRadius: 2,
  }]
}))
const chartOptions = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    y: { min: 0, max: 100, ticks: { callback: v => v+'%' }, grid: { color: '#f3f4f6' } },
    x: { ticks: { maxTicksLimit: 5, maxRotation: 0 }, grid: { display: false } }
  }
}

async function load() {
  const id = route.params.id
  if (!id) { loading.value = false; return }
  try {
    const { data } = await axios.get('/api/plants/' + id)
    const thresholds = data.thresholds
    const readings = data.readings ?? []
    const moisture = readings.length ? readings[readings.length - 1].m : null
    let status = 'unknown'
    if (moisture !== null && thresholds) {
      if (moisture <= thresholds.critical_low)      status = 'critical_dry'
      else if (moisture <= thresholds.target_low)   status = 'dry'
      else if (moisture >= thresholds.critical_high) status = 'critical_wet'
      else if (moisture >= thresholds.target_high)   status = 'wet'
      else status = 'ok'
    }
    plant.value = { ...data, status }
    if (data.settings) settings.value = data.settings
  } finally {
    loading.value = false
  }
}

async function manualWater() {
  watering.value = true
  try {
    await axios.post(`/api/plants/${route.params.id}/water`, { duration_seconds: waterDuration.value })
    setTimeout(load, (waterDuration.value + 2) * 1000)
  } finally {
    setTimeout(() => { watering.value = false }, waterDuration.value * 1000)
  }
}

function formatTime(t) {
  if (!t) return '从未'
  const diff = (Date.now() - new Date(t)) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.round(diff/60) + '分钟前'
  if (diff < 86400) return Math.round(diff/3600) + '小时前'
  return `${new Date(t).getMonth()+1}/${new Date(t).getDate()}`
}

function reasonLabel(r) {
  return { manual:'手动浇水', threshold:'自动浇水', critical_dry:'紧急补水', schedule:'定时浇水', moisture_low:'湿度偏低' }[r] ?? (r || '浇水')
}

// 植物特性辅助
const strategyLabel = computed(() => ({
  'keep_moist': '保湿型',
  'dry_between': '干透浇透',
  'dry_then_water': '干透浇透',
  'standard': '标准型',
})[plant.value?.profile?.watering?.strategy] ?? '标准型')

function sensitivityLabel(level) {
  return { very_high: '非常高', high: '极高', medium: '中等', low: '偏低' }[level] ?? level ?? '--'
}
function sensitivityColor(level) {
  return { very_high: 'text-red-600', high: 'text-red-500', medium: 'text-orange-400', low: 'text-green-500' }[level] ?? 'text-gray-500'
}

const SEASON_META = {
  spring: { emoji: '🌸', name: '春' },
  summer: { emoji: '☀️', name: '夏' },
  autumn: { emoji: '🍂', name: '秋' },
  winter: { emoji: '❄️', name: '冬' },
}
const seasonMultipliers = computed(() => {
  const mults = plant.value?.profile?.seasonal_multipliers ?? {}
  return ['spring','summer','autumn','winter'].map(s => ({
    emoji: SEASON_META[s].emoji,
    name: SEASON_META[s].name,
    mult: mults[s] ?? 1.0,
    current: s === season,
  }))
})

async function toggleAutoWater() {
  const val = !settings.value.auto_water_enabled
  settings.value.auto_water_enabled = val
  await axios.patch(`/api/plants/${route.params.id}/settings`, { auto_water_enabled: val })
}

async function updateSetting(key, value) {
  settings.value[key] = value
  await axios.patch(`/api/plants/${route.params.id}/settings`, { [key]: value })
}

onMounted(load)
</script>

<style scoped>
.text-shadow, .text-shadow * {
  text-shadow: 0 1px 3px rgba(0,0,0,0.45);
}
</style>
