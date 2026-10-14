<script setup lang="ts">
/**
 * AI 工作流状态面板：展示当前 AI 正在处理的任务与进度。
 */
import { computed, onMounted } from 'vue'

import SfIcon from '@/components/common/SfIcon.vue'
import { useAIStore } from '@/stores/ai'

const ai = useAIStore()

const statusIcon = computed(() => (s: string) => {
  switch (s) {
    case 'running': return 'spinner'
    case 'completed': return 'check'
    case 'failed': return 'alert'
    case 'queued': return 'clock'
    default: return 'circle'
  }
})

const statusLabel = computed(() => (s: string) => {
  switch (s) {
    case 'running': return '运行中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'queued': return '等待中'
    default: return s
  }
})

const statusTone = computed(() => (s: string) => {
  switch (s) {
    case 'running': return 'primary'
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'queued': return 'neutral'
    default: return 'neutral'
  }
})

onMounted(() => {
  void ai.fetchWorkflows()
})
</script>

<template>
  <div class="wf-panel">
    <div class="wf-header">
      <div class="wf-title">
        <SfIcon name="spinner" :size="14" />
        AI 工作流运行状态
      </div>
      <div class="wf-count">
        <span class="wf-badge running">{{ ai.runningWorkflows.length }} 运行中</span>
        <span class="wf-badge completed">{{ ai.completedToday }} 已完成</span>
      </div>
    </div>

    <div class="wf-list">
      <div v-for="wf in ai.workflows" :key="wf.id" class="wf-item">
        <div class="wf-top">
          <div class="wf-name">
            <SfIcon :name="statusIcon(wf.status)" :size="12" />
            {{ wf.name }}
          </div>
          <span class="wf-tag" :class="`tag-${statusTone(wf.status)}`">{{ statusLabel(wf.status) }}</span>
        </div>
        <div class="wf-bar-wrap">
          <div class="wf-bar-bg">
            <div class="wf-bar-fill" :class="`fill-${statusTone(wf.status)}`" :style="{ width: `${wf.progress}%` }" />
          </div>
          <span class="wf-pct">{{ wf.progress }}%</span>
        </div>
        <div class="wf-detail">{{ wf.detail }}</div>
        <div v-if="wf.eta" class="wf-eta">预计 {{ wf.eta }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wf-panel {
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  padding: var(--sf-space-3);
}
.wf-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--sf-space-3);
}
.wf-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--sf-font-14);
  font-weight: 600;
  color: var(--sf-text);
}
.wf-count {
  display: flex;
  gap: var(--sf-space-2);
}
.wf-badge {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: var(--sf-font-11);
  font-weight: 500;
}
.wf-badge.running {
  background: var(--sf-info-soft);
  color: var(--sf-info);
}
.wf-badge.completed {
  background: var(--sf-success-soft);
  color: var(--sf-success);
}

.wf-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--sf-space-3);
}
.wf-item {
  padding: var(--sf-space-3);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-bg);
  border: 1px solid var(--sf-border);
}
.wf-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.wf-name {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--sf-font-13);
  font-weight: 500;
  color: var(--sf-text);
}
.wf-tag {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: var(--sf-font-11);
  font-weight: 500;
}
.tag-primary { background: var(--sf-primary-soft); color: var(--sf-primary); }
.tag-success { background: var(--sf-success-soft); color: var(--sf-success); }
.tag-danger  { background: var(--sf-danger-soft);  color: var(--sf-danger); }
.tag-neutral { background: var(--sf-bg);            color: var(--sf-text-secondary); border: 1px solid var(--sf-border); }

.wf-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.wf-bar-bg {
  flex: 1;
  height: 5px;
  border-radius: 3px;
  background: var(--sf-border);
  overflow: hidden;
}
.wf-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}
.fill-primary { background: var(--sf-primary); }
.fill-success { background: var(--sf-success); }
.fill-danger  { background: var(--sf-danger); }
.fill-neutral { background: var(--sf-text-faint); }
.wf-pct {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  min-width: 30px;
  text-align: right;
}

.wf-detail {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  line-height: 1.45;
}
.wf-eta {
  margin-top: 4px;
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
}
</style>
