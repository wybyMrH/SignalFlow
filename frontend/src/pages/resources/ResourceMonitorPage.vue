<script setup lang="ts">
/**
 * 资源管理（position 3）：
 * 侧边栏「资源管理」入口对应的运维观测页。
 * 覆盖服务器（CPU/内存/磁盘/负载）、数据库（连接/慢查询/表空间）、
 * API 端点（健康/响应时间/错误率）、系统日志检索与告警。
 * 理念：资源不是静态台账，而是与 Agent 执行、工作流运行联动的观测层——
 * 总览「资源健康」卡与本站共用同一数据源；工作流异常会在这里回显为告警。
 * 所有数据由 mock 驱动，不实现真实后端监控。
 */
import { computed, onMounted, ref } from 'vue'

import AIFloatingAssistant from '@/components/ai/AIFloatingAssistant.vue'
import SfIcon from '@/components/common/SfIcon.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useResourcesStore } from '@/stores/resources'
import { useWorkflowsStore } from '@/stores/workflows'
import { formatDateTime } from '@/utils'
import type { ResourceAlert } from '@/types'

const store = useResourcesStore()
const workflowsStore = useWorkflowsStore()

const activeTab = ref<'servers' | 'databases' | 'apis' | 'logs'>('servers')
const logLevel = ref<'all' | 'info' | 'warn' | 'error'>('all')
const logKeyword = ref('')

const levelTone: Record<string, 'success' | 'warning' | 'danger' | 'neutral' | 'info'> = {
  healthy: 'success',
  degraded: 'warning',
  warning: 'warning',
  down: 'danger',
  error: 'danger',
  info: 'info',
}

const logLevelTone: Record<string, 'info' | 'warning' | 'danger'> = {
  info: 'info',
  warn: 'warning',
  error: 'danger',
}

/** 进度条取色：按阈值分级 */
function usageTone(v: number): 'ok' | 'warn' | 'danger' {
  if (v >= 90) return 'danger'
  if (v >= 70) return 'warn'
  return 'ok'
}

function usageColor(v: number): string {
  const t = usageTone(v)
  if (t === 'danger') return 'var(--sf-danger)'
  if (t === 'warn') return 'var(--sf-warning)'
  return 'var(--sf-success)'
}

const serverHealthy = computed(
  () => store.detail?.servers.filter((s) => s.status === 'healthy').length ?? 0,
)
const dbHealthy = computed(
  () => store.detail?.databases.filter((d) => d.status === 'healthy').length ?? 0,
)
const apiHealthy = computed(
  () => store.detail?.apis.filter((a) => a.status !== 'down').length ?? 0,
)

const servers = computed(() => store.detail?.servers ?? [])
const databases = computed(() => store.detail?.databases ?? [])
const apis = computed(() => store.detail?.apis ?? [])
/** 告警 = 静态告警 + 工作流运行异常（与工作流配置页实时同步，形成「执行 → 观测」闭环） */
const alerts = computed<ResourceAlert[]>(() => {
  const base = [...(store.detail?.alerts ?? [])]
  for (const w of workflowsStore.details) {
    const failedRun = w.history.find((h) => h.status === 'failed')
    if (failedRun) {
      base.push({
        id: `WF-${w.id}-AL`,
        level: 'error',
        title: `工作流「${w.name}」运行失败`,
        time: failedRun.started_at,
        target: `${w.id} / ${failedRun.error_message ?? '运行异常'}`,
      })
    }
  }
  return base
})

const filteredLogs = computed(() => {
  const logs = store.detail?.logs ?? []
  const kw = logKeyword.value.trim().toLowerCase()
  return logs.filter((l) => {
    if (logLevel.value !== 'all' && l.level !== logLevel.value) return false
    if (!kw) return true
    return (
      l.message.toLowerCase().includes(kw) ||
      l.module.toLowerCase().includes(kw) ||
      l.id.toLowerCase().includes(kw)
    )
  })
})

const sortedAlerts = computed(() => {
  const rank = { error: 0, warn: 1, info: 2 }
  return [...alerts.value].sort((a, b) => rank[a.level] - rank[b.level])
})

const alertTone: Record<string, 'danger' | 'warning' | 'info'> = {
  error: 'danger',
  warn: 'warning',
  info: 'info',
}

