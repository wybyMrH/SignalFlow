<script setup lang="ts">
/**
 * 商务洞察：企业合作信息 AI 提炼与市场动向报告。
 * 覆盖规划文档「推销联动」：从反馈语义匹配产品目录 → 企业类型/行业分布识别 →
 * 市场动向信号提炼 → 共性需求归纳 → 可视化汇总报告。线索推进保留人工确认。
 */
import { computed, onMounted, ref } from 'vue'

import SfIcon from '@/components/common/SfIcon.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useAIStore } from '@/stores/ai'
import { formatDateTime } from '@/utils'
import type { BusinessLeadStage, MarketSignalType } from '@/types'

const ai = useAIStore()

const activeTab = ref<'leads' | 'industries' | 'signals' | 'needs'>('leads')

const tabs = [
  { key: 'leads' as const, label: '企业线索', icon: 'target' as const },
  { key: 'industries' as const, label: '行业分布', icon: 'industry' as const },
  { key: 'signals' as const, label: '市场动向', icon: 'trend-up' as const },
  { key: 'needs' as const, label: '共性需求', icon: 'need' as const },
]

const summary = computed(() => ai.businessSummary)
const leads = computed(() => ai.businessLeads)
const industries = computed(() => ai.industryShares)
const signals = computed(() => ai.marketSignals)
const needs = computed(() => ai.commonNeeds)

const stageLabel: Record<BusinessLeadStage, string> = {
  identified: '已识别',
  qualified: '已确认',
  pushed: '已推送销售',
}
const stageTone: Record<BusinessLeadStage, 'info' | 'success' | 'warning'> = {
  identified: 'info',
  qualified: 'warning',
  pushed: 'success',
}
const signalTypeLabel: Record<MarketSignalType, string> = {
  opportunity: '机会',
  gap: '能力缺口',
  risk: '准入风险',
  shift: '需求变化',
}
const signalTypeTone: Record<MarketSignalType, 'success' | 'warning' | 'danger' | 'info'> = {
  opportunity: 'success',
  gap: 'warning',
  risk: 'danger',
  shift: 'info',
}

const valueTone = (v: number) => (v >= 85 ? 'success' : v >= 75 ? 'warning' : 'info') as 'success' | 'warning' | 'info'
const trendLabel = (t: 'up' | 'flat' | 'down') => (t === 'up' ? '上升' : t === 'down' ? '回落' : '平稳')

function pctBarStyle(pct: number) {
  return { width: `${Math.round(pct * 100)}%` }
}
function scoreBarStyle(val: number) {
  return { width: `${Math.round(val)}%` }
}

onMounted(() => {
  void ai.loadBusinessCenter()
})
</script>

