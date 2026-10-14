<script setup lang="ts">
/**
 * 状态/情感/优先级徽标：语义色背景 + 短文案。
 * tone: success | warning | danger | info | neutral | muted
 */
defineProps<{
  label: string
  tone?: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'muted'
}>()
</script>

<template>
  <span class="badge" :class="`tone-${tone ?? 'neutral'}`">{{ label }}</span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 12px;
  line-height: 18px;
  white-space: nowrap;
}
.tone-success {
  color: var(--sf-success);
  background: var(--sf-success-soft);
}
.tone-warning {
  color: var(--sf-warning);
  background: var(--sf-warning-soft);
}
.tone-danger {
  color: var(--sf-danger);
  background: var(--sf-danger-soft);
}
.tone-info {
  color: var(--sf-info);
  background: var(--sf-info-soft);
}
.tone-neutral {
  color: var(--sf-text-secondary);
  background: var(--sf-bg);
  border: 1px solid var(--sf-border);
}
.tone-muted {
  color: var(--sf-text-faint);
  background: transparent;
  border: 1px solid var(--sf-border);
}
</style>