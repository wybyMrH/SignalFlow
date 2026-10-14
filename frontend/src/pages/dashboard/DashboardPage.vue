<script setup lang="ts">
/**
 * AI 总览面板（重构版）：打破传统管理面板布局，引入 AI 原生设计。
 * 
 * 布局编排：
 * 1. 顶部 = 紧凑 KPI 指标条（保持数据锚点）
 * 2. 主体 = 左数据区（趋势图 + 双栏列表）+ 右 AI 助手面板（常驻对话栏）
 * 3. 底部 = AI 工作流状态 + 自动化规则配置
 * 
 * AI 能力：
 * - 侧边常驻 AI 对话栏：自然语言查询 → mock 工作流 → 数据总结/知识库回复
 * - 工作流状态面板：实时展示 AI 处理中任务与进度
 * - 自动化扩展区：面向政企场景的预设规则开关与统计
 */
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import AIAutomationRules from '@/components/ai/AIAutomationRules.vue'
import AIChatPanel from '@/components/ai/AIChatPanel.vue'
import AIWorkflowStatus from '@/components/ai/AIWorkflowStatus.vue'
import BarRow from '@/components/common/BarRow.vue'
import SfIcon from '@/components/common/SfIcon.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TrendChart from '@/components/common/TrendChart.vue'
import { useFeedbackStore } from '@/stores/feedback'
import { useInsightsStore } from '@/stores/insights'
import { formatDateTime } from '@/utils'
import { sourceLabels } from '@/utils/labels'

const router = useRouter()
const insights = useInsightsStore()
const feedback = useFeedbackStore()

const metrics = computed(() => insights.metrics)
const topTopics = computed(() => insights.dashboard?.items.slice(0, 5) ?? [])

onMounted(() => {
  void insights.fetchMetrics()
  void insights.fetchDashboard()
  void feedback.fetchPending(6)
})

function goFeedback(status?: string) {
  void router.push({ path: '/feedback', query: status ? { status } : {} })
}

function goInsights() {
  void router.push('/insights')
}

const priorTone = (score: number) => (score >= 85 ? 'danger' : score >= 70 ? 'warning' : score >= 55 ? 'info' : 'neutral') as 'danger' | 'warning' | 'info' | 'neutral'
</script>

<template>
  <div class="dash">
    <!-- 顶部：紧凑 KPI 指标条 -->
    <div class="kpi-row">
      <template v-if="insights.metricsLoading || !metrics">
        <Skeleton v-for="i in 6" :key="i" :rows="2" class="kpi-skel" />
      </template>
      <template v-else>
        <StatCard label="反馈总量" :value="metrics.total_feedbacks" hint="近 14 天累计" />
        <StatCard label="待处理" :value="metrics.pending" :delta="`高优 ${metrics.high_priority}`" delta-tone="warning" />
        <StatCard label="高优先级" :value="metrics.high_priority" hint="待处理中 P4+" />
        <StatCard label="今日解决" :value="metrics.resolved_today" delta-tone="up" hint="已解决+回复" />
        <StatCard label="平均时长" :value="metrics.avg_resolve_hours" unit="h" hint="解决中位数" />
        <StatCard label="去重主题" :value="metrics.deduped_topics" hint="洞察聚类" />
      </template>
    </div>

    <!-- 主体：左数据区 + 右 AI 助手 -->
    <div class="main-grid">
      <div class="data-area">
        <!-- 趋势图 -->
        <section class="card trend-card">
          <div class="card-head">
            <h2 class="card-title">信号趋势</h2>
            <span class="card-sub">{{ metrics ? `更新 ${formatDateTime(metrics.updated_at)}` : '' }}</span>
          </div>
          <TrendChart v-if="metrics" :points="metrics.trend" :height="150" />
          <Skeleton v-else :rows="3" />
        </section>

        <!-- 双栏：待处理反馈 + 优先级信号榜 -->
        <div class="duo">
          <section class="card">
            <div class="card-head">
              <h2 class="card-title">待处理反馈</h2>
              <button type="button" class="link-btn" @click="goFeedback('new')">
                全部 <SfIcon name="chevron-right" :size="14" />
              </button>
            </div>
            <Skeleton v-if="feedback.pendingLoading" :rows="5" />
            <ul v-else class="mini-list">
              <li v-for="item in feedback.pendingItems" :key="item.id" class="mini-item" @click="goFeedback('new')">
                <div class="mini-top">
                  <span class="mini-title">{{ item.id }}</span>
                  <StatusBadge :label="sourceLabels[item.source as keyof typeof sourceLabels] ?? item.source" tone="neutral" />
                </div>
                <p class="mini-text">{{ item.content }}</p>
              </li>
            </ul>
          </section>

          <section class="card">
            <div class="card-head">
              <h2 class="card-title">优先级信号榜</h2>
              <button type="button" class="link-btn" @click="goInsights">
                洞察 <SfIcon name="chevron-right" :size="14" />
              </button>
            </div>
            <Skeleton v-if="insights.dashboardLoading" :rows="5" />
            <div v-else class="signal-list">
              <div v-for="t in topTopics" :key="t.id" class="signal-item" role="button" tabindex="0" @click="goInsights" @keydown.enter="goInsights">
                <div class="signal-top">
                  <span class="signal-title">{{ t.title }}</span>
                  <StatusBadge :label="String(t.priority_score)" :tone="priorTone(t.priority_score)" />
                </div>
                <BarRow :label="t.short" :value="t.strength" :pct="t.strength" :tone="priorTone(t.priority_score)" />
                <span class="signal-meta">{{ t.feedback_count }} 条反馈 · 强度 {{ t.strength }}</span>
              </div>
            </div>
          </section>
        </div>
      </div>

      <!-- 右 AI 助手面板（常驻） -->
      <div class="ai-area">
        <AIChatPanel />
      </div>
    </div>

    <!-- 底部：AI 工作流状态 -->
    <AIWorkflowStatus />

    <!-- 底部：AI 自动化扩展 -->
    <AIAutomationRules />
  </div>