<template>
  <div class="biz-center">
    <!-- 顶部报告概览：可视化汇总头部 -->
    <div class="stats-row">
      <template v-if="ai.businessSummaryLoading || !summary">
        <Skeleton v-for="i in 6" :key="i" :rows="2" class="stat-skel" />
      </template>
      <template v-else>
        <div class="stat-card">
          <div class="stat-label">企业合作线索</div>
          <div class="stat-value">{{ summary.total_leads }}</div>
          <div class="stat-hint">来自 {{ summary.total_feedback_count }} 条企业反馈</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">优质线索（已确认）</div>
          <div class="stat-value">{{ summary.qualified_leads }}</div>
          <div class="stat-hint">待跟进 {{ summary.total_leads - summary.qualified_leads }} 条</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">已推送销售</div>
          <div class="stat-value" style="color: var(--sf-success)">{{ summary.pushed_leads }}</div>
          <div class="stat-hint">进入 CRM 商机流程</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">覆盖行业</div>
          <div class="stat-value">{{ summary.industry_count }}</div>
          <div class="stat-hint">{{ summary.customer_count }} 家企业客户</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">市场动向信号</div>
          <div class="stat-value">{{ summary.market_signal_count }}</div>
          <div class="stat-hint">机会 / 缺口 / 风险</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">共性需求归纳</div>
          <div class="stat-value">{{ summary.common_need_count }}</div>
          <div class="stat-hint">映射产品能力候选</div>
        </div>
      </template>
    </div>

    <!-- 报告元信息 -->
    <div v-if="summary" class="report-meta">
      <SfIcon name="file" :size="14" />
      报告周期 {{ summary.report_period }} · 生成于 {{ formatDateTime(summary.generated_at) }} ·
      AI 仅提炼候选，线索推进与对外动作需人工确认
    </div>

    <!-- 标签页 -->
    <div class="tab-bar">
      <button
        v-for="t in tabs"
        :key="t.key"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === t.key }"
        @click="activeTab = t.key"
      >
        <SfIcon :name="t.icon" :size="14" />
        {{ t.label }}
        <span v-if="t.key === 'leads' && leads.length" class="tab-badge">{{ leads.length }}</span>
        <span v-if="t.key === 'signals' && signals.length" class="tab-badge">{{ signals.length }}</span>
      </button>
    </div>

    <!-- 面板 1：企业合作线索 -->
    <div v-if="activeTab === 'leads'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="target" :size="14" />
          企业合作线索识别
        </div>
        <div class="panel-sub">
          从反馈语义匹配产品目录 · 共 {{ leads.length }} 条
        </div>
      </div>

      <Skeleton v-if="ai.leadsLoading" :rows="6" />
      <div v-else class="lead-list">
        <div v-for="lead in leads" :key="lead.id" class="lead-card">
          <div class="lead-top">
            <div class="lead-id">{{ lead.id }}</div>
            <div class="lead-tags">
              <StatusBadge :label="stageLabel[lead.stage]" :tone="stageTone[lead.stage]" />
              <span class="type-chip">{{ lead.company_type }} · {{ lead.size_band }}</span>
            </div>
          </div>

          <div class="lead-name">{{ lead.company_name }}</div>
          <p class="lead-content">{{ lead.content }}</p>

          <div class="lead-match">
            <div class="match-row">
              <span class="match-label">所属行业</span>
              <span class="match-value">{{ lead.industry }}</span>
            </div>
            <div class="match-row">
              <span class="match-label">匹配产品</span>
              <span class="match-value match-product">{{ lead.matched_product }}</span>
            </div>
            <div class="match-row">
              <span class="match-label">匹配理由</span>
              <span class="match-value">{{ lead.match_reason }}</span>
            </div>
          </div>

          <div class="lead-scores">
            <div class="score-item">
              <span class="score-label">客户价值</span>
              <div class="score-track">
                <div class="score-fill" :class="`fill-${valueTone(lead.value_score)}`" :style="scoreBarStyle(lead.value_score)" />
              </div>
              <span class="score-num" :class="`num-${valueTone(lead.value_score)}`">{{ lead.value_score }}</span>
            </div>
            <div class="score-item">
              <span class="score-label">匹配置信度</span>
              <div class="score-track">
                <div class="score-fill" :style="scoreBarStyle(lead.confidence * 100)" />
              </div>
              <span class="score-num">{{ Math.round(lead.confidence * 100) }}%</span>
            </div>
          </div>

          <div class="lead-actions">
            <button
              v-if="lead.stage !== 'pushed'"
              type="button"
              class="btn-primary"
              @click="ai.advanceLeadStage(lead.id)"
            >
              <SfIcon name="chevron-right" :size="12" />
              {{ lead.stage === 'identified' ? '确认线索' : '推送销售' }}
            </button>
            <span v-else class="lead-pushed">
              <SfIcon name="check" :size="12" />
              已推送，等待销售跟进
            </span>
            <span class="lead-hint">AI 建议，不自动外发推销内容</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 面板 2：行业分布 -->
    <div v-if="activeTab === 'industries'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="industry" :size="14" />
          行业分布
        </div>
        <div class="panel-sub">按近 30 天企业反馈统计</div>
      </div>

      <Skeleton v-if="ai.industriesLoading" :rows="6" />
      <div v-else class="industry-list">
        <div v-for="ind in industries" :key="ind.industry" class="industry-row">
          <div class="industry-info">
            <span class="industry-name">{{ ind.industry }}</span>
            <span class="industry-count">{{ ind.count }} 条</span>
            <span class="industry-trend" :class="`trend-${ind.trend}`">
              <SfIcon :name="ind.trend === 'up' ? 'trend-up' : ind.trend === 'down' ? 'trend-down' : 'trend-flat'" :size="12" />
              {{ trendLabel(ind.trend) }}
            </span>
          </div>
          <div class="industry-bar-wrap">
            <div class="industry-track">
              <div class="industry-fill" :style="pctBarStyle(ind.pct)" />
            </div>
            <span class="industry-pct">{{ Math.round(ind.pct * 100) }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 面板 3：市场动向 -->
    <div v-if="activeTab === 'signals'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="trend-up" :size="14" />
          市场动向信号
        </div>
        <div class="panel-sub">AI 从反馈趋势中提炼 · 共 {{ signals.length }} 个信号</div>
      </div>

      <Skeleton v-if="ai.signalsLoading" :rows="6" />
      <div v-else class="signal-list">
        <div v-for="s in signals" :key="s.id" class="signal-card">
          <div class="signal-top">
            <StatusBadge :label="signalTypeLabel[s.type]" :tone="signalTypeTone[s.type]" />
            <span class="signal-id">{{ s.id }}</span>
          </div>
          <div class="signal-title">{{ s.title }}</div>
          <p class="signal-summary">{{ s.summary }}</p>
          <div class="signal-severity">
            <span class="severity-label">影响强度</span>
            <div class="severity-track">
              <div
                class="severity-fill"
                :class="`fill-${s.severity >= 80 ? 'danger' : s.severity >= 65 ? 'warning' : 'info'}`"
                :style="scoreBarStyle(s.severity)"
              />
            </div>
            <span class="severity-num">{{ s.severity }}</span>
          </div>
          <div class="signal-meta">
            <span class="signal-evidence">{{ s.evidence_count }} 条支撑反馈</span>
            <span class="signal-industries">{{ s.related_industries.join(' / ') }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 面板 4：共性需求 -->
    <div v-if="activeTab === 'needs'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="need" :size="14" />
          共性需求归纳
        </div>
        <div class="panel-sub">跨企业共性诉求 → 产品能力候选</div>
      </div>

      <Skeleton v-if="ai.needsLoading" :rows="6" />
      <div v-else class="need-list">
        <div v-for="n in needs" :key="n.id" class="need-card">
          <div class="need-top">
            <div class="need-name">{{ n.title }}</div>
            <StatusBadge
              :label="n.status === 'shipped' ? '已上线' : n.status === 'planned' ? '已规划' : '待评估'"
              :tone="n.status === 'shipped' ? 'success' : n.status === 'planned' ? 'info' : 'neutral'"
            />
          </div>
          <p class="need-desc">{{ n.description }}</p>
          <div class="need-stats">
            <div class="need-stat">
              <span class="need-stat-num">{{ n.feedback_count }}</span>
              <span class="need-stat-label">条反馈</span>
            </div>
            <div class="need-stat">
              <span class="need-stat-num">{{ n.customer_count }}</span>
              <span class="need-stat-label">家企业</span>
            </div>
            <div class="need-stat">
              <span class="need-stat-num">P{{ n.priority }}</span>
              <span class="need-stat-label">优先级</span>
            </div>
          </div>
          <div class="need-industries">
            <span v-for="i in n.industries" :key="i" class="need-chip">{{ i }}</span>
          </div>
          <div class="need-potential">
            <span class="potential-label">产品能力候选</span>
            <span class="potential-value">{{ n.product_potential }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.biz-center {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}

/* 顶部统计卡 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--sf-space-3);
}
.stat-skel {
  height: 84px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  padding: 12px 16px;
}
.stat-card {
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  padding: 12px 16px;
}
.stat-label {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
  margin-bottom: 4px;
}
.stat-value {
  font-size: var(--sf-font-24);
  font-weight: 700;
  color: var(--sf-primary);
  line-height: 1.2;
}
.stat-hint {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  margin-top: 4px;
}

/* 报告元信息 */
.report-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  padding: 8px 12px;
}

/* 标签页 */
.tab-bar {
  display: flex;
  gap: var(--sf-space-1);
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  padding: 4px;
}
.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--sf-radius-sm);
  border: none;
  background: transparent;
  color: var(--sf-text-secondary);
  font-size: var(--sf-font-13);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.tab-btn:hover {
  background: var(--sf-primary-soft);
  color: var(--sf-primary);
}
.tab-btn.active {
  background: var(--sf-primary);
  color: #fff;
}
.tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: var(--sf-warning);
  color: #fff;
  font-size: var(--sf-font-11);
  font-weight: 600;
}