onMounted(() => {
  if (!store.detail) store.fetchAll()
  if (!workflowsStore.details.length) workflowsStore.fetchAll()
})

function refresh() {
  store.fetchAll()
}
</script>

<template>
  <div class="resource-center">
    <!-- 顶部汇总统计 -->
    <div class="stats-row">
      <template v-if="store.loading && !store.detail">
        <Skeleton v-for="i in 4" :key="i" :rows="2" class="stat-skel" />
      </template>
      <template v-else>
        <div class="stat-card">
          <div class="stat-label">服务器健康</div>
          <div class="stat-value" style="color: var(--sf-info)">
            {{ store.healthyServers }}/{{ servers.length }}
          </div>
          <div class="stat-hint">
            {{ serverHealthy === servers.length ? '全部正常' : '存在负载/异常节点' }}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">数据库</div>
          <div class="stat-value" style="color: var(--sf-warning)">
            {{ dbHealthy }}/{{ databases.length }}
          </div>
          <div class="stat-hint">连接 / 慢查询 / 表空间</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">API 可用端点</div>
          <div class="stat-value" style="color: var(--sf-success)">
            {{ apiHealthy }}/{{ apis.length }}
          </div>
          <div class="stat-hint">
            {{ store.downApis ? `${store.downApis} 个宕机 · ` : '' }}{{ store.degradedApis }} 个性能降级
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">活跃告警</div>
          <div class="stat-value" :style="{ color: alerts.some((a) => a.level === 'error') ? 'var(--sf-danger)' : 'var(--sf-warning)' }">
            {{ alerts.length }}
          </div>
          <div class="stat-hint">最高 {{ sortedAlerts[0]?.level === 'error' ? '严重' : sortedAlerts[0]?.level === 'warn' ? '警告' : '提示' }}</div>
        </div>
      </template>
    </div>

    <!-- 理念提示条 -->
    <div class="notice-bar">
      <SfIcon name="magic" :size="14" />
      <span>
        资源观测不是孤立台账：总览「资源健康」卡片与本站共用同一数据源；工作流与 Agent 运行异常会回显为告警，
        形成「执行 → 观测 → 处置」闭环。数据由 mock 驱动，可在总览与本站之间互相跳转核对。
      </span>
      <button type="button" class="btn ghost refresh-btn" @click="refresh">
        <SfIcon name="refresh" :size="13" :class="{ spin: store.loading }" /> 刷新
      </button>
    </div>

    <!-- Tab 切换 -->
    <div class="tabs">
      <button type="button" class="tab-btn" :class="{ active: activeTab === 'servers' }" @click="activeTab = 'servers'">
        <SfIcon name="server" :size="14" /> 服务器
      </button>
      <button type="button" class="tab-btn" :class="{ active: activeTab === 'databases' }" @click="activeTab = 'databases'">
        <SfIcon name="database" :size="14" /> 数据库
      </button>
      <button type="button" class="tab-btn" :class="{ active: activeTab === 'apis' }" @click="activeTab = 'apis'">
        <SfIcon name="workflow" :size="14" /> API 服务
      </button>
      <button type="button" class="tab-btn" :class="{ active: activeTab === 'logs' }" @click="activeTab = 'logs'">
        <SfIcon name="term" :size="14" /> 日志与告警
      </button>
    </div>

    <!-- 服务器 -->
    <template v-if="activeTab === 'servers'">
      <div class="section-head">
        <div class="toolbar-title">节点状态（CPU / 内存 / 磁盘 / 负载）</div>
      </div>
      <div v-if="store.loading && !store.detail" class="server-grid">
        <Skeleton v-for="i in 4" :key="i" :rows="6" class="server-skel" />
      </div>
      <div v-else class="server-grid">
        <article v-for="s in servers" :key="s.id" class="server-card">
          <header class="server-head">
            <div class="server-title">
              <SfIcon name="server" :size="16" />
              <span class="server-name">{{ s.name }}</span>
            </div>
            <StatusBadge :label="s.status === 'healthy' ? '正常' : s.status === 'warning' ? '负载高' : '宕机'" :tone="levelTone[s.status] ?? 'neutral'" />
          </header>
          <div class="server-meta">
            <span class="role">{{ s.role }}</span>
            <span class="uptime"><SfIcon name="clock" :size="10" /> {{ s.uptime }}</span>
          </div>
          <div v-for="item in [
            { label: 'CPU', value: s.cpu },
            { label: '内存', value: s.mem },
            { label: '磁盘', value: s.disk },
          ]" :key="item.label" class="meter">
            <div class="meter-head">
              <span class="meter-label">{{ item.label }}</span>
              <span class="meter-value">{{ item.value }}%</span>
            </div>
            <div class="meter-track">
              <div class="meter-fill" :style="{ width: `${item.value}%`, background: usageColor(item.value) }" />
            </div>
          </div>
          <footer class="server-foot">
            <span class="load">负载 {{ s.load }}</span>
            <span class="node-id">{{ s.id }}</span>
          </footer>
        </article>
      </div>
    </template>

    <!-- 数据库 -->
    <template v-else-if="activeTab === 'databases'">
      <div class="section-head">
        <div class="toolbar-title">实例状态（连接数 / 慢查询 / 表空间）</div>
      </div>
      <div v-if="store.loading && !store.detail" class="db-list">
        <Skeleton v-for="i in 3" :key="i" :rows="4" class="db-skel" />
      </div>
      <div v-else class="db-list">
        <article v-for="d in databases" :key="d.id" class="db-card">
          <div class="db-icon"><SfIcon name="database" :size="18" /></div>
          <div class="db-main">
            <div class="db-title">
              <span class="db-name">{{ d.name }}</span>
              <StatusBadge :label="d.status === 'healthy' ? '正常' : d.status === 'degraded' ? '降级' : '异常'" :tone="levelTone[d.status] ?? 'neutral'" />
            </div>
            <div class="db-engine">{{ d.engine }}</div>
            <div class="db-stats">
              <span class="db-stat">
                连接
                <b :style="{ color: d.connections > d.max_connections * 0.85 ? 'var(--sf-warning)' : undefined }">{{ d.connections }}</b>
                / {{ d.max_connections }}
              </span>
              <span class="db-stat">
                慢查询
                <b :style="{ color: d.slow_queries > 5 ? 'var(--sf-warning)' : undefined }">{{ d.slow_queries }}</b>
              </span>
              <span class="db-stat">表空间 {{ d.tablespace_pct }}%</span>
            </div>
          </div>
          <div class="db-right">
            <div class="meter" style="width: 120px">
              <div class="meter-head">
                <span class="meter-label">表空间</span>
                <span class="meter-value">{{ d.tablespace_pct }}%</span>
              </div>
              <div class="meter-track">
                <div
                  class="meter-fill"
                  :style="{ width: `${d.tablespace_pct}%`, background: usageColor(d.tablespace_pct) }"
                />
              </div>
            </div>
            <span class="db-check">检查于 {{ formatDateTime(d.last_check) }}</span>
          </div>
        </article>
      </div>
    </template>

    <!-- API 服务 -->
    <template v-else-if="activeTab === 'apis'">
      <div class="section-head">
        <div class="toolbar-title">端点健康（响应时间 / 错误率 / QPS）</div>
      </div>
      <div v-if="store.loading && !store.detail" class="api-list">
        <Skeleton v-for="i in 6" :key="i" :rows="3" class="api-skel" />
      </div>
      <div v-else class="api-table">
        <table class="table">
          <thead>
            <tr>
              <th>方法</th>
              <th>端点</th>
              <th>状态</th>
              <th>平均响应</th>
              <th>错误率</th>
              <th>QPS</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in apis" :key="a.id" :class="{ 'row-down': a.status === 'down' }">
              <td>
                <span class="method" :style="{ color: a.method === 'GET' ? 'var(--sf-info)' : a.method === 'POST' ? 'var(--sf-success)' : 'var(--sf-warning)' }">
                  {{ a.method }}
                </span>
              </td>
              <td class="path">
                <code>{{ a.path }}</code>
                <span v-if="a.status === 'down'" class="down-tag">宕机</span>
              </td>
              <td><StatusBadge :label="a.status === 'healthy' ? '正常' : a.status === 'degraded' ? '降级' : '异常'" :tone="levelTone[a.status] ?? 'neutral'" /></td>
              <td>
                <span :style="{ color: a.response_ms > 500 ? 'var(--sf-warning)' : undefined }">{{ a.response_ms }}ms</span>
              </td>
              <td>
                <span :style="{ color: a.error_rate > 3 ? 'var(--sf-danger)' : a.error_rate > 1 ? 'var(--sf-warning)' : undefined }">
                  {{ a.error_rate }}%
                </span>
              </td>
              <td>{{ a.rps.toFixed(1) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- 日志与告警 -->
    <template v-else>
      <div class="log-toolbar">
        <div class="log-filters">
          <button
            v-for="lv in (['all', 'info', 'warn', 'error'] as const)"
            :key="lv"
            type="button"
            class="filter-btn"
            :class="{ active: logLevel === lv }"
            @click="logLevel = lv"
          >
            {{ lv === 'all' ? '全部' : lv === 'info' ? '信息' : lv === 'warn' ? '警告' : '错误' }}
          </button>
        </div>
        <label class="search-box">
          <SfIcon name="search" :size="13" />
          <input v-model="logKeyword" type="text" placeholder="检索模块 / 消息 / 日志编号" />
        </label>
      </div>

      <div class="log-layout">
        <div class="log-panel">
          <div class="panel-title">系统日志（{{ filteredLogs.length }} 条）</div>
          <div v-if="store.loading && !store.detail" class="log-list">
            <Skeleton v-for="i in 6" :key="i" :rows="2" class="log-skel" />
          </div>
          <div v-else class="log-list">
            <div v-if="!filteredLogs.length" class="log-empty">无匹配日志</div>
            <div v-for="l in filteredLogs" :key="l.id" class="log-item">
              <StatusBadge :label="l.level.toUpperCase()" :tone="logLevelTone[l.level]" />
              <div class="log-body">
                <div class="log-meta">
                  <span class="log-module">{{ l.module }}</span>
                  <span class="log-time">{{ formatDateTime(l.time) }}</span>
                </div>
                <div class="log-msg">{{ l.message }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="alert-panel">
          <div class="panel-title">告警中心（{{ alerts.length }}）</div>
          <div class="alert-list">
            <div v-for="a in sortedAlerts" :key="a.id" class="alert-item" :class="a.level">
              <StatusBadge :label="a.level === 'error' ? '严重' : a.level === 'warn' ? '警告' : '提示'" :tone="alertTone[a.level]" />
              <div class="alert-main">
                <div class="alert-title">{{ a.title }}</div>
                <div class="alert-target">{{ a.target }}</div>
              </div>
              <span class="alert-time">{{ a.time.replace('T', ' ').slice(5, 16) }}</span>
            </div>
          </div>
          <div class="alert-note">
            <SfIcon name="link" :size="12" />
            告警与总览「资源健康」卡、工作流配置页运行历史同源
          </div>
        </div>
      </div>
    </template>

    <AIFloatingAssistant context="resources" />
  </div>
</template>

<style scoped>
.resource-center {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}

/* 顶部统计 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sf-space-3);
}
.stat-skel {
  height: 84px;
}
.stat-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 84px;
  max-height: 92px;
  padding: 12px 16px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  box-shadow: var(--sf-shadow);
}
.stat-label {
  font-size: 12px;
  color: var(--sf-text-secondary);
  margin-bottom: 4px;
}
.stat-value {
  font-size: 24px;
  font-weight: 650;
  line-height: 1.15;
  color: var(--sf-text);
}
.stat-hint {
  margin-top: 4px;
  font-size: 12px;
  color: var(--sf-text-faint);
}

.notice-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--sf-radius-sm);
  background: var(--sf-primary-soft);
  border: 1px solid var(--sf-primary-border);
  color: var(--sf-primary);
  font-size: 12px;
  line-height: 1.5;
}
.notice-bar .refresh-btn {
  margin-left: auto;
  flex-shrink: 0;
  color: var(--sf-primary);
}
.refresh-btn:hover {
  background: var(--sf-primary-soft);
}
.spin {
  animation: spin 0.9s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.tabs {
  display: flex;
  gap: 6px;
  border-bottom: 1px solid var(--sf-border);
}
.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--sf-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease;
}
.tab-btn.active {
  color: var(--sf-primary);
  border-bottom-color: var(--sf-primary);
  font-weight: 600;
}

.section-head {
  padding-top: 2px;
}
.toolbar-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--sf-text-secondary);
}

/* 服务器 */
.server-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--sf-space-3);
}
.server-skel {
  height: 210px;
}
.server-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  box-shadow: var(--sf-shadow);
}
.server-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.server-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--sf-text);
  min-width: 0;
}
.server-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.server-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--sf-text-faint);
}
.role {
  padding: 1px 8px;
  border-radius: 10px;
  background: var(--sf-primary-soft);
  color: var(--sf-primary);
}
.uptime {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}
.meter {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.meter-head {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
}
.meter-label {
  color: var(--sf-text-secondary);
}
.meter-value {
  color: var(--sf-text);
  font-weight: 600;
}
.meter-track {
  height: 6px;
  border-radius: 3px;
  background: var(--sf-border);
  overflow: hidden;
}
.meter-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
}
.server-foot {
  display: flex;
  justify-content: space-between;
  border-top: 1px solid var(--sf-border);
  padding-top: 8px;
  font-size: 11px;
  color: var(--sf-text-faint);
}
.node-id {
  font-variant-numeric: tabular-nums;
}