</template>

<style scoped>
.dash {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}

/* KPI 指标条 */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--sf-space-3);
}
.kpi-skel {
  height: 84px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  padding: 12px 16px;
}

/* 主体网格：左数据 + 右 AI */
.main-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: var(--sf-space-3);
  min-height: 0;
  align-items: start;
}
.data-area {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
  min-height: 0;
}
.ai-area {
  min-height: 0;
  height: 100%;
  max-height: calc(100vh - var(--sf-header-h) - 140px);
  position: sticky;
  top: var(--sf-space-3);
}
.ai-area > * {
  height: 100%;
}

/* 卡片通用 */
.card {
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  box-shadow: var(--sf-shadow);
  padding: var(--sf-space-3) var(--sf-space-4);
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--sf-space-2);
}
.card-title {
  margin: 0;
  font-size: var(--sf-font-14);
  font-weight: 600;
}
.card-sub {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.link-btn {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  border: none;
  background: none;
  color: var(--sf-primary);
  font-size: var(--sf-font-12);
  cursor: pointer;
  padding: 2px 4px;
}
.link-btn:hover {
  text-decoration: underline;
}

/* 双栏 */
.duo {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sf-space-3);
  min-height: 0;
}
.mini-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.mini-item {
  padding: var(--sf-space-2) 0;
  border-bottom: 1px solid var(--sf-border);
  cursor: pointer;
}
.mini-item:last-child {
  border-bottom: none;
}
.mini-item:hover {
  background: var(--sf-primary-soft);
}
.mini-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
}
.mini-title {
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-text-secondary);
}
.mini-text {
  margin: 3px 0 0;
  font-size: var(--sf-font-13);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.signal-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
}
.signal-item {
  padding: var(--sf-space-2) var(--sf-space-1);
  border-bottom: 1px solid var(--sf-border);
  cursor: pointer;
}
.signal-item:last-child {
  border-bottom: none;
}
.signal-item:hover {
  background: var(--sf-primary-soft);
}
.signal-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: 4px;
}
.signal-title {
  font-size: var(--sf-font-13);
  font-weight: 600;
}
.signal-meta {
  display: block;
  margin-top: 3px;
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}

/* 响应式 */
@media (max-width: 1200px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
  .ai-area {
    position: static;
    max-height: 520px;
  }
  .kpi-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .duo {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .kpi-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
