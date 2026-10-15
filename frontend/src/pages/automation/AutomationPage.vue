<script setup lang="ts">
/**
 * AI 自动化中心：自动分类、去重合并、优先级规则配置与执行面板。
 * 理念：把 AI 预处理结果透明展示给人，保留人工确认与干预的主动权。
 */
import { computed, onMounted, ref } from 'vue'

import SfIcon from '@/components/common/SfIcon.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useAIStore } from '@/stores/ai'
import { formatDateTime } from '@/utils'

const ai = useAIStore()

const activeTab = ref<'classification' | 'dedup' | 'priority'>('classification')

const tabs = [
  { key: 'classification' as const, label: '自动分类', icon: 'label' as const },
  { key: 'dedup' as const, label: '去重合并', icon: 'filter' as const },
  { key: 'priority' as const, label: '优先级规则', icon: 'alert' as const },
]

const summary = computed(() => ai.automationSummary)
const classified = computed(() => ai.classificationResults)
const dedupGroups = computed(() => ai.dedupGroups)
const priorityRules = computed(() => ai.priorityRules)
const adjustments = computed(() => ai.priorityAdjustments)

const reviewQueue = computed(() => classified.value.filter((r) => r.needs_review))
const pendingGroups = computed(() => dedupGroups.value.filter((g) => g.status === 'pending'))
const mergedGroups = computed(() => dedupGroups.value.filter((g) => g.status === 'merged'))

const confidenceTone = (c: number) => (c >= 0.9 ? 'success' : c >= 0.75 ? 'info' : c >= 0.6 ? 'warning' : 'danger') as 'success' | 'info' | 'warning' | 'danger'
const confidenceLabel = (c: number) => (c >= 0.9 ? '高' : c >= 0.75 ? '中' : c >= 0.6 ? '低' : '需确认')

const priorityToneFromNum = (p: number) => (p >= 5 ? 'danger' : p >= 4 ? 'warning' : p >= 3 ? 'info' : 'neutral') as 'danger' | 'warning' | 'info' | 'neutral'

function pctBarStyle(pct: number) {
  return { width: `${Math.round(pct * 100)}%` }
}

function factorBarStyle(val: number, max: number) {
  return { width: `${Math.round((val / max) * 100)}%` }
}

onMounted(() => {
  void ai.loadAutomationCenter()
})
</script>

