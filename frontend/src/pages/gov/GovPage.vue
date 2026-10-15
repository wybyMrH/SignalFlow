<script setup lang="ts">
/**
 * FS-6 政务适配：克制成稳的政务统计与动向面板。
 * 结构参考商务洞察：顶部汇总统计卡 + 报告元信息 + 多标签页。
 * 覆盖规划文档 §6.3：诉求分级、督办事项、区域分布、热点主题聚类（含痛点成因）、
 * 舆情蓝黄橙红预警、政策告知统计、审计留痕。AI 仅提炼候选，处置需人工确认。
 */
import { onMounted, ref } from 'vue'

import AIFloatingAssistant from '@/components/ai/AIFloatingAssistant.vue'
import BarRow from '@/components/common/BarRow.vue'
import SfIcon from '@/components/common/SfIcon.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { fetchGovOverview } from '@/api/gov'
import { formatDateTime } from '@/utils'
import type { GovAlertLevel, GovOverview } from '@/types'

const overview = ref<GovOverview | null>(null)
const loading = ref(false)

const activeTab = ref<
  'classifications' | 'supervisions' | 'regions' | 'topics' | 'alerts' | 'notices' | 'audits'
>('classifications')

const tabs = [
  { key: 'classifications' as const, label: '诉求分级', icon: 'label' as const },
  { key: 'supervisions' as const, label: '督办事项', icon: 'shield' as const },
  { key: 'regions' as const, label: '区域分布', icon: 'map' as const },
  { key: 'topics' as const, label: '热点主题', icon: 'insights' as const },
  { key: 'alerts' as const, label: '舆情预警', icon: 'alert' as const },
  { key: 'notices' as const, label: '政策告知', icon: 'megaphone' as const },
  { key: 'audits' as const, label: '审计留痕', icon: 'file' as const },
]

const alertLevelLabel: Record<GovAlertLevel, string> = {
  red: '红色预警',
  orange: '橙色预警',
  yellow: '黄色预警',
  blue: '蓝色预警',
}
const alertLevelTone: Record<GovAlertLevel, string> = {
  red: 'alert-red',
  orange: 'alert-orange',
  yellow: 'alert-yellow',
  blue: 'alert-blue',
}
const trendLabel = (t: 'up' | 'flat' | 'down') => (t === 'up' ? '上升' : t === 'down' ? '回落' : '平稳')
const trendIcon = (t: 'up' | 'flat' | 'down') =>
  t === 'up' ? ('trend-up' as const) : t === 'down' ? ('trend-down' as const) : ('trend-flat' as const)

function pctBarStyle(pct: number) {
  return { width: `${Math.min(pct, 100).toFixed(1)}%` }
}
function rateText(rate: number) {
  return `${Math.round(rate * 100)}%`
}