/* 数据库 */
.db-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
}
.db-skel {
  height: 96px;
}
.db-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  box-shadow: var(--sf-shadow);
}
.db-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--sf-radius-sm);
  background: var(--sf-primary-soft);
  color: var(--sf-primary);
  flex-shrink: 0;
}
.db-main {
  flex: 1;
  min-width: 0;
}
.db-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--sf-text);
}
.db-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.db-engine {
  margin-top: 2px;
  font-size: 12px;
  color: var(--sf-text-faint);
}
.db-stats {
  display: flex;
  gap: 14px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--sf-text-secondary);
}
.db-stat b {
  color: var(--sf-text);
}
.db-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}
.db-check {
  font-size: 11px;
  color: var(--sf-text-faint);
}

/* API 表格 */
.api-table {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  overflow: hidden;
}
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.table th,
.table td {
  padding: 9px 12px;
  text-align: left;
  border-bottom: 1px solid var(--sf-border);
}
.table th {
  font-size: 11px;
  font-weight: 600;
  color: var(--sf-text-faint);
  background: var(--sf-surface);
}
.table tbody tr:last-child td {
  border-bottom: none;
}
.table tbody tr:hover {
  background: var(--sf-primary-soft);
}
.row-down {
  background: var(--sf-danger-soft);
}
.method {
  font-weight: 700;
}
.path {
  display: flex;
  align-items: center;
  gap: 8px;
}
.path code {
  font-size: 12px;
  color: var(--sf-text);
}
.down-tag {
  padding: 1px 6px;
  border-radius: 8px;
  font-size: 10px;
  color: var(--sf-danger);
  background: var(--sf-danger-soft);
}
.api-skel {
  height: 60px;
}

