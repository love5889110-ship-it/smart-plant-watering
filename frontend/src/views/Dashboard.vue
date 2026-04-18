<template>
  <div class="min-h-screen pb-28 relative overflow-hidden">

    <!-- 动态背景 -->
    <div class="fixed inset-0 -z-10 transition-all duration-1000"
         :style="{ background: bgGradient }"></div>

    <!-- 季节漂浮粒子 -->
    <div class="fixed inset-0 -z-10 pointer-events-none overflow-hidden">
      <div v-for="p in floatingParticles" :key="p.id"
           class="absolute select-none animate-float"
           :style="p.style">{{ p.emoji }}</div>
    </div>

    <!-- 顶部 Header -->
    <div class="px-5 pt-14 pb-4 text-shadow">
      <div class="flex items-start justify-between">
        <div>
          <div class="text-white font-medium text-sm">{{ greeting }}</div>
          <div class="text-white font-bold text-2xl mt-0.5">我的花园</div>
          <div class="flex items-center gap-2 mt-2 flex-wrap">
            <span class="bg-white/20 text-white text-xs px-2.5 py-1 rounded-full font-medium">{{ seasonEmoji }} {{ seasonName }}</span>
            <span class="bg-white/20 text-white text-xs px-2.5 py-1 rounded-full">{{ timeLabel }}</span>
          </div>
        </div>
        <button @click="refresh"
                class="bg-white/20 backdrop-blur text-white rounded-2xl p-3 active:scale-90 transition-transform mt-1">
          <span :class="{ 'animate-spin inline-block': loading }">🔄</span>
        </button>
      </div>

      <!-- 总览统计 -->
      <div class="grid grid-cols-3 gap-2.5 mt-4">
        <div class="bg-white/20 backdrop-blur rounded-2xl py-3 text-center">
          <div class="text-2xl font-bold text-white">{{ plants.length }}</div>
          <div class="text-white/90 text-xs mt-0.5 font-medium">植物</div>
        </div>
        <div class="bg-white/20 backdrop-blur rounded-2xl py-3 text-center">
          <div class="text-2xl font-bold text-white">{{ healthyCount }}</div>
          <div class="text-white/90 text-xs mt-0.5 font-medium">状态良好</div>
        </div>
        <div class="bg-white/20 backdrop-blur rounded-2xl py-3 text-center">
          <div class="text-2xl font-bold" :class="needWaterCount > 0 ? 'text-yellow-300' : 'text-white'">
            {{ needWaterCount }}
          </div>
          <div class="text-white/90 text-xs mt-0.5 font-medium">需要浇水</div>
        </div>
      </div>
    </div>

    <!-- 今日行动任务卡片 -->
    <div v-if="globalAdvice.length > 0" class="mx-4 mb-5 text-shadow">
      <div class="text-white text-xs font-bold uppercase tracking-wider mb-2 px-1">📋 今日任务</div>
      <div class="space-y-2.5">
        <div v-for="a in globalAdvice" :key="a.text"
             class="flex items-center gap-3 rounded-2xl px-4 py-3 backdrop-blur transition-all active:scale-95"
             :class="a.urgent ? 'bg-red-500/40 border border-red-200/40' : 'bg-white/20'">
          <!-- 图标 -->
          <div class="text-xl w-8 text-center flex-shrink-0">{{ a.icon }}</div>
          <!-- 文字 -->
          <div class="flex-1 min-w-0">
            <div class="text-white text-sm font-semibold leading-snug" :class="a.urgent ? 'text-yellow-200' : ''">
              {{ a.text }}
            </div>
          </div>
          <!-- 行动标签 -->
          <div v-if="a.action === 'water'"
               class="text-xs bg-blue-400/30 text-blue-100 px-2 py-0.5 rounded-full flex-shrink-0">浇水</div>
          <div v-else-if="a.action === 'fertilize'"
               class="text-xs bg-green-400/30 text-green-100 px-2 py-0.5 rounded-full flex-shrink-0">施肥</div>
          <div v-else-if="a.action === 'sunlight'"
               class="text-xs bg-yellow-400/30 text-yellow-100 px-2 py-0.5 rounded-full flex-shrink-0">晒太阳</div>
        </div>
      </div>
    </div>

    <!-- 植物卡片列表 -->
    <div class="px-4 space-y-4">
      <PlantCard
        v-for="plant in plants" :key="plant.id"
        :plant="plant"
        @click="$router.push('/plant/' + plant.id)"
      />

      <!-- 空状态 -->
      <div v-if="!loading && plants.length === 0" class="text-center py-16">
        <div class="text-7xl mb-4 animate-bounce">🪴</div>
        <div class="text-white font-semibold text-lg mb-2">花园还是空的</div>
        <div class="text-white/60 text-sm mb-8">添加你的第一株植物，开始养成之旅</div>
        <button @click="showAdd = true"
                class="bg-white text-green-700 px-8 py-3 rounded-2xl font-semibold shadow-xl active:scale-95 transition-transform">
          🌱 添加植物
        </button>
      </div>
    </div>

    <!-- 添加按钮 -->
    <button v-if="plants.length > 0" @click="showAdd = true"
            class="fixed bottom-8 right-5 bg-white text-green-700 w-16 h-16 rounded-2xl shadow-2xl text-3xl font-bold flex items-center justify-center active:scale-90 transition-all">
      +
    </button>

    <!-- 添加植物弹窗 -->
    <Transition name="slide-up">
      <div v-if="showAdd" class="fixed inset-0 bg-black/60 flex items-end z-50" @click.self="showAdd = false">
        <div class="bg-white w-full rounded-t-3xl p-6 max-h-[92vh] overflow-y-auto">
          <div class="w-10 h-1 bg-gray-200 rounded-full mx-auto mb-6"></div>
          <h2 class="font-bold text-xl mb-1">🌱 选择你的植物</h2>
          <p class="text-gray-400 text-sm mb-5">每株植物都有独特的养护性格</p>

          <div class="grid grid-cols-3 gap-3 mb-5">
            <button v-for="p in profiles" :key="p.id"
                    @click="form.profile_id = p.id"
                    class="p-3 rounded-2xl border-2 text-center transition-all"
                    :class="form.profile_id === p.id ? 'border-green-500 bg-green-50 scale-105' : 'border-gray-100 bg-gray-50'">
              <div class="text-3xl mb-1">{{ p.emoji }}</div>
              <div class="text-xs font-medium text-gray-700">{{ p.name_zh }}</div>
              <div class="text-xs text-gray-400 mt-0.5">{{ p.moisture_thresholds?.target_low }}~{{ p.moisture_thresholds?.target_high }}%</div>
            </button>
          </div>

          <div v-if="selectedProfile" class="rounded-3xl overflow-hidden mb-5 border border-gray-100">
            <div class="bg-gradient-to-r from-green-500 to-emerald-500 p-4 text-white">
              <div class="flex items-center gap-3">
                <div class="text-4xl">{{ selectedProfile.emoji }}</div>
                <div>
                  <div class="font-bold text-lg">{{ selectedProfile.name_zh }}</div>
                  <div class="text-white/70 text-sm">{{ selectedProfile.name_en }}</div>
                </div>
              </div>
            </div>
            <div class="bg-white p-4">
              <div class="grid grid-cols-2 gap-3 mb-3">
                <div class="bg-gray-50 rounded-xl p-3 text-center">
                  <div class="text-xs text-gray-400 mb-1">适宜湿度</div>
                  <div class="font-bold text-green-600">{{ selectedProfile.moisture_thresholds?.target_low }}~{{ selectedProfile.moisture_thresholds?.target_high }}%</div>
                </div>
                <div class="bg-gray-50 rounded-xl p-3 text-center">
                  <div class="text-xs text-gray-400 mb-1">干旱敏感度</div>
                  <div class="font-bold text-orange-500">{{ sensitivityLabel(selectedProfile.sensitivity?.drought) }}</div>
                </div>
              </div>
              <div class="text-xs text-gray-500 mb-2 font-medium">季节需水倍率</div>
              <div class="grid grid-cols-4 gap-1">
                <div v-for="(val, key) in selectedProfile.seasonal_multipliers" :key="key"
                     class="bg-gray-50 rounded-lg p-1.5 text-center">
                  <div class="text-sm">{{ {spring:'🌸',summer:'☀️',autumn:'🍂',winter:'❄️'}[key] }}</div>
                  <div class="text-xs font-bold text-gray-700">x{{ val }}</div>
                </div>
              </div>
              <div class="mt-3 text-xs text-gray-500 leading-relaxed bg-green-50 rounded-xl p-3">
                💬 {{ selectedProfile.watering?.notes }}
              </div>
            </div>
          </div>

          <div class="space-y-3">
            <div>
              <label class="text-sm font-medium text-gray-700 mb-1.5 block">给它起个名字 ✏️</label>
              <input v-model="form.nickname" placeholder="例如：阳台的蓝莓 🫐"
                     class="w-full border-2 border-gray-100 rounded-2xl p-3.5 text-sm focus:outline-none focus:border-green-400 transition-colors" />
            </div>
            <div>
              <label class="text-sm font-medium text-gray-700 mb-1.5 block">绑定设备</label>
              <input v-model="form.device_id" placeholder="esp32_plant_01"
                     class="w-full border-2 border-gray-100 rounded-2xl p-3.5 text-sm font-mono focus:outline-none focus:border-green-400 transition-colors" />
              <div class="text-xs text-gray-400 mt-1 ml-1">固件 config.h 中的 DEVICE_ID</div>
            </div>
            <button @click="addPlant"
                    :disabled="!form.nickname || !form.device_id"
                    class="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white py-4 rounded-2xl font-semibold text-base shadow-lg shadow-green-200 disabled:opacity-40 active:scale-95 transition-all mt-2">
              开始养成 🌱
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import PlantCard from '../components/PlantCard.vue'
import {
  getTimeOfDay, getSeason, getSeasonEmoji, getTimeGreeting,
  getActionAdvice, getBgGradient, getSeasonParticles
} from '../utils/plant.js'

