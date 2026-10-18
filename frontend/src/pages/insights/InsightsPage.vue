<script setup lang="ts">
/**
 * FS-3 洞察与决策：噪音 → 洞察。
 * 左=主题/痛点列表（反馈数/强度条/优先级分）；右=选中主题详情（证据链 + 评分卡）。
 * 理念：每个主题可解释、可下钻到原始反馈原文；一屏一焦点（优先级评分卡）。
 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import AIFloatingAssistant from '@/components/ai/AIFloatingAssistant.vue'
import BarRow from '@/components/common/BarRow.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { getTopicCases, type CaseStatus, type GovernanceCase } from '@/mocks/cases'
import { useInsightsStore } from '@/stores/insights'
import type { InsightTopic, PriorityLevel, RoadmapItem } from '@/types'
import { formatDate } from '@/utils'
import { priorityLabels, priorityTone, sentimentLabels, sentimentTone, sourceLabels } from '@/utils/labels'

const insights = useInsightsStore()
const router = useRouter()
const selectedId = ref<string | null>(null)

const topics = computed(() => insights.dashboard?.items ?? [])
const selected = computed<InsightTopic | null>(() => {
  if (!selectedId.value) return topics.value[0] ?? null
  return topics.value.find((t) => t.id === selectedId.value) ?? null
})

/** 治理案例（按当前主题） */
const selectedCases = computed<GovernanceCase[]>(() => (selected.value ? getTopicCases(selected.value.id) : []))

/** 路线图项（供闭环选目标规划） */
const roadmapItems = computed<RoadmapItem[]>(() => insights.roadmap?.items ?? [])
const caseStatusMeta: Record<CaseStatus, { label: string; tone: 'success' | 'info' | 'neutral' }> = {
  done: { label: '已落地', tone: 'success' },
  doing: { label: '推进中', tone: 'info' },
  planned: { label: '已规划', tone: 'neutral' },
}

const targetRoadmapId = ref('')
const creating = ref(false)
const createdMsg = ref<{ ok: boolean; text: string } | null>(null)
let roadmapLoaded = false

const trendMeta: Record<InsightTopic['trend'], { label: string; tone: 'success' | 'warning' | 'neutral' }> = {
  up: { label: '上升', tone: 'warning' },
  flat: { label: '平稳', tone: 'neutral' },
  down: { label: '回落', tone: 'success' },
}

const levelTone: Record<PriorityLevel, 'danger' | 'warning' | 'info' | 'neutral'> = priorityTone

onMounted(() => {
  void insights.fetchDashboard()
  void insights.fetchRoadmap().then(() => {
    if (selected.value) {
      const item = roadmapItems.value.find((r) => r.topic_id === selected.value?.id)
      targetRoadmapId.value = item?.id ?? (roadmapItems.value[0]?.id ?? '')
    }
  })
})

function select(id: string) {
  selectedId.value = id
  createdMsg.value = null
  // 自动匹配与主题关联的路线图项
  const item = roadmapItems.value.find((r) => r.topic_id === id)
  targetRoadmapId.value = item?.id ?? (roadmapItems.value[0]?.id ?? '')
}

async function ensureRoadmap() {
  if (!roadmapLoaded) {
    roadmapLoaded = true
    try {
      await insights.fetchRoadmap()
      if (selected.value) {
        const item = roadmapItems.value.find((r) => r.topic_id === selected.value?.id)
        targetRoadmapId.value = item?.id ?? (roadmapItems.value[0]?.id ?? '')
      }
    } catch {
      roadmapLoaded = false
    }
  }
}

async function createGovTask() {
  const t = selected.value
  if (!t || !targetRoadmapId.value || creating.value) return
  creating.value = true
  createdMsg.value = null
  try {
    await insights.createTask({
      roadmap_id: targetRoadmapId.value,
      title: `专项治理：${t.title}`,
      owner: roadmapItems.value.find((r) => r.id === targetRoadmapId.value)?.owner ?? '运营管理组',
      priority: t.priority_score >= 85 ? 1 : t.priority_score >= 70 ? 2 : 3,
    })
    createdMsg.value = { ok: true, text: `已生成治理任务「专项治理：${t.title}」，可在路线图中跟踪落地。` }
  } catch {
    createdMsg.value = { ok: false, text: '任务生成失败，请稍后重试。' }
  } finally {
    creating.value = false
  }
}