/* 日志与告警 */
.log-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.log-filters {
  display: flex;
  gap: 6px;
}
.filter-btn {
  padding: 5px 12px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.filter-btn.active {
  border-color: var(--sf-primary);
  background: var(--sf-primary);
  color: #fff;
}
.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text-faint);
  min-width: 260px;
}
.search-box input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: var(--sf-text);
  font-size: 12px;
}
.log-layout {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: var(--sf-space-3);
  align-items: start;
}
.log-panel,
.alert-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--sf-text-secondary);
}
.log-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 560px;
  overflow-y: auto;
}
.log-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
}
.log-body {
  flex: 1;
  min-width: 0;
}
.log-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.log-module {
  font-size: 12px;
  font-weight: 600;
  color: var(--sf-text);
}
.log-time {
  font-size: 11px;
  color: var(--sf-text-faint);
}
.log-msg {
  margin-top: 3px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--sf-text-secondary);
}
.log-empty {
  padding: 32px 0;
  text-align: center;
  font-size: 12px;
  color: var(--sf-text-faint);
}
.log-skel {
  height: 58px;
}
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
}
.alert-item.error {
  border-left: 3px solid var(--sf-danger);
}
.alert-item.warn {
  border-left: 3px solid var(--sf-warning);
}
.alert-item.info {
  border-left: 3px solid var(--sf-info);
}
.alert-main {
  flex: 1;
  min-width: 0;
}
.alert-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--sf-text);
}
.alert-target {
  margin-top: 2px;
  font-size: 11px;
  color: var(--sf-text-faint);
}
.alert-time {
  font-size: 11px;
  color: var(--sf-text-faint);
}
.alert-note {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--sf-text-faint);
}

@media (max-width: 1100px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .log-layout {
    grid-template-columns: 1fr;
  }
}
</style>