const plants = ref([])
const profiles = ref([])
const loading = ref(true)
const showAdd = ref(false)
const form = ref({ profile_id: 'blueberry', nickname: '', device_id: 'esp32_plant_01' })
let timer = null

const timeOfDay = getTimeOfDay()
const season = getSeason()
const bgGradient = getBgGradient(timeOfDay, season)
const seasonEmoji = getSeasonEmoji(season)
const seasonName = { spring: '春季', summer: '夏季', autumn: '秋季', winter: '冬季' }[season]
const timeLabel = { morning: '清晨', forenoon: '上午', noon: '正午', afternoon: '下午', evening: '傍晚', night: '夜间' }[timeOfDay]
const greeting = getTimeGreeting(timeOfDay)

// 生成漂浮粒子
const floatingParticles = computed(() => {
  const groups = getSeasonParticles(season, timeOfDay)
  const result = []
  let id = 0
  for (const g of groups) {
    for (let i = 0; i < g.count; i++) {
      const left = 5 + Math.random() * 90
      const delay = Math.random() * 8
      const duration = 6 + Math.random() * 8
      const size = 0.8 + Math.random() * 0.8
      result.push({
        id: id++,
        emoji: g.emoji,
        style: {
          left: left + '%',
          bottom: '-10%',
          fontSize: size + 'rem',
          animationDelay: delay + 's',
          animationDuration: duration + 's',
          opacity: 0.4 + Math.random() * 0.4,
        }
      })
    }
  }
  return result
})