function goRoadmap() {
  void router.push('/roadmap')
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

        <div class="case-sec">
          <h3 class="sec-title">治理案例参考</h3>
          <div v-if="selectedCases.length" class="case-grid">
            <div v-for="c in selectedCases" :key="c.id" class="case-card">
              <div class="case-top">
                <span class="case-name">{{ c.title }}</span>
                <StatusBadge :label="caseStatusMeta[c.status].label" :tone="caseStatusMeta[c.status].tone" />
              </div>
              <p class="case-org">{{ c.org }}</p>
              <p class="case-action">{{ c.action }}</p>
              <p class="case-effect">成效：{{ c.effect }}</p>
            </div>
          </div>
          <p v-else class="empty-text">暂无案例参考</p>
        </div>

        <div class="closer-sec">
          <h3 class="sec-title">治理闭环</h3>
          <p class="closer-desc">将当前主题一键纳入路线图，持续跟踪治理落地，形成「洞察 → 决策 → 治理」闭环。</p>
          <div class="closer-row">
            <select v-model="targetRoadmapId" class="closer-select" :disabled="creating" @focus="ensureRoadmap">
              <option v-for="r in roadmapItems" :key="r.id" :value="r.id">{{ r.title }}</option>
            </select>
            <button type="button" class="btn primary" :disabled="creating || !targetRoadmapId" @click="createGovTask">
              {{ creating ? '生成中…' : '一键生成治理任务' }}
            </button>
            <button v-if="createdMsg?.ok" type="button" class="btn ghost" @click="goRoadmap">前往路线图 →</button>
          </div>
          <p v-if="createdMsg" class="closer-msg" :class="createdMsg.ok ? 'msg-ok' : 'msg-err'">{{ createdMsg.text }}</p>
        </div>
      </div>
      <p v-else class="empty-text">无主题数据</p>
    </section>
  </div>

  <AIFloatingAssistant context="insights" />
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
  max-height: 620px;
  overflow-y: auto;
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
.score-box {
  display: grid;
  grid-template-columns: 132px 1fr;
  align-items: center;
  gap: var(--sf-space-4);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  padding: var(--sf-space-3) var(--sf-space-4);
}
.score-nums {
  display: flex;
  align-items: baseline;
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
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
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
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sf-space-2) var(--sf-space-3);
}
.ev {
  padding: var(--sf-space-2) var(--sf-space-3);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-bg);
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
.case-sec {
  margin-top: var(--sf-space-4);
}
.case-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sf-space-3);
}
.case-card {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  padding: var(--sf-space-3);
  background: var(--sf-surface);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.case-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
}
.case-name {
  font-size: var(--sf-font-13);
  font-weight: 600;
}
.case-org {
  font-size: var(--sf-font-12);
  color: var(--sf-primary);
}
.case-action {
  margin: 0;
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  line-height: 1.5;
}
.case-effect {
  margin: 0;
  font-size: var(--sf-font-12);
  color: var(--sf-success);
}
.closer-sec {
  margin-top: var(--sf-space-5);
  padding-top: var(--sf-space-4);
  border-top: 1px solid var(--sf-border);
}
.closer-desc {
  margin: 0 0 var(--sf-space-3);
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
}
.closer-row {
  display: flex;
  align-items: center;
  gap: var(--sf-space-3);
  flex-wrap: wrap;
}
.closer-select {
  min-width: 240px;
  padding: 7px 10px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text);
  font-size: var(--sf-font-13);
}
.closer-msg {
  margin: var(--sf-space-3) 0 0;
  font-size: var(--sf-font-13);
}
.msg-ok {
  color: var(--sf-success);
}
.msg-err {
  color: var(--sf-danger);
}
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 7px 14px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text);
  font-size: var(--sf-font-13);
  cursor: pointer;
  transition: border-color 0.15s ease, background-color 0.15s ease, color 0.15s ease;
}
.btn:hover {
  border-color: var(--sf-primary-border);
}
.btn.primary {
  background: var(--sf-primary);
  border-color: var(--sf-primary);
  color: #fff;
}
.btn.primary:hover {
  background: var(--sf-primary-light);
  border-color: var(--sf-primary-light);
}
.btn.ghost {
  background: transparent;
  border-color: var(--sf-primary-border);
  color: var(--sf-primary);
}
.btn.ghost:hover {
  background: var(--sf-primary-soft);
}
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.empty-text {
  color: var(--sf-text-faint);
  font-size: var(--sf-font-13);
}
@media (max-width: 1100px) {
  .ins {
    grid-template-columns: 1fr;
  }
  .score-box {
    grid-template-columns: 1fr;
  }
  .score-dims {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .ev-list {
    grid-template-columns: 1fr;
  }
  .case-grid {
    grid-template-columns: 1fr;
  }
}
</style>