<script setup lang="ts">
/**
 * AI 自动化规则配置区：面向政企场景的预设自动化规则卡片。
 * 支持开关切换与快速统计展示。
 */
import { onMounted } from 'vue'

import SfIcon from '@/components/common/SfIcon.vue'
import { useAIStore } from '@/stores/ai'

const ai = useAIStore()

const toneBg: Record<string, string> = {
  primary: 'var(--sf-primary-soft)',
  success: 'var(--sf-success-soft)',
  warning: 'var(--sf-warning-soft)',
  info: 'var(--sf-info-soft)',
  danger: 'var(--sf-danger-soft)',
}
const toneColor: Record<string, string> = {
  primary: 'var(--sf-primary)',
  success: 'var(--sf-success)',
  warning: 'var(--sf-warning)',
  info: 'var(--sf-info)',
  danger: 'var(--sf-danger)',
}

const iconMap: Record<string, string> = {
  tags: 'label',
  message: 'chat',
  alert: 'alert',
  sentiment: 'sentiment',
  checklist: 'checklist',
  clock: 'clock',
}

onMounted(() => {
  void ai.fetchRules()
})
</script>

<template>
  <div class="auto-panel">
    <div class="auto-header">
      <div class="auto-title">
        <SfIcon name="magic" :size="14" />
        AI 自动化扩展
      </div>
      <div class="auto-sub">
        面向政企场景的自动化业务处理规则 ·
        <span class="auto-enabled">{{ ai.rules.filter((r) => r.enabled).length }}/{{ ai.rules.length }} 已启用</span>
      </div>
    </div>

    <div class="auto-grid">
      <div
        v-for="rule in ai.rules"
        :key="rule.id"
        class="auto-card"
        :class="{ 'auto-card--off': !rule.enabled }"
      >
        <div class="auto-card-top">
          <div class="auto-icon" :style="{ background: toneBg[rule.tone], color: toneColor[rule.tone] }">
            <SfIcon :name="(iconMap[rule.icon] ?? 'circle') as any" :size="16" />
          </div>
          <label class="auto-toggle">
            <input
              type="checkbox"
              :checked="rule.enabled"
              @change="ai.toggleRule(rule.id)"
            />
            <span class="auto-toggle-track">
              <span class="auto-toggle-knob" />
            </span>
          </label>
        </div>
        <div class="auto-card-name">{{ rule.name }}</div>
        <div class="auto-card-desc">{{ rule.description }}</div>
        <div class="auto-card-foot">
          <span class="auto-scenario">{{ rule.scenario }}</span>
          <span v-if="rule.stats" class="auto-stats">{{ rule.stats }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auto-panel {
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  padding: var(--sf-space-3);
}
.auto-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--sf-space-2);
  margin-bottom: var(--sf-space-3);
}
.auto-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--sf-font-14);
  font-weight: 600;
  color: var(--sf-text);
}
.auto-sub {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.auto-enabled {
  color: var(--sf-success);
  font-weight: 500;
}

.auto-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--sf-space-3);
}
.auto-card {
  padding: var(--sf-space-3);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-bg);
  border: 1px solid var(--sf-border);
  transition: opacity 0.15s;
}
.auto-card--off {
  opacity: 0.65;
}
.auto-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--sf-space-2);
}
.auto-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.auto-toggle {
  position: relative;
  display: inline-block;
  width: 36px;
  height: 20px;
  cursor: pointer;
}
.auto-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}
.auto-toggle-track {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  background: var(--sf-border);
  transition: background 0.2s;
}
.auto-toggle input:checked + .auto-toggle-track {
  background: var(--sf-primary);
}
.auto-toggle-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.2s;
  box-shadow: 0 1px 2px rgba(0,0,0,0.12);
}
.auto-toggle input:checked + .auto-toggle-track .auto-toggle-knob {
  transform: translateX(16px);
}

.auto-card-name {
  font-size: var(--sf-font-14);
  font-weight: 600;
  color: var(--sf-text);
  margin-bottom: 4px;
}
.auto-card-desc {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  line-height: 1.5;
  margin-bottom: var(--sf-space-2);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.auto-card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
}
.auto-scenario {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: var(--sf-font-11);
  background: var(--sf-primary-soft);
  color: var(--sf-primary);
  font-weight: 500;
}
.auto-stats {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
}
</style>
