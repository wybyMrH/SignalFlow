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
import { computed, onMounted, ref } from 'vue'
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
import { fetchGovOverview } from '@/api/gov'
import { fetchResourceHealth } from '@/api/interviews'
import { useAgentsStore } from '@/stores/agents'
import { useAIStore } from '@/stores/ai'
import { useFeedbackStore } from '@/stores/feedback'
import { useInsightsStore } from '@/stores/insights'
import { useWorkflowsStore } from '@/stores/workflows'
import { formatDateTime } from '@/utils'
import { sourceLabels } from '@/utils/labels'
import type { GovOverview, ResourceHealth } from '@/types'

const router = useRouter()
const insights = useInsightsStore()
const feedback = useFeedbackStore()
const ai = useAIStore()
const agents = useAgentsStore()
const workflows = useWorkflowsStore()

const metrics = computed(() => insights.metrics)
const topTopics = computed(() => insights.dashboard?.items.slice(0, 5) ?? [])

/** 运营驾驶舱：跨模块状态数据 */
const govOverview = ref<GovOverview | null>(null)
const resource = ref<ResourceHealth | null>(null)
const followUpLeads = computed(() => ai.businessLeads.filter((l) => l.stage !== 'pushed').length)
const pendingGovAlerts = computed(() => govOverview.value?.alerts.filter((a) => !a.dispatched).length ?? 0)
const highAlerts = computed(() => govOverview.value?.alerts.filter((a) => a.level === 'orange' || a.level === 'red').length ?? 0)
const enabledRules = computed(() => ai.rules.filter((r) => r.enabled).length)
/** 工作流总开关：是否全部启用（映射到工作流配置页真实状态） */
const allWorkflowsOn = computed(() => workflows.details.length > 0 && workflows.enabled.length === workflows.details.length)

function toggleAllWorkflows() {
  workflows.toggleAll(!allWorkflowsOn.value)
}

onMounted(() => {
  void insights.fetchMetrics()
  void insights.fetchDashboard()
  void feedback.fetchPending(6)
  void ai.fetchRules()
  void ai.fetchBusinessLeadsList()
  void ai.fetchAutomationSummaryData()
  void agents.fetchAll()
  void workflows.fetchAll()
  void fetchGovOverview().then((d) => (govOverview.value = d))
  void fetchResourceHealth().then((d) => (resource.value = d))
})

function goFeedback(status?: string) {
  void router.push({ path: '/feedback', query: status ? { status } : {} })
}

function goInsights() {
  void router.push('/insights')
}

