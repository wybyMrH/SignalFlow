<script setup lang="ts">
/** 空态：紧凑示意 + 一行说明。 */
import SfIcon from './SfIcon.vue'

defineProps<{
  text?: string
}>()
</script>

<template>
  <div class="empty">
    <SfIcon name="file" :size="22" />
    <span class="empty-text">{{ text ?? '暂无数据' }}</span>
  </div>
</template>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px 12px;
  color: var(--sf-text-faint);
}
.empty-text {
  font-size: 13px;
}
</style>