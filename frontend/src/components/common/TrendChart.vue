<script setup lang="ts">
/**
 * 信号趋势图：纯 SVG 双线（反馈量/已解决），无外部图表库。
 * 遵循 docs/frontend-development-plan.md §5.3/§5.4：紧凑、信号波形品牌隐喻、
 * 数据点 tooltip 用 <title> 表达，150-250ms 过渡。
 */
import { computed } from 'vue'

import type { TrendPoint } from '@/types'

const props = defineProps<{
  points: TrendPoint[]
  height?: number
}>()

const W = 560
const H = computed(() => props.height ?? 160)
const PAD = { top: 12, right: 12, bottom: 24, left: 30 }

const series = computed(() => {
  const pts = props.points
  if (!pts.length) return { lineA: '', lineB: '', dots: [] as Array<{ x: number; y: number; cx: number; cy: number; label: string; count: number; resolved: number }>, max: 1 }
  const max = Math.max(1, ...pts.map((p) => Math.max(p.count, p.resolved)))
  const innerW = W - PAD.left - PAD.right
  const innerH = H.value - PAD.top - PAD.bottom
  const step = pts.length > 1 ? innerW / (pts.length - 1) : 0
  const px = (i: number) => PAD.left + i * step
  const py = (v: number) => PAD.top + innerH - (v / max) * innerH
  const lineA = pts.map((p, i) => `${i ? 'L' : 'M'}${px(i).toFixed(1)},${py(p.count).toFixed(1)}`).join(' ')
  const lineB = pts.map((p, i) => `${i ? 'L' : 'M'}${px(i).toFixed(1)},${py(p.resolved).toFixed(1)}`).join(' ')
  const dots = pts.map((p, i) => ({
    x: px(i),
    y: py(p.count),
    cx: px(i),
    cy: py(p.resolved),
    label: p.label,
    count: p.count,
    resolved: p.resolved,
  }))
  return { lineA, lineB, dots, max }
})

const areaA = computed(() => {
  if (!props.points.length) return ''
  const s = series.value
  const first = s.dots[0]
  const last = s.dots[s.dots.length - 1]
  if (!first || !last) return ''
  return `${s.lineA} L${last.x},${H.value - PAD.bottom} L${first.x},${H.value - PAD.bottom} Z`
})

const gridYs = computed(() => {
  const max = series.value.max
  const ticks = 4
  return Array.from({ length: ticks + 1 }, (_, i) => {
    const v = Math.round((max / ticks) * i)
    const innerH = H.value - PAD.top - PAD.bottom
    return { v, y: PAD.top + innerH - (v / max) * innerH }
  })
})
</script>

<template>
  <div class="trend">
    <svg :viewBox="`0 0 ${W} ${H}`" class="trend-svg" role="img" aria-label="信号趋势图">
      <defs>
        <linearGradient id="sf-area" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="var(--sf-primary)" stop-opacity="0.14" />
          <stop offset="100%" stop-color="var(--sf-primary)" stop-opacity="0" />
        </linearGradient>
      </defs>
      <!-- 网格 -->
      <g v-for="g in gridYs" :key="g.y">
        <line :x1="PAD.left" :x2="W - PAD.right" :y1="g.y" :y2="g.y" class="grid" />
        <text :x="PAD.left - 6" :y="g.y + 3.5" class="tick">{{ g.v }}</text>
      </g>
      <!-- 面积 -->
      <path :d="areaA" fill="url(#sf-area)" />
      <!-- 反馈量线 -->
      <path :d="series.lineA" class="line line-a" />
      <!-- 已解决线 -->
      <path :d="series.lineB" class="line line-b" />
      <!-- 数据点 tooltip -->
      <g v-for="d in series.dots" :key="d.label">
        <circle :cx="d.cx" :cy="d.cy" r="2.5" class="dot dot-b" />
        <rect x="-2" y="-2" width="4" height="4" fill="transparent">
          <title>{{ d.label }} 反馈 {{ d.count }} / 已解决 {{ d.resolved }}</title>
        </rect>
      </g>
      <!-- 横轴标签（隔点显示） -->
      <text
        v-for="(d, i) in series.dots"
        :key="`t-${d.label}`"
        :x="d.x"
        :y="H - 6"
        class="xlabel"
        :class="{ 'xhide': i % 3 !== 0 && series.dots.length > 8 }"
        text-anchor="middle"
      >
        {{ d.label }}
      </text>
    </svg>
    <div class="legend">
      <span class="leg-item"><i class="sw sw-a" />反馈量</span>
      <span class="leg-item"><i class="sw sw-b" />已解决</span>
    </div>
  </div>
</template>

<style scoped>
.trend {
  width: 100%;
}
.trend-svg {
  display: block;
  width: 100%;
  height: auto;
  max-height: 180px;
}
.grid {
  stroke: var(--sf-border);
  stroke-width: 1;
  stroke-dasharray: 3 3;
}
.tick {
  fill: var(--sf-text-faint);
  font-size: 10px;
  text-anchor: end;
}
.xlabel {
  fill: var(--sf-text-faint);
  font-size: 10px;
}
.xhide {
  opacity: 0;
}
.line {
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.line-a {
  stroke: var(--sf-primary);
}
.line-b {
  stroke: var(--sf-success);
}
.dot {
  fill: var(--sf-surface);
  stroke-width: 1.5;
}
.dot-b {
  stroke: var(--sf-success);
}
.legend {
  display: flex;
  gap: 12px;
  padding: 4px 2px 0;
}
.leg-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--sf-text-secondary);
}
.sw {
  width: 10px;
  height: 3px;
  border-radius: 2px;
  display: inline-block;
}
.sw-a {
  background: var(--sf-primary);
}
.sw-b {
  background: var(--sf-success);
}
</style>