/* 面板通用 */
.panel {
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  padding: var(--sf-space-3) var(--sf-space-4);
}
.panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: var(--sf-space-3);
  flex-wrap: wrap;
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--sf-font-14);
  font-weight: 600;
  color: var(--sf-text);
}
.panel-sub {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}

/* 企业线索 */
.lead-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.lead-card {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  padding: var(--sf-space-3);
  background: var(--sf-bg);
}
.lead-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: var(--sf-space-2);
  flex-wrap: wrap;
}
.lead-id {
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-text-secondary);
}
.lead-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.type-chip {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: var(--sf-font-11);
  background: var(--sf-primary-soft);
  color: var(--sf-primary);
  font-weight: 500;
}
.lead-name {
  font-size: var(--sf-font-15);
  font-weight: 600;
  color: var(--sf-text);
  margin-bottom: 4px;
}
.lead-content {
  margin: 0 0 var(--sf-space-2);
  font-size: var(--sf-font-13);
  line-height: 1.45;
  color: var(--sf-text);
}
.lead-match {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: var(--sf-space-2);
  padding: var(--sf-space-2);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
}
.match-row {
  display: flex;
  gap: 8px;
  font-size: var(--sf-font-12);
  line-height: 1.4;
}
.match-label {
  color: var(--sf-text-faint);
  min-width: 60px;
  flex-shrink: 0;
}
.match-value {
  color: var(--sf-text-secondary);
}
.match-product {
  color: var(--sf-primary);
  font-weight: 500;
}
.lead-scores {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sf-space-3);
  margin-bottom: var(--sf-space-2);
}
.score-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.score-label {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  min-width: 62px;
}
.score-track {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: var(--sf-border);
  overflow: hidden;
}
.score-fill {
  height: 100%;
  border-radius: 3px;
  background: var(--sf-primary);
}
.fill-success { background: var(--sf-success); }
.fill-warning { background: var(--sf-warning); }
.fill-info    { background: var(--sf-info); }
.fill-danger  { background: var(--sf-danger); }
.score-num {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  min-width: 30px;
  text-align: right;
  font-weight: 600;
}
.num-success { color: var(--sf-success); }
.num-warning { color: var(--sf-warning); }
.num-info    { color: var(--sf-info); }
.lead-actions {
  display: flex;
  align-items: center;
  gap: var(--sf-space-2);
  flex-wrap: wrap;
}
.lead-pushed {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--sf-font-12);
  color: var(--sf-success);
  font-weight: 500;
}
.lead-hint {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}

