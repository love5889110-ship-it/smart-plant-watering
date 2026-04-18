<template>
  <div class="rounded-3xl overflow-hidden shadow-lg cursor-pointer active:scale-95 transition-all duration-200 bg-white"
       :class="breatheClass"
       @click="$emit('click')">

    <!-- 上半：彩色区域，只放植物角色 -->
    <div class="relative px-5 pt-5 pb-4 overflow-hidden"
         :style="{ background: cardGradient }">
      <!-- 装饰圆 -->
      <div class="absolute -right-6 -top-6 w-28 h-28 rounded-full bg-white/10 pointer-events-none"></div>

      <!-- 波浪水位 -->
      <div class="absolute bottom-0 left-0 right-0 transition-all duration-1000"
           :style="{ height: waterHeight, background: 'rgba(255,255,255,0.15)' }">
        <svg class="absolute -top-3 left-0 w-[200%] animate-wave" viewBox="0 0 400 15" preserveAspectRatio="none" style="height:15px">
          <path d="M0,8 C50,0 100,15 150,8 C200,0 250,15 300,8 C350,0 400,15 400,8 L400,15 L0,15 Z" fill="white" fill-opacity="0.2"/>
        </svg>
      </div>

      <div class="relative flex items-center gap-4">
        <!-- 植物大表情 -->
        <div class="relative flex-shrink-0">
          <div class="text-6xl select-none" :class="faceAnim">{{ plantFace }}</div>
          <div v-if="plant.status === 'critical_dry'" class="absolute -top-1 -right-1 text-sm animate-bounce">💦</div>
          <div v-if="plant.status === 'ok'" class="absolute -top-1 -right-1 text-xs animate-pulse">✨</div>
        </div>

        <!-- 对话气泡 -->
        <div class="bg-white/90 rounded-2xl rounded-bl-none px-3 py-2 flex-1 shadow-sm">
          <div class="text-gray-800 text-xs leading-snug font-medium">{{ mood }}</div>
        </div>
      </div>
    </div>

    <!-- 下半：白色区域，放所有文字信息 -->
    <div class="px-5 py-4">
      <!-- 名字 + 等级 -->
      <div class="flex items-center justify-between mb-3">
        <div>
          <div class="flex items-center gap-1.5">
            <span class="text-base">{{ plant.emoji }}</span>
            <span class="font-bold text-gray-900 text-base">{{ plant.nickname }}</span>
          </div>
          <div class="text-gray-500 text-xs mt-0.5">{{ plant.profile_name }}</div>
        </div>
        <div class="text-right">
          <div class="font-bold text-sm" :style="{ color: statusColor }">{{ levelLabel }}</div>
          <div class="text-gray-400 text-xs">Lv.{{ level }}</div>
        </div>
      </div>

      <!-- 湿度 + 健康 -->
      <div class="flex items-center gap-3 mb-3">
        <!-- 湿度圆环 -->
        <div class="relative w-16 h-16 flex-shrink-0">
          <svg class="w-full h-full -rotate-90" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="26" fill="none" stroke="#f3f4f6" stroke-width="6"/>
            <circle cx="32" cy="32" r="26" fill="none" stroke-width="6"
                    stroke-linecap="round"
                    :stroke="statusColor"
                    :stroke-dasharray="`${(moisture ?? 0) * 1.633} 163`"
                    class="transition-all duration-1000"/>
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center">
            <div class="font-bold text-sm text-gray-800 leading-none">{{ moisture !== null ? Math.round(moisture) + '%' : '--' }}</div>
            <div class="text-gray-400 text-xs">湿度</div>
          </div>
        </div>

        <!-- 健康条 + 状态 -->
        <div class="flex-1">
          <div class="flex justify-between text-xs mb-1">
            <span class="text-gray-500">健康值</span>
            <span class="font-semibold text-gray-700">{{ plant.health_score }}</span>
          </div>
          <div class="h-2 bg-gray-100 rounded-full overflow-hidden mb-2">
            <div class="h-full rounded-full transition-all duration-700"
                 :style="{ width: plant.health_score + '%', background: statusColor }">
            </div>
          </div>
          <div class="text-xs font-medium" :style="{ color: statusColor }">{{ statusText }}</div>
        </div>
      </div>

      <!-- 底部：浇水时间 + 箭头 -->
      <div class="flex items-center justify-between pt-3 border-t border-gray-100">
        <div class="text-gray-400 text-xs">{{ formatTime(plant.last_watered_at) }}</div>
        <div class="text-gray-300 font-bold text-lg">›</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getPlantMood, getCardGradient, getTimeOfDay, getSeason } from '../utils/plant.js'

const props = defineProps({ plant: Object })
defineEmits(['click'])

const timeOfDay = getTimeOfDay()
const season = getSeason()

const moisture = computed(() => props.plant.current_moisture)
const status = computed(() => props.plant.status)
const mood = computed(() => getPlantMood(status.value, props.plant.nickname, timeOfDay, season))
const level = computed(() => Math.max(1, Math.min(5, Math.floor((props.plant.health_score ?? 0) / 20))))
const levelLabel = computed(() => ['', '幼苗', '成长', '茁壮', '旺盛', '满级'][level.value])
const cardGradient = computed(() => getCardGradient(status.value))

const statusColor = computed(() => ({
  ok:           '#16a34a',
  dry:          '#d97706',
  critical_dry: '#dc2626',
  wet:          '#2563eb',
  critical_wet: '#7c3aed',
  unknown:      '#6b7280',
})[status.value] ?? '#6b7280')

const statusText = computed(() => ({
  ok:           '状态良好 ✓',
  dry:          '有点渴 💧',
  critical_dry: '紧急缺水 🚨',
  wet:          '水分充足 💦',
  critical_wet: '过湿警告 ⚠️',
  unknown:      '等待数据 💤',
})[status.value] ?? '未知')

const waterHeight = computed(() => {
  const pct = Math.min(100, Math.max(0, moisture.value ?? 0))
  return Math.round(pct * 0.5 + 5) + '%'
})

const breatheClass = computed(() => {
  if (status.value === 'critical_dry') return 'animate-pulse-fast'
  if (status.value === 'ok') return 'breathe'
  return ''
})

const plantFace = computed(() => ({
  ok: '🌿', dry: '🥀', critical_dry: '🌵', wet: '🌊', critical_wet: '😰', unknown: '🌱'
})[status.value] ?? '🌱')

const faceAnim = computed(() => {
  if (status.value === 'critical_dry') return 'animate-pulse'
  if (status.value === 'ok') return 'hover:scale-110 transition-transform'
  return ''
})

function formatTime(t) {
  if (!t) return '💧 从未浇水'
  const diff = (Date.now() - new Date(t)) / 1000
  if (diff < 60) return '💧 刚刚浇水'
  if (diff < 3600) return `💧 ${Math.round(diff/60)}分钟前`
  if (diff < 86400) return `💧 ${Math.round(diff/3600)}小时前`
  return `💧 ${Math.round(diff/86400)}天前`
}
</script>

<style scoped>
@keyframes wave {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.animate-wave { animation: wave 3s linear infinite; }

@keyframes breathe {
  0%, 100% { box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
  50%       { box-shadow: 0 8px 32px rgba(0,0,0,0.15); transform: scale(1.01); }
}
.breathe { animation: breathe 4s ease-in-out infinite; }

@keyframes pulseFast {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.8; }
}
.animate-pulse-fast { animation: pulseFast 1s ease-in-out infinite; }
</style>
