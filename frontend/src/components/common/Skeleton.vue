<script setup lang="ts">
/** 骨架加载块：lint 语义色呼吸动画，渲染时按行数生成。 */
defineProps<{
  rows?: number
}>()
</script>

<template>
  <div class="skeleton" aria-busy="true">
    <div v-for="i in rows ?? 3" :key="i" class="line" :style="{ width: `${90 - (i % 3) * 12}%` }" />
  </div>
</template>

<style scoped>
.skeleton {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 0;
}
.line {
  height: 12px;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--sf-border) 25%, var(--sf-bg) 50%, var(--sf-border) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.3s infinite;
}
@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>