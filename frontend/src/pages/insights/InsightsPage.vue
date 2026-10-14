<script setup lang="ts">
/**
 * FS-3 洞察与决策：噪音 → 洞察。
 * 左=主题/痛点列表（反馈数/强度条/优先级分）；右=选中主题详情（证据链 + 评分卡）。
 * 理念：每个主题可解释、可下钻到原始反馈原文；一屏一焦点（优先级评分卡）。
 */
import { computed, onMounted, ref } from 'vue'

import BarRow from '@/components/common/BarRow.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { InsightTopic, PriorityLevel } from '@/types'
import { useInsightsStore } from '@/stores/insights'
import { formatDate } from '@/utils'
import { priorityLabels, priorityTone, sentimentLabels, sentimentTone, sourceLabels } from '@/utils/labels'

const insights = useInsightsStore()
const selectedId = ref<string | null>(null)

const topics = computed(() => insights.dashboard?.items ?? [])
const selected = computed<InsightTopic | null>(() => {
  if (!selectedId.value) return topics.value[0] ?? null
  return topics.value.find((t) => t.id === selectedId.value) ?? null
})

const trendMeta: Record<InsightTopic['trend'], { label: string; tone: 'success' | 'warning' | 'neutral' }> = {
  up: { label: '上升', tone: 'warning' },
  flat: { label: '平稳', tone: 'neutral' },
  down: { label: '回落', tone: 'success' },
}

const levelTone: Record<PriorityLevel, 'danger' | 'warning' | 'info' | 'neutral'> = priorityTone

onMounted(() => {
  void insights.fetchDashboard()
})

function select(id: string) {
  selectedId.value = id
}
</script>

<template>
  <div class="ins">
    <section class="card left">
      <div class="head">
        <h2 class="title">主题与痛点</h2>
        <span class="sub">{{ topics.length }} 个主题</span>
      </div>
      <Skeleton v-if="insights.dashboardLoading" :rows="6" />
      <div v-else class="topic-list">
        <button
          v-for="t in topics"
          :key="t.id"
          type="button"
          class="topic"
          :class="{ active: selected && t.id === selected.id }"
          @click="select(t.id)"
        >
          <div class="topic-top">
            <span class="topic-title">{{ t.title }}</span>
            <StatusBadge
              :label="`${priorityLabels[t.score_card.level]} ${t.priority_score}`"
              :tone="levelTone[t.score_card.level]"
            />
          </div>
          <p class="topic-short">{{ t.short }}</p>
          <BarRow :label="`${t.feedback_count} 条反馈 · ${t.customer_count} 客户`" :value="t.strength" :pct="t.strength" tone="info" />
          <span class="topic-meta">
            强度 {{ t.strength }}
            <StatusBadge :label="trendMeta[t.trend].label" :tone="trendMeta[t.trend].tone" />
          </span>
        </button>
      </div>
    </section>

    <section class="card right">
      <Skeleton v-if="insights.dashboardLoading" :rows="8" />
      <div v-else-if="selected" class="detail">
        <div class="head">
          <div>
            <h2 class="title">{{ selected.title }}</h2>
            <p class="short">{{ selected.short }}</p>
          </div>
          <StatusBadge :label="priorityLabels[selected.score_card.level]" :tone="levelTone[selected.score_card.level]" />
        </div>

        <div class="grid2">
          <div class="score-box">
            <div class="score-nums">
              <span class="score-total num">{{ selected.score_card.total }}</span>
              <span class="score-max">/ {{ selected.score_card.max }}</span>
            </div>
            <div class="score-dims">
              <div v-for="d in selected.score_card.dimensions" :key="d.key" class="dim-item">
                <div class="dim-top">
                  <span>{{ d.label }}</span>
                  <span class="num">{{ d.score }}/{{ d.max }}</span>
                </div>
                <div class="dim-track">
                  <div class="dim-fill" :style="{ width: `${(d.score / d.max) * 100}%` }" />
                </div>
                <span class="dim-note">{{ d.note }}</span>
              </div>
            </div>
          </div>

          <div class="evidence">
            <h3 class="sec-title">证据链</h3>
            <ul class="ev-list">
              <li v-for="e in selected.evidence" :key="e.feedback_id" class="ev">
                <div class="ev-top">
                  <span class="ev-id">{{ e.feedback_id }}</span>
                  <StatusBadge :label="sentimentLabels[e.sentiment]" :tone="sentimentTone[e.sentiment]" />
                  <span class="ev-src">{{ sourceLabels[e.source] }}</span>
                </div>
                <p class="ev-text">{{ e.excerpt }}</p>
                <span class="ev-meta">{{ e.author }} · {{ formatDate(e.created_at) }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <p v-else class="empty-text">无主题数据</p>
    </section>
  </div>
</template>

<style scoped>
.ins {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: var(--sf-space-3);
  align-items: start;
}
.card {
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  box-shadow: var(--sf-shadow);
  padding: var(--sf-space-3) var(--sf-space-4);
}
.head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: var(--sf-space-2);
}
.title {
  margin: 0;
  font-size: var(--sf-font-14);
  font-weight: 600;
}
.sub {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.short {
  margin: 4px 0 0;
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
}
.topic-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
}
.topic {
  display: block;
  width: 100%;
  text-align: left;
  padding: var(--sf-space-2);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text);
  cursor: pointer;
}
.topic:hover {
  border-color: var(--sf-primary-border);
}
.topic.active {
  border-color: var(--sf-primary);
  background: var(--sf-primary-soft);
}
.topic-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
}
.topic-title {
  font-size: var(--sf-font-13);
  font-weight: 600;
}
.topic-short {
  margin: 4px 0 6px;
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.topic-meta {
  display: inline-flex;
  align-items: center;
  gap: var(--sf-space-2);
  margin-top: 3px;
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.detail {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.grid2 {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: var(--sf-space-4);
}
.score-box {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  padding: var(--sf-space-3);
}
.score-nums {
  display: flex;
  align-items: baseline;
  margin-bottom: var(--sf-space-3);
}
.score-total {
  font-size: var(--sf-font-24);
  font-weight: 700;
  color: var(--sf-primary);
}
.score-max {
  font-size: var(--sf-font-13);
  color: var(--sf-text-faint);
}
.score-dims {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.dim-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.dim-top {
  display: flex;
  justify-content: space-between;
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
}
.dim-track {
  height: 5px;
  border-radius: 3px;
  background: var(--sf-bg);
  overflow: hidden;
}
.dim-fill {
  height: 100%;
  background: var(--sf-primary);
  border-radius: 3px;
}
.dim-note {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.sec-title {
  margin: 0 0 var(--sf-space-2);
  font-size: var(--sf-font-14);
  font-weight: 600;
}
.ev-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.ev {
  padding: var(--sf-space-2) 0;
  border-bottom: 1px solid var(--sf-border);
}
.ev:last-child {
  border-bottom: none;
}
.ev-top {
  display: flex;
  align-items: center;
  gap: var(--sf-space-2);
}
.ev-id {
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-text-secondary);
}
.ev-src {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.ev-text {
  margin: 4px 0;
  font-size: var(--sf-font-13);
  line-height: 1.45;
}
.ev-meta {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.empty-text {
  color: var(--sf-text-faint);
  font-size: var(--sf-font-13);
}
@media (max-width: 1100px) {
  .ins {
    grid-template-columns: 1fr;
  }
  .grid2 {
    grid-template-columns: 1fr;
  }
}
</style>