const selectedProfile = computed(() => profiles.value.find(p => p.id === form.value.profile_id) ?? null)
const healthyCount = computed(() => plants.value.filter(p => p.status === 'ok').length)
const needWaterCount = computed(() => plants.value.filter(p => ['dry','critical_dry'].includes(p.status)).length)

const globalAdvice = computed(() => {
  const all = plants.value.flatMap(p => getActionAdvice(p, timeOfDay, season))
  const seen = new Set()
  return all.filter(a => { if (seen.has(a.text)) return false; seen.add(a.text); return true }).slice(0, 5)
})

async function refresh() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/dashboard')
    plants.value = data.plants
  } catch(e) { console.error(e) } finally { loading.value = false }
}
async function loadProfiles() {
  const { data } = await axios.get('/api/plant-profiles')
  profiles.value = data
}
async function addPlant() {
  if (!form.value.nickname || !form.value.device_id) return
  await axios.post('/api/plants', form.value)
  showAdd.value = false
  form.value = { profile_id: 'blueberry', nickname: '', device_id: 'esp32_plant_01' }
  refresh()
}
function sensitivityLabel(l) {
  return { low: '低', medium: '中', high: '高', very_high: '极高' }[l] ?? '-'
}

onMounted(() => { refresh(); loadProfiles(); timer = setInterval(refresh, 30000) })
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
/* 粒子向上漂浮 */
@keyframes floatUp {
  0%   { transform: translateY(0) rotate(0deg); opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 0.8; }
  100% { transform: translateY(-110vh) rotate(360deg); opacity: 0; }
}
.animate-float { animation: floatUp linear infinite; }

.slide-up-enter-active, .slide-up-leave-active { transition: all 0.35s cubic-bezier(0.4,0,0.2,1); }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(100%); }

/* 文字阴影 */
.text-shadow, .text-shadow * {
  text-shadow: 0 1px 3px rgba(0,0,0,0.45);
}
</style>