function go(path: string) {
  void router.push(path)
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
          <TrendChart v-if="metrics" :points="metrics.trend" :height="120" />
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

    <!-- 运营驾驶舱：跨模块状态速览与配置入口 -->
    <section class="ops-grid">
      <article class="ops-card">
        <div class="ops-head">
          <span class="ops-title"><SfIcon name="automation" :size="14" /> 自动化任务</span>
          <button type="button" class="ops-link" @click="go('/automation')">管理 <SfIcon name="chevron-right" :size="12" /></button>
        </div>
        <div class="ops-main">{{ ai.automationSummary?.classified_count ?? '—' }}</div>
        <div class="ops-label">今日自动分类</div>
        <div class="ops-meta">
          <span>待审核 {{ ai.automationSummary?.review_queue_count ?? '—' }}</span>
          <span>自动升级 {{ ai.automationSummary?.auto_escalated_count ?? '—' }}</span>
          <span>运行中 {{ ai.runningWorkflows.length }}</span>
        </div>
      </article>

      <article class="ops-card">
        <div class="ops-head">
          <span class="ops-title"><SfIcon name="briefcase" :size="14" /> 商务线索</span>
          <button type="button" class="ops-link" @click="go('/business')">商务洞察 <SfIcon name="chevron-right" :size="12" /></button>
        </div>
        <div class="ops-main">{{ followUpLeads }}</div>
        <div class="ops-label">线索待跟进（未推送）</div>
        <div class="ops-meta">
          <span>总线索 {{ ai.businessSummary?.total_leads ?? ai.businessLeads.length }}</span>
          <span>已推送 {{ ai.businessSummary?.pushed_leads ?? '—' }}</span>
          <span>共性需求 {{ ai.businessSummary?.common_need_count ?? '—' }}</span>
        </div>
      </article>

      <article class="ops-card">
        <div class="ops-head">
          <span class="ops-title"><SfIcon name="gov" :size="14" /> 政务预警</span>
          <button type="button" class="ops-link" @click="go('/gov')">政务适配 <SfIcon name="chevron-right" :size="12" /></button>
        </div>
        <div class="ops-main" :style="pendingGovAlerts > 0 ? { color: 'var(--sf-warning)' } : {}">{{ pendingGovAlerts }}</div>
        <div class="ops-label">预警待派发</div>
        <div class="ops-meta">
          <span>待办诉求 {{ govOverview?.summary.pending_count ?? '—' }}</span>
          <span>超期 {{ govOverview?.summary.overdue_count ?? '—' }}</span>
          <span>橙红预警 {{ highAlerts }}</span>
        </div>
      </article>

      <article class="ops-card">
        <div class="ops-head">
          <span class="ops-title"><SfIcon name="agent" :size="14" /> Agent 与工作流</span>
          <span class="ops-links">
            <button type="button" class="ops-link" @click="go('/agents')">Agent <SfIcon name="chevron-right" :size="12" /></button>
            <button type="button" class="ops-link" @click="go('/workflows')">工作流 <SfIcon name="chevron-right" :size="12" /></button>
          </span>
        </div>
        <div class="ops-main">{{ agents.enabledAgents.length }}<span class="ops-unit">/{{ agents.agents.length }}</span></div>
        <div class="ops-label">已启用 Agent</div>
        <div class="ops-meta">
          <span>已启用工作流 {{ workflows.enabled.length }}/{{ workflows.details.length }}</span>
          <span>运行中 {{ workflows.running.length }}</span>
          <span>启用规则 {{ enabledRules }}</span>
        </div>
        <div class="ops-foot">
          <span class="ops-hint">
            <SfIcon name="workflow" :size="12" /> 工作流总开关
            <span class="ops-hint-sub">{{ allWorkflowsOn ? '全部启用' : '部分/未启用' }}</span>
          </span>
          <button
            type="button"
            class="switch"
            :class="{ on: workflows.enabled.length > 0 }"
            :title="allWorkflowsOn ? '停用全部工作流（映射到工作流配置页）' : '启用全部工作流（映射到工作流配置页）'"
            @click="toggleAllWorkflows"
          >
            <span class="knob" />
          </button>
        </div>
      </article>

      <article class="ops-card">
        <div class="ops-head">
          <span class="ops-title"><SfIcon name="server" :size="14" /> 资源健康</span>
          <button type="button" class="ops-link" @click="go('/resources')">资源管理 <SfIcon name="chevron-right" :size="12" /></button>
        </div>
        <div class="ops-main">{{ resource ? `${resource.server_healthy}/${resource.server_count}` : '—' }}</div>
        <div class="ops-label">服务节点健康</div>
        <div class="ops-meta">
          <span>数据库 {{ resource ? (resource.db_status === 'healthy' ? '正常' : resource.db_status === 'degraded' ? '降级' : resource.db_status === 'down' ? '异常' : resource.db_status) : '—' }}</span>
          <span>API {{ resource ? `${resource.api_healthy}/${resource.api_total}` : '—' }}</span>
          <span v-if="resource?.alert_count">告警 {{ resource.alert_count }}</span>
          <span v-else>无告警</span>
        </div>
      </article>
    </section>

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
}
.data-area {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
  min-height: 0;
  max-height: calc(100vh - var(--sf-header-h) - 136px);
}
.ai-area {
  min-height: 0;
  height: calc(100vh - var(--sf-header-h) - 136px);
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

/* 双栏：撑满左列剩余高度，内容超出时卡片内部滚动 */
.duo {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sf-space-3);
  min-height: 0;
  flex: 1;
  min-height: 220px;
}
.duo .card {
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.duo .mini-list,
.duo .signal-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 2px;
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

/* 运营驾驶舱：跨模块状态卡 */
.ops-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--sf-space-3);
}
.ops-card {
  display: flex;
  flex-direction: column;
  gap: 3px;
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  box-shadow: var(--sf-shadow);
  padding: var(--sf-space-3) var(--sf-space-4);
  min-width: 0;
}
.ops-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: 6px;
}
.ops-title {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-text-secondary);
  white-space: nowrap;
  overflow: hidden;
}
.ops-title :deep(svg) {
  color: var(--sf-primary);
  flex-shrink: 0;
}
.ops-link {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  border: none;
  background: none;
  color: var(--sf-primary);
  font-size: var(--sf-font-12);
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
}
.ops-link:hover {
  text-decoration: underline;
}
.ops-links {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.ops-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 4px;
}
.ops-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--sf-font-11);
  color: var(--sf-text-secondary);
  min-width: 0;
}
.ops-hint-sub {
  color: var(--sf-text-faint);
}

/* 开关 */
.switch {
  position: relative;
  width: 38px;
  height: 22px;
  border: none;
  border-radius: 11px;
  background: var(--sf-border);
  cursor: pointer;
  transition: background 0.18s ease;
  flex-shrink: 0;
}
.switch.on {
  background: var(--sf-primary);
}
.switch .knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  transition: left 0.18s ease;
  box-shadow: 0 1px 3px rgba(2, 6, 23, 0.25);
}
.switch.on .knob {
  left: 18px;
}
.ops-main {
  font-size: 24px;
  font-weight: 700;
  color: var(--sf-text);
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}
.ops-unit {
  font-size: var(--sf-font-13);
  font-weight: 500;
  color: var(--sf-text-faint);
}
.ops-label {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.ops-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 3px 10px;
  margin-top: 6px;
  border-top: 1px dashed var(--sf-border);
  padding-top: 6px;
  font-size: var(--sf-font-11);
  color: var(--sf-text-secondary);
  line-height: 1.4;
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
  .ops-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 640px) {
  .kpi-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .ops-grid {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
}
</style>