/* 行业分布 */
.industry-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.industry-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.industry-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.industry-name {
  font-size: var(--sf-font-13);
  font-weight: 600;
  color: var(--sf-text);
  min-width: 90px;
}
.industry-count {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
}
.industry-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--sf-font-11);
}
.trend-up { color: var(--sf-success); }
.trend-down { color: var(--sf-danger); }
.trend-flat { color: var(--sf-text-faint); }
.industry-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.industry-track {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: var(--sf-border);
  overflow: hidden;
}
.industry-fill {
  height: 100%;
  border-radius: 4px;
  background: var(--sf-primary);
}
.industry-pct {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  min-width: 40px;
  text-align: right;
}

/* 市场动向 */
.signal-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sf-space-3);
}
.signal-card {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  padding: var(--sf-space-3);
  background: var(--sf-bg);
}
.signal-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: 6px;
}
.signal-id {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  font-weight: 600;
}
.signal-title {
  font-size: var(--sf-font-14);
  font-weight: 600;
  color: var(--sf-text);
  margin-bottom: 6px;
}
.signal-summary {
  margin: 0 0 var(--sf-space-2);
  font-size: var(--sf-font-12);
  line-height: 1.5;
  color: var(--sf-text-secondary);
}
.signal-severity {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: var(--sf-space-2);
}
.severity-label {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  min-width: 62px;
}
.severity-track {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: var(--sf-border);
  overflow: hidden;
}
.severity-fill {
  height: 100%;
  border-radius: 3px;
}
.severity-num {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  min-width: 30px;
  text-align: right;
  font-weight: 600;
}
.signal-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  flex-wrap: wrap;
}
.signal-evidence {
  font-size: var(--sf-font-11);
  color: var(--sf-warning);
  font-weight: 500;
}
.signal-industries {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
}

/* 共性需求 */
.need-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sf-space-3);
}
.need-card {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  padding: var(--sf-space-3);
  background: var(--sf-bg);
}
.need-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: 6px;
}
.need-name {
  font-size: var(--sf-font-14);
  font-weight: 600;
  color: var(--sf-text);
}
.need-desc {
  margin: 0 0 var(--sf-space-2);
  font-size: var(--sf-font-12);
  line-height: 1.5;
  color: var(--sf-text-secondary);
}
.need-stats {
  display: flex;
  gap: var(--sf-space-3);
  margin-bottom: var(--sf-space-2);
}
.need-stat {
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 4px 8px;
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
}
.need-stat-num {
  font-size: var(--sf-font-15);
  font-weight: 700;
  color: var(--sf-primary);
}
.need-stat-label {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
}
.need-industries {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: var(--sf-space-2);
}
.need-chip {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: var(--sf-font-11);
  background: var(--sf-primary-soft);
  color: var(--sf-primary);
}
.need-potential {
  display: flex;
  gap: 8px;
  font-size: var(--sf-font-12);
  line-height: 1.4;
}
.potential-label {
  color: var(--sf-text-faint);
  min-width: 90px;
  flex-shrink: 0;
}
.potential-value {
  color: var(--sf-success);
  font-weight: 500;
}

/* 按钮 */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: var(--sf-radius-sm);
  border: none;
  background: var(--sf-primary);
  color: #fff;
  font-size: var(--sf-font-12);
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn-primary:hover {
  opacity: 0.9;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .signal-list,
  .need-list {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .stats-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .lead-scores {
    grid-template-columns: 1fr;
  }
}
</style>