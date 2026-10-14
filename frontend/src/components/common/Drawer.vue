<script setup lang="ts">
/**
 * 右侧抽屉（反馈详情/主题详情）：480px，覆盖层 + 滑入过渡。
 * emits: close
 */
import SfIcon from './SfIcon.vue'

defineProps<{
  open: boolean
  title?: string
  width?: number
}>()
const emit = defineEmits<{ (e: 'close'): void }>()

function onMask() {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="drawer-wrap">
        <div class="mask" @click="onMask" />
        <aside class="drawer" :style="{ width: `${width ?? 480}px` }" role="dialog" aria-modal="true">
          <header class="drawer-head">
            <h3 class="drawer-title">{{ title ?? '' }}</h3>
            <button type="button" class="icon-btn" title="关闭" @click="onMask">
              <SfIcon name="close" :size="18" />
            </button>
          </header>
          <div class="drawer-body">
            <slot />
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-wrap {
  position: fixed;
  inset: 0;
  z-index: 50;
}
.mask {
  position: absolute;
  inset: 0;
  background: rgba(2, 6, 23, 0.32);
}
.drawer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  max-width: calc(100vw - 24px);
  background: var(--sf-surface);
  border-left: 1px solid var(--sf-border);
  box-shadow: -8px 0 24px rgba(2, 6, 23, 0.12);
}
.drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 12px 0 16px;
  border-bottom: 1px solid var(--sf-border);
  flex-shrink: 0;
}
.drawer-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--sf-radius-sm);
  background: transparent;
  color: var(--sf-text-secondary);
  cursor: pointer;
}
.icon-btn:hover {
  background: var(--sf-bg);
  color: var(--sf-text);
}
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.2s ease;
}
.drawer-enter-active .drawer,
.drawer-leave-active .drawer {
  transition: transform 0.2s ease;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from .drawer,
.drawer-leave-to .drawer {
  transform: translateX(24px);
}
</style>