onMounted(async () => {
  loading.value = true
  try {
    overview.value = await fetchGovOverview()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="gov-center">
    <!-- 顶部汇总统计卡 -->
    <div class="stats-row">
      <template v-if="loading || !overview">
        <Skeleton v-for="i in 6" :key="i" :rows="2" class="stat-skel" />
      </template>
      <template v-else>
        <div class="stat-card">
          <div class="stat-label">本期诉求总量</div>
          <div class="stat-value">{{ overview.summary.total_count }}</div>
          <div class="stat-hint">覆盖 {{ overview.regions.length }} 个区域</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">本周新增</div>
          <div class="stat-value" style="color: var(--sf-info)">{{ overview.summary.weekly_new }}</div>
          <div class="stat-hint">近 7 日归集</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">待办事项</div>
          <div class="stat-value" style="color: var(--sf-warning)">{{ overview.summary.pending_count }}</div>
          <div class="stat-hint">分级办理中</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">逾期未办</div>
          <div class="stat-value" style="color: var(--sf-danger)">{{ overview.summary.overdue_count }}</div>
          <div class="stat-hint">红黄牌预警</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">按期办结率</div>
          <div class="stat-value">{{ rateText(overview.summary.resolve_rate) }}</div>
          <div class="stat-hint">闭环办理口径</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">最高预警等级</div>
          <div
            v-if="overview.summary.highest_alert"
            class="stat-value"
            :class="`level-${overview.summary.highest_alert}`"
          >
            {{ alertLevelLabel[overview.summary.highest_alert].replace('预警', '') }}
          </div>
          <div v-else class="stat-value">—</div>
          <div class="stat-hint">蓝 → 黄 → 橙 → 红</div>
        </div>
      </template>
    </div>

    <!-- 报告元信息 -->
    <div v-if="overview" class="report-meta">
      <SfIcon name="file" :size="14" />
      统计周期 {{ overview.period }} · 生成于 {{ formatDateTime(overview.generated_at) }} ·
      AI 仅提炼候选，办理、答复与公开需人工确认
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
        <span
          v-if="t.key === 'alerts' && overview?.alerts.length"
          class="tab-badge"
        >{{ overview.alerts.length }}</span>
      </button>
    </div>

    <!-- 面板 1：诉求分级 -->
    <div v-if="activeTab === 'classifications'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="label" :size="14" />
          诉求分级
        </div>
        <div class="panel-sub">A 类即报 · 敏感优先 · 共 {{ overview?.classifications.length ?? 0 }} 级</div>
      </div>
      <Skeleton v-if="loading" :rows="6" />
      <div v-else-if="overview" class="bars">
        <BarRow
          v-for="c in overview.classifications"
          :key="c.level"
          :label="`${c.level} ${c.label}`"
          :value="c.count"
          :pct="c.pct"
          :tone="c.tone"
        />
      </div>
    </div>

    <!-- 面板 2：督办事项 -->
    <div v-if="activeTab === 'supervisions'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="shield" :size="14" />
          督办事项
        </div>
        <div class="panel-sub">逾期自动标红 · 联动治理任务闭环</div>
      </div>
      <Skeleton v-if="loading" :rows="6" />
      <table v-else-if="overview" class="tbl">
        <thead>
          <tr>
            <th>层级</th>
            <th>事项</th>
            <th>数量</th>
            <th>逾期</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in overview.supervisions" :key="s.level">
            <td class="nowrap">{{ s.level }}</td>
            <td class="nowrap dim">{{ s.label }}</td>
            <td class="num">{{ s.count }}</td>
            <td>
              <StatusBadge :label="String(s.overdue)" :tone="s.overdue > 0 ? 'danger' : 'success'" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 面板 3：区域分布 -->
    <div v-if="activeTab === 'regions'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="map" :size="14" />
          区域诉求分布
        </div>
        <div class="panel-sub">按诉求来源区域统计 · 热点事项实时归口</div>
      </div>
      <Skeleton v-if="loading" :rows="6" />
      <div v-else-if="overview" class="region-list">
        <div v-for="r in overview.regions" :key="r.region" class="region-row">
          <div class="region-info">
            <span class="region-name">{{ r.region }}</span>
            <span class="region-count">{{ r.count }} 件</span>
            <span class="region-trend" :class="`trend-${r.trend}`">
              <SfIcon :name="trendIcon(r.trend)" :size="12" />
              {{ trendLabel(r.trend) }}
            </span>
          </div>
          <div class="region-bar-wrap">
            <div class="region-track">
              <div class="region-fill" :style="pctBarStyle(r.pct)" />
            </div>
            <span class="region-pct">{{ r.pct }}%</span>
          </div>
          <div class="region-meta">
            <span class="meta-label">热点事项</span>
            <span class="meta-hot">{{ r.hot_issue }}</span>
            <span v-for="d in r.departments" :key="d" class="dept-chip">{{ d }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 面板 4：热点主题 -->
    <div v-if="activeTab === 'topics'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="insights" :size="14" />
          热点主题聚类
        </div>
        <div class="panel-sub">覆盖量 · 增幅 · 痛点成因（引用原话为证）</div>
      </div>
      <Skeleton v-if="loading" :rows="6" />
      <div v-else-if="overview" class="topic-list">
        <div v-for="t in overview.topics" :key="t.id" class="topic-card">
          <div class="topic-top">
            <div class="topic-id">{{ t.id }}</div>
            <StatusBadge
              :label="t.task_status === 'generated' ? '已生成治理任务' : '待生成治理任务'"
              :tone="t.task_status === 'generated' ? 'success' : 'warning'"
            />
          </div>
          <div class="topic-title">{{ t.title }}</div>
          <p class="topic-summary">{{ t.summary }}</p>
          <div class="topic-stats">
            <div class="topic-stat">
              <span class="topic-stat-num">{{ t.coverage }}</span>
              <span class="topic-stat-label">条覆盖</span>
            </div>
            <div class="topic-stat" :class="t.growth >= 0 ? 'growth-up' : 'growth-down'">
              <span class="topic-stat-num">{{ t.growth >= 0 ? '+' : '' }}{{ t.growth }}%</span>
              <span class="topic-stat-label">增幅</span>
            </div>
            <div class="topic-stat">
              <span class="topic-stat-num">{{ t.regions.join('、') }}</span>
              <span class="topic-stat-label">涉及区域</span>
            </div>
            <div class="topic-stat">
              <span class="topic-stat-num">{{ t.department }}</span>
              <span class="topic-stat-label">归口部门</span>
            </div>
          </div>
          <div class="topic-cause">
            <span class="cause-label">痛点成因</span>
            <span class="cause-value">{{ t.root_cause }}</span>
          </div>
          <div class="topic-evidence">
            <span class="evidence-mark">“</span>
            <span class="evidence-text">{{ t.evidence }}</span>
            <span class="evidence-mark">”</span>
          </div>
          <div v-if="t.task_status === 'generated' && t.task_id" class="topic-task">
            <SfIcon name="check" :size="12" />
            治理任务 {{ t.task_id }} 已进入督办流程
          </div>
        </div>
      </div>
    </div>

    <!-- 面板 5：舆情预警 -->
    <div v-if="activeTab === 'alerts'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="alert" :size="14" />
          舆情与风险预警
        </div>
        <div class="panel-sub">敏感词库 + 异常量级 + 情绪分析 → 蓝黄橙红分级推送</div>
      </div>
      <Skeleton v-if="loading" :rows="6" />
      <div v-else-if="overview" class="alert-list">
        <div v-for="a in overview.alerts" :key="a.id" class="alert-card">
          <div class="alert-top">
            <span class="alert-level" :class="alertLevelTone[a.level]">
              <span class="level-dot" />{{ alertLevelLabel[a.level] }}
            </span>
            <span class="alert-id">{{ a.id }}</span>
          </div>
          <div class="alert-title">{{ a.title }}</div>
          <p class="alert-summary">{{ a.summary }}</p>
          <div class="alert-trigger">
            <span class="trigger-label">触发信号</span>
            <span class="trigger-value">{{ a.trigger }}</span>
          </div>
          <div class="alert-meta">
            <span class="alert-evidence">{{ a.evidence_count }} 条证据</span>
            <span class="alert-regions">{{ a.regions.join(' / ') }}</span>
            <span v-if="a.dispatched" class="alert-dispatched">
              <SfIcon name="send" :size="12" />
              已派发至 {{ a.dispatched_to }}
            </span>
            <span v-else class="alert-pending">待派发处理</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 面板 6：政策告知 -->
    <div v-if="activeTab === 'notices'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="megaphone" :size="14" />
          政策告知
        </div>
        <div class="panel-sub">公告直发渠道 · 送达与阅读统计</div>
      </div>
      <Skeleton v-if="loading" :rows="6" />
      <div v-else-if="overview" class="notice-list">
        <div v-for="n in overview.notices" :key="n.id" class="notice-card">
          <div class="notice-top">
            <span class="notice-title">{{ n.title }}</span>
            <StatusBadge
              :label="n.status === 'published' ? '已发布' : '草稿'"
              :tone="n.status === 'published' ? 'success' : 'warning'"
            />
          </div>
          <p class="notice-content">{{ n.content }}</p>
          <div class="notice-meta">
            <span class="notice-scope">{{ n.scope }}</span>
            <span class="notice-channel">
              <SfIcon name="send" :size="12" />
              {{ n.channel }}
            </span>
            <span class="notice-sent">送达 {{ n.sent_count }} 人</span>
            <span v-if="n.status === 'published'" class="notice-read">阅读率 {{ rateText(n.read_rate) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 面板 7：审计留痕 -->
    <div v-if="activeTab === 'audits'" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <SfIcon name="file" :size="14" />
          审计留痕
        </div>
        <div class="panel-sub">操作全程可追溯 · 数据不出域</div>
      </div>
      <Skeleton v-if="loading" :rows="6" />
      <table v-else-if="overview" class="tbl">
        <thead>
          <tr>
            <th>操作</th>
            <th>操作人</th>
            <th>对象</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in overview.audits" :key="a.id">
            <td class="nowrap">{{ a.action }}</td>
            <td class="nowrap dim">{{ a.operator }}</td>
            <td class="nowrap dim">{{ a.target }}</td>
            <td class="nowrap dim">{{ a.time }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <AIFloatingAssistant context="gov" />
</template>

<style scoped>
.gov-center {
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
.level-blue { color: var(--sf-info); }
.level-yellow { color: var(--sf-warning); }
.level-orange { color: #d97706; }
.level-red { color: var(--sf-danger); }

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
  flex-wrap: wrap;
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
  background: var(--sf-danger);
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

/* 诉求分级 */
.bars {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
}

/* 区域分布 */
.region-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.region-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.region-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.region-name {
  font-size: var(--sf-font-13);
  font-weight: 600;
  color: var(--sf-text);
  min-width: 76px;
}
.region-count {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
}
.region-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--sf-font-11);
}
.trend-up { color: var(--sf-success); }
.trend-down { color: var(--sf-danger); }
.trend-flat { color: var(--sf-text-faint); }
.region-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.region-track {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: var(--sf-border);
  overflow: hidden;
}
.region-fill {
  height: 100%;
  border-radius: 4px;
  background: var(--sf-primary);
}
.region-pct {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  min-width: 40px;
  text-align: right;
}
.region-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: var(--sf-font-12);
}
.meta-label {
  color: var(--sf-text-faint);
}
.meta-hot {
  color: var(--sf-text);
  font-weight: 500;
}
.dept-chip {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: var(--sf-font-11);
  background: var(--sf-primary-soft);
  color: var(--sf-primary);
}

/* 热点主题 */
.topic-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.topic-card {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  padding: var(--sf-space-3);
  background: var(--sf-bg);
}
.topic-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: 6px;
}
.topic-id {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  font-weight: 600;
}
.topic-title {
  font-size: var(--sf-font-14);
  font-weight: 600;
  color: var(--sf-text);
  margin-bottom: 6px;
}
.topic-summary {
  margin: 0 0 var(--sf-space-2);
  font-size: var(--sf-font-12);
  line-height: 1.5;
  color: var(--sf-text-secondary);
}
.topic-stats {
  display: flex;
  gap: var(--sf-space-2);
  flex-wrap: wrap;
  margin-bottom: var(--sf-space-2);
}
.topic-stat {
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 4px 8px;
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
}
.topic-stat-num {
  font-size: var(--sf-font-13);
  font-weight: 700;
  color: var(--sf-primary);
}
.growth-up .topic-stat-num { color: var(--sf-danger); }
.growth-down .topic-stat-num { color: var(--sf-success); }
.topic-stat-label {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
}
.topic-cause {
  display: flex;
  gap: 8px;
  font-size: var(--sf-font-12);
  line-height: 1.4;
  margin-bottom: 6px;
}
.cause-label {
  color: var(--sf-text-faint);
  min-width: 56px;
  flex-shrink: 0;
}
.cause-value {
  color: var(--sf-warning);
  font-weight: 500;
}
.topic-evidence {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  padding: 6px 8px;
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  border-left: 3px solid var(--sf-primary);
  font-size: var(--sf-font-12);
  line-height: 1.5;
  color: var(--sf-text-secondary);
  margin-bottom: 6px;
}
.evidence-mark {
  color: var(--sf-primary);
  font-weight: 700;
}
.evidence-text {
  flex: 1;
}
.topic-task {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--sf-font-12);
  color: var(--sf-success);
  font-weight: 500;
}

/* 舆情预警 */
.alert-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sf-space-3);
}
.alert-card {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  padding: var(--sf-space-3);
  background: var(--sf-bg);
}
.alert-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: 6px;
}
.alert-level {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: var(--sf-font-11);
  font-weight: 600;
}
.level-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.alert-red {
  background: rgba(220, 53, 69, 0.1);
  color: var(--sf-danger);
}
.alert-orange {
  background: rgba(217, 119, 6, 0.12);
  color: #b45309;
}
.alert-yellow {
  background: rgba(202, 138, 4, 0.12);
  color: #a16207;
}
.alert-blue {
  background: rgba(14, 116, 144, 0.12);
  color: #0e7490;
}
.alert-id {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  font-weight: 600;
}
.alert-title {
  font-size: var(--sf-font-14);
  font-weight: 600;
  color: var(--sf-text);
  margin-bottom: 6px;
}
.alert-summary {
  margin: 0 0 var(--sf-space-2);
  font-size: var(--sf-font-12);
  line-height: 1.5;
  color: var(--sf-text-secondary);
}
.alert-trigger {
  display: flex;
  gap: 8px;
  font-size: var(--sf-font-12);
  line-height: 1.4;
  margin-bottom: var(--sf-space-2);
  padding: 6px 8px;
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
}
.trigger-label {
  color: var(--sf-text-faint);
  min-width: 56px;
  flex-shrink: 0;
}
.trigger-value {
  color: var(--sf-text-secondary);
}
.alert-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: var(--sf-font-11);
}
.alert-evidence {
  color: var(--sf-warning);
  font-weight: 500;
}
.alert-regions {
  color: var(--sf-text-faint);
}
.alert-dispatched {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--sf-success);
  font-weight: 500;
}
.alert-pending {
  color: var(--sf-text-faint);
}

