<script setup lang="ts">
/**
 * 横向占比条：用于渠道分布/信号强度等量化展示。
 * 数值条颜色由 tone 映射到语义色；宽度百分比由外部保证 0-100。
 */
defineProps<{
  label: string
  value: number
  pct: number
  tone?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'neutral'
}>()
</script>

<template>
  <div class="bar-row">
    <div class="bar-top">
      <span class="bar-label">{{ label }}</span>
      <span class="bar-value num">{{ value }}</span>
    </div>
    <div class="bar-track">
      <div class="bar-fill" :class="`fill-${tone ?? 'primary'}`" :style="{ width: `${Math.min(100, Math.max(0, pct))}%` }" />
    </div>
  </div>
</template>

<style scoped>
.bar-row + .bar-row {
  margin-top: 8px;
}
.bar-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 3px;
}
.bar-label {
  font-size: 12px;
  color: var(--sf-text-secondary);
}
.bar-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--sf-text);
}
.bar-track {
  height: 6px;
  border-radius: 3px;
  background: var(--sf-bg);
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.25s ease;
}
.fill-primary {
  background: var(--sf-primary);
}
.fill-success {
  background: var(--sf-success);
}
.fill-warning {
  background: var(--sf-warning);
}
.fill-danger {
  background: var(--sf-danger);
}
.fill-info {
  background: var(--sf-info);
}
.fill-neutral {
  background: var(--sf-text-faint);
}
</style>