<template>
  <div class="auto-center">
    <!-- 顶部执行概览 -->
    <div class="stats-row">
      <template v-if="ai.summaryLoading || !summary">
        <Skeleton v-for="i in 6" :key="i" :rows="2" class="stat-skel" />
      </template>
      <template v-else>
        <div class="stat-card">
          <div class="stat-label">今日自动分类</div>
          <div class="stat-value">{{ summary.classified_count }}</div>
          <div class="stat-hint">平均置信度 {{ Math.round(summary.avg_confidence * 100) }}%</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">人工确认队列</div>
          <div class="stat-value" :class="{ warn: summary.review_queue_count > 0 }">{{ summary.review_queue_count }}</div>
          <div class="stat-hint">待审率 {{ Math.round(summary.manual_review_rate * 100) }}%</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">去重组数</div>
          <div class="stat-value">{{ summary.deduped_group_count }}</div>
          <div class="stat-hint">节省 {{ summary.saved_feedback_count }} 条重复</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">优先级调整</div>
          <div class="stat-value">{{ summary.priority_adjusted_count }}</div>
          <div class="stat-hint">含自动升级 {{ summary.auto_escalated_count }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">规则命中总数</div>
          <div class="stat-value">{{ summary.priority_adjusted_count + summary.auto_escalated_count + summary.deduped_group_count }}</div>
          <div class="stat-hint">{{ ai.enabledPriorityRules.length }} 条规则运行中</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">处理日期</div>
          <div class="stat-value" style="font-size: var(--sf-font-16)">{{ summary.date.slice(5) }}</div>
          <div class="stat-hint">{{ summary.date }}</div>
        </div>
      </template>
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
        <span v-if="t.key === 'classification' && reviewQueue.length" class="tab-badge">{{ reviewQueue.length }}</span>
        <span v-if="t.key === 'dedup' && pendingGroups.length" class="tab-badge">{{ pendingGroups.length }}</span>
      </button>
    </div>

    <!-- 面板 1：自动分类 -->
    <div v-if="activeTab === 'classification'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="label" :size="14" />
          自动分类结果
        </div>
        <div class="panel-sub">
          共 {{ classified.length }} 条 · 需人工确认 <strong>{{ reviewQueue.length }}</strong> 条
        </div>
      </div>

      <Skeleton v-if="ai.classificationLoading" :rows="6" />
      <div v-else class="class-list">
        <div
          v-for="item in classified"
          :key="item.feedback_id"
          class="class-card"
          :class="{ 'class-review': item.needs_review }"
        >
          <div class="class-top">
            <div class="class-id">{{ item.feedback_id }}</div>
            <div class="class-tags">
              <StatusBadge :label="item.suggested_topic" tone="info" />
              <StatusBadge :label="confidenceLabel(item.confidence)" :tone="confidenceTone(item.confidence)" />
              <span v-if="item.needs_review" class="review-tag">待确认</span>
            </div>
          </div>
          <p class="class-content">{{ item.content }}</p>
          <div class="class-confidence">
            <span class="conf-label">置信度</span>
            <div class="conf-track">
              <div class="conf-fill" :class="`fill-${confidenceTone(item.confidence)}`" :style="pctBarStyle(item.confidence)" />
            </div>
            <span class="conf-num">{{ Math.round(item.confidence * 100) }}%</span>
          </div>
          <div v-if="item.alternatives.length" class="class-alts">
            <span class="alt-label">候选类别：</span>
            <span v-for="alt in item.alternatives" :key="alt.topic" class="alt-chip">
              {{ alt.topic }} {{ Math.round(alt.confidence * 100) }}%
            </span>
          </div>
          <div v-if="item.reviewer_note" class="class-note">
            <SfIcon name="alert" :size="12" />
            {{ item.reviewer_note }}
          </div>
          <div v-if="item.needs_review" class="class-actions">
            <button type="button" class="btn-primary" @click="ai.confirmClassification(item.feedback_id)">
              <SfIcon name="check" :size="12" />
              确认分类
            </button>
            <span class="class-hint">低置信度或歧义主题，建议人工复核</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 面板 2：去重合并 -->
    <div v-if="activeTab === 'dedup'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="filter" :size="14" />
          相似反馈去重
        </div>
        <div class="panel-sub">
          共 {{ dedupGroups.length }} 组 · 待处理 <strong>{{ pendingGroups.length }}</strong> 组 · 已合并 <strong>{{ mergedGroups.length }}</strong> 组
        </div>
      </div>

      <Skeleton v-if="ai.dedupLoading" :rows="6" />
      <div v-else class="dedup-list">
        <div
          v-for="g in dedupGroups"
          :key="g.group_id"
          class="dedup-card"
          :class="{ 'dedup-pending': g.status === 'pending' }"
        >
          <div class="dedup-top">
            <div class="dedup-id">{{ g.group_id }}</div>
            <div class="dedup-tags">
              <StatusBadge :label="g.merged_topic" tone="info" />
              <StatusBadge
                :label="g.status === 'merged' ? '已合并' : g.status === 'dismissed' ? '已忽略' : '待处理'"
                :tone="g.status === 'merged' ? 'success' : g.status === 'dismissed' ? 'neutral' : 'warning'"
              />
              <span class="repeat-badge">重复 {{ g.repeat_count }} 次</span>
            </div>
          </div>

          <div class="dedup-members">
            <div v-for="(m, idx) in g.members" :key="m.feedback_id" class="member-row">
              <span class="member-idx">{{ idx + 1 }}</span>
              <span class="member-id">{{ m.feedback_id }}</span>
              <div class="member-sim">
                <div class="sim-track">
                  <div class="sim-fill" :style="pctBarStyle(m.similarity)" />
                </div>
                <span class="sim-num">{{ Math.round(m.similarity * 100) }}%</span>
              </div>
              <p class="member-text">{{ m.content }}</p>
            </div>
          </div>

          <div v-if="g.status === 'pending'" class="dedup-actions">
            <button type="button" class="btn-primary" @click="ai.resolveDedupGroup(g.group_id, 'merge')">
              <SfIcon name="check" :size="12" />
              合并为一条
            </button>
            <button type="button" class="btn-ghost" @click="ai.resolveDedupGroup(g.group_id, 'dismiss')">
              <SfIcon name="close" :size="12" />
              忽略
            </button>
            <span class="class-hint">AI 建议合并为「{{ g.merged_topic }}」主题</span>
          </div>
          <div v-else-if="g.status === 'merged' && g.merged_at" class="dedup-meta">
            已于 {{ formatDateTime(g.merged_at) }} 合并
          </div>
        </div>
      </div>
    </div>

    <!-- 面板 3：优先级规则 -->
    <div v-if="activeTab === 'priority'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="alert" :size="14" />
          优先级规则配置（RICE 模型）
        </div>
        <div class="panel-sub">
          {{ ai.enabledPriorityRules.length }}/{{ priorityRules.length }} 条规则已启用
        </div>
      </div>

      <Skeleton v-if="ai.priorityRulesLoading" :rows="6" />
      <div v-else class="prio-list">
        <div
          v-for="rule in priorityRules"
          :key="rule.id"
          class="prio-card"
          :class="{ 'prio-off': !rule.enabled }"
        >
          <div class="prio-top">
            <div class="prio-name">{{ rule.name }}</div>
            <label class="auto-toggle">
              <input
                type="checkbox"
                :checked="rule.enabled"
                @change="ai.togglePriorityRule(rule.id)"
              />
              <span class="auto-toggle-track">
                <span class="auto-toggle-knob" />
              </span>
            </label>
          </div>
          <p class="prio-desc">{{ rule.description }}</p>

          <div class="prio-factors">
            <div v-for="f in rule.factors" :key="f.key" class="factor-row">
              <div class="factor-info">
                <span class="factor-label">{{ f.label }}</span>
                <span class="factor-weight">权重 {{ Math.round(f.weight * 100) }}%</span>
              </div>
              <div class="factor-bar-wrap">
                <div class="factor-track">
                  <div class="factor-fill" :style="factorBarStyle(f.value, f.max)" />
                </div>
                <span class="factor-num">{{ f.value }}/{{ f.max }}</span>
              </div>
              <span class="factor-note">{{ f.note }}</span>
            </div>
          </div>

          <div class="prio-foot">
            <span class="prio-threshold">触发阈值 {{ rule.threshold }} 分</span>
            <StatusBadge
              :label="rule.auto_escalate ? '自动升级' : '仅标记'"
              :tone="rule.auto_escalate ? 'warning' : 'neutral'"
            />
          </div>
        </div>
      </div>

      <!-- 调整记录 -->
      <div class="adj-section">
        <div class="panel-head">
          <div class="panel-title">
            <SfIcon name="refresh" :size="14" />
            优先级调整记录
          </div>
          <div class="panel-sub">最近 {{ adjustments.length }} 条</div>
        </div>
        <Skeleton v-if="ai.adjustmentsLoading" :rows="4" />
        <div v-else class="adj-list">
          <div v-for="a in adjustments" :key="a.feedback_id + a.adjusted_at" class="adj-row">
            <div class="adj-left">
              <span class="adj-id">{{ a.feedback_id }}</span>
              <span class="adj-arrow">→</span>
              <StatusBadge :label="`P${a.old_priority}`" tone="neutral" />
              <SfIcon name="chevron-right" :size="12" />
              <StatusBadge :label="`P${a.new_priority}`" :tone="priorityToneFromNum(a.new_priority)" />
            </div>
            <p class="adj-reason">{{ a.reason }}</p>
            <span class="adj-meta">规则 {{ a.triggered_by }} · {{ formatDateTime(a.adjusted_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auto-center {
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
.stat-value.warn {
  color: var(--sf-warning);
}
.stat-hint {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  margin-top: 4px;
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

/* 自动分类列表 */
.class-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.class-card {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  padding: var(--sf-space-3);
  background: var(--sf-bg);
}
.class-review {
  border-color: var(--sf-warning-border);
  background: var(--sf-warning-soft);
}
.class-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: var(--sf-space-2);
  flex-wrap: wrap;
}
.class-id {
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-text-secondary);
}
.class-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.review-tag {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: var(--sf-font-11);
  background: var(--sf-warning);
  color: #fff;
  font-weight: 500;
}
.class-content {
  margin: 0 0 var(--sf-space-2);
  font-size: var(--sf-font-13);
  line-height: 1.45;
  color: var(--sf-text);
}
.class-confidence {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: var(--sf-space-2);
}
.conf-label {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  min-width: 40px;
}
.conf-track {
  flex: 1;
  height: 5px;
  border-radius: 3px;
  background: var(--sf-border);
  overflow: hidden;
}
.conf-fill {
  height: 100%;
  border-radius: 3px;
}
.fill-success { background: var(--sf-success); }
.fill-info    { background: var(--sf-info); }
.fill-warning { background: var(--sf-warning); }
.fill-danger  { background: var(--sf-danger); }
.conf-num {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  min-width: 36px;
  text-align: right;
}
.class-alts {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: var(--sf-space-2);
}
.alt-label {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.alt-chip {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: var(--sf-font-11);
  background: var(--sf-primary-soft);
  color: var(--sf-primary);
}
.class-note {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: var(--sf-font-12);
  color: var(--sf-warning);
  margin-bottom: var(--sf-space-2);
}
.class-actions {
  display: flex;
  align-items: center;
  gap: var(--sf-space-2);
  flex-wrap: wrap;
}
.class-hint {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}

/* 去重合并 */
.dedup-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.dedup-card {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  padding: var(--sf-space-3);
  background: var(--sf-bg);
}
.dedup-pending {
  border-color: var(--sf-warning-border);
}
.dedup-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: var(--sf-space-2);
  flex-wrap: wrap;
}
.dedup-id {
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-text-secondary);
}
.dedup-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.repeat-badge {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: var(--sf-font-11);
  background: var(--sf-info-soft);
  color: var(--sf-info);
  font-weight: 500;
}
.dedup-members {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
  margin-bottom: var(--sf-space-2);
}
.member-row {
  display: grid;
  grid-template-columns: 24px 80px 140px 1fr;
  gap: 8px;
  align-items: center;
  padding: var(--sf-space-2);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
}
.member-idx {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  text-align: center;
}
.member-id {
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-text-secondary);
}
.member-sim {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sim-track {
  flex: 1;
  height: 5px;
  border-radius: 3px;
  background: var(--sf-border);
  overflow: hidden;
}
.sim-fill {
  height: 100%;
  border-radius: 3px;
  background: var(--sf-primary);
}
.sim-num {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  min-width: 36px;
  text-align: right;
}
.member-text {
  margin: 0;
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.dedup-actions {
  display: flex;
  align-items: center;
  gap: var(--sf-space-2);
  flex-wrap: wrap;
}
.dedup-meta {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}

/* 优先级规则 */
.prio-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.prio-card {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  padding: var(--sf-space-3);
  background: var(--sf-bg);
}
.prio-off {
  opacity: 0.65;
}
.prio-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: 4px;
}
.prio-name {
  font-size: var(--sf-font-14);
  font-weight: 600;
  color: var(--sf-text);
}
.prio-desc {
  margin: 0 0 var(--sf-space-2);
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  line-height: 1.45;
}
.prio-factors {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--sf-space-3);
  margin-bottom: var(--sf-space-2);
}
.factor-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.factor-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.factor-label {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
}
.factor-weight {
  font-size: var(--sf-font-11);
  color: var(--sf-primary);
  font-weight: 500;
}
.factor-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.factor-track {
  flex: 1;
  height: 5px;
  border-radius: 3px;
  background: var(--sf-border);
  overflow: hidden;
}
.factor-fill {
  height: 100%;
  border-radius: 3px;
  background: var(--sf-primary);
}
.factor-num {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  min-width: 40px;
  text-align: right;
}
.factor-note {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
}
.prio-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
}
.prio-threshold {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  font-weight: 500;
}

/* 调整记录 */
.adj-section {
  margin-top: var(--sf-space-3);
  padding-top: var(--sf-space-3);
  border-top: 1px solid var(--sf-border);
}
.adj-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
}
.adj-row {
  padding: var(--sf-space-2);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-bg);
  border: 1px solid var(--sf-border);
}
.adj-left {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}
.adj-id {
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-text-secondary);
}
.adj-arrow {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.adj-reason {
  margin: 0 0 4px;
  font-size: var(--sf-font-12);
  color: var(--sf-text);
  line-height: 1.4;
}
.adj-meta {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
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
.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: var(--sf-radius-sm);
  border: 1px solid var(--sf-border);
  background: var(--sf-surface);
  color: var(--sf-text-secondary);
  font-size: var(--sf-font-12);
  cursor: pointer;
  transition: background 0.15s;
}
.btn-ghost:hover {
  background: var(--sf-bg);
}

/* 开关（复用 AIAutomationRules 样式） */
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

/* 响应式 */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .member-row {
    grid-template-columns: 24px 1fr;
  }
  .member-sim {
    grid-column: 2;
  }
  .member-text {
    grid-column: 2;
  }
}
@media (max-width: 640px) {
  .stats-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .prio-factors {
    grid-template-columns: 1fr;
  }
}
</style>