/* 政策告知 */
.notice-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.notice-card {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  padding: var(--sf-space-3);
  background: var(--sf-bg);
}
.notice-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-bottom: 6px;
}
.notice-title {
  font-size: var(--sf-font-14);
  font-weight: 600;
  color: var(--sf-text);
}
.notice-content {
  margin: 0 0 var(--sf-space-2);
  font-size: var(--sf-font-12);
  line-height: 1.5;
  color: var(--sf-text-secondary);
}
.notice-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
}
.notice-channel,
.notice-sent,
.notice-read {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.notice-read {
  color: var(--sf-primary);
  font-weight: 500;
}

/* 表格（督办 / 审计） */
.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--sf-font-13);
}
.tbl th {
  height: 32px;
  padding: 0 var(--sf-space-1);
  text-align: left;
  font-size: var(--sf-font-12);
  font-weight: 500;
  color: var(--sf-text-secondary);
  background: var(--sf-bg);
  border-bottom: 1px solid var(--sf-border);
  white-space: nowrap;
}
.tbl td {
  height: 36px;
  padding: 0 var(--sf-space-1);
  border-bottom: 1px solid var(--sf-border);
  vertical-align: middle;
}
.tbl tr:last-child td {
  border-bottom: none;
}
.nowrap {
  white-space: nowrap;
}
.dim {
  color: var(--sf-text-secondary);
  font-size: var(--sf-font-12);
}
.num {
  font-variant-numeric: tabular-nums;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .alert-list {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .stats-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>