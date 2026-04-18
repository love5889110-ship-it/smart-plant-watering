<!-- 环形湿度表盘组件 -->
<template>
  <div class="flex flex-col items-center">
    <svg :width="size" :height="size" viewBox="0 0 120 120">
      <!-- 背景圆弧 -->
      <circle cx="60" cy="60" :r="radius" fill="none" stroke="#e5e7eb"
              :stroke-width="strokeWidth" stroke-linecap="round"
              :stroke-dasharray="circumference"
              :stroke-dashoffset="0"
              transform="rotate(-210 60 60)" />
      <!-- 湿度圆弧 -->
      <circle cx="60" cy="60" :r="radius" fill="none" :stroke="arcColor"
              :stroke-width="strokeWidth" stroke-linecap="round"
              :stroke-dasharray="circumference"
              :stroke-dashoffset="dashOffset"
              transform="rotate(-210 60 60)"
              style="transition: stroke-dashoffset 0.8s ease, stroke 0.5s ease" />
      <!-- 中间数字 -->
      <text x="60" y="58" text-anchor="middle" dominant-baseline="middle"
            class="font-bold" :style="{ fontSize: '22px', fill: arcColor, fontWeight: 700 }">
        {{ displayValue }}
      </text>
      <text x="60" y="76" text-anchor="middle" dominant-baseline="middle"
            style="font-size:11px; fill:#6b7280">%</text>
    </svg>
    <span class="text-xs mt-1 font-medium" :style="{ color: arcColor }">{{ statusLabel }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  moisture: { type: Number, default: null },
  thresholds: { type: Object, default: () => ({}) },
  size: { type: Number, default: 120 },
})

const radius = 48
const strokeWidth = 10
const arcAngle = 240  // 圆弧跨度240度
const circumference = computed(() => 2 * Math.PI * radius * (arcAngle / 360))

const displayValue = computed(() => props.moisture !== null ? Math.round(props.moisture) : '--')

const dashOffset = computed(() => {
  if (props.moisture === null) return circumference.value
  const pct = Math.max(0, Math.min(100, props.moisture)) / 100
  return circumference.value * (1 - pct)
})

const arcColor = computed(() => {
  const m = props.moisture
  const t = props.thresholds
  if (m === null) return '#9ca3af'
  if (t.critical_low && m <= t.critical_low) return '#ef4444'
  if (t.target_low && m <= t.target_low) return '#f97316'
  if (t.critical_high && m >= t.critical_high) return '#3b82f6'
  if (t.target_high && m >= t.target_high) return '#60a5fa'
  return '#22c55e'
})

const statusLabel = computed(() => {
  const m = props.moisture
  const t = props.thresholds
  if (m === null) return '无数据'
  if (t.critical_low && m <= t.critical_low) return '严重缺水!'
  if (t.target_low && m <= t.target_low) return '需要浇水'
  if (t.critical_high && m >= t.critical_high) return '过湿!'
  if (t.target_high && m >= t.target_high) return '稍湿'
  return '状态良好'
})
</script>
