<script setup lang="ts">
/**
 * 指标卡（FS-1）：1 个主数字（24px）+ 至多 2 行辅助信息，总高 ≤ 92px。
 * 遵循 docs/frontend-development-plan.md §5.2 指标卡标准。
 */
defineProps<{
  label: string
  value: string | number
  unit?: string
  delta?: string
  deltaTone?: 'up' | 'down' | 'flat' | 'warning' | 'danger'
  hint?: string
}>()
</script>

<template>
  <div class="stat-card">
    <div class="stat-label">{{ label }}</div>
    <div class="stat-value-row">
      <span class="stat-value num">{{ value }}</span>
      <span v-if="unit" class="stat-unit">{{ unit }}</span>
    </div>
    <div class="stat-foot">
      <span v-if="delta" class="stat-delta" :class="`delta-${deltaTone ?? 'flat'}`">{{ delta }}</span>
      <span v-else-if="hint" class="stat-hint">{{ hint }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 84px;
  max-height: 92px;
  padding: 12px 16px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  box-shadow: var(--sf-shadow);
}
.stat-label {
  font-size: 12px;
  color: var(--sf-text-secondary);
  margin-bottom: 4px;
}
.stat-value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.stat-value {
  font-size: 24px;
  font-weight: 650;
  line-height: 1.15;
  color: var(--sf-text);
}
.stat-unit {
  font-size: 12px;
  color: var(--sf-text-faint);
}
.stat-foot {
  margin-top: 4px;
  font-size: 12px;
  min-height: 16px;
}
.stat-delta {
  font-weight: 500;
}
.delta-up {
  color: var(--sf-danger);
}
.delta-down {
  color: var(--sf-success);
}
.delta-flat {
  color: var(--sf-text-secondary);
}
.delta-warning {
  color: var(--sf-warning);
}
.delta-danger {
  color: var(--sf-danger);
}
.stat-hint {
  color: var(--sf-text-faint);
}
</style>