<script setup lang="ts">
/**
 * 工作流配置（position 4）：
 * 侧边栏「工作流配置」入口。展示预置工作流模板（发布公告 / 自动分类与去重 /
 * 舆情监测与应急 / 商单自动回复 / 多源诉求聚合解决），每个工作流包含：
 * LangGraph 风格节点图、触发条件、Agent 绑定、工具链、运行历史/日志。
 * 与 Agent 配置页、总览驾驶舱、资源管理页共用同一数据源，形成
 * 「展示 → 配置 → 执行 → 观测」闭环；全部数据由 mock 驱动，可运行模拟案例。
 */
import { computed, onMounted, ref } from 'vue'

import AIFloatingAssistant from '@/components/ai/AIFloatingAssistant.vue'
import Drawer from '@/components/common/Drawer.vue'
import SfIcon from '@/components/common/SfIcon.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useAgentsStore } from '@/stores/agents'
import { useWorkflowsStore } from '@/stores/workflows'
import type { WorkflowDetail, WorkflowNode, WorkflowRun } from '@/types'
import { formatDateTime } from '@/utils'

const wf = useWorkflowsStore()
const agents = useAgentsStore()

const detailOpen = ref(false)
const detailId = ref('')

const activeWf = computed(() => (detailId.value ? wf.byId(detailId.value) : undefined))

/** 工具 key → 中文名（与 Agent 工具链展示口径一致） */
const TOOL_LABELS: Record<string, string> = {
  policy_search: '查政策库',
  lead_search: '查商务线索',
  feedback_search: '查反馈库',
  news_search: '舆情检索',
  send_email: '发送邮件',
  send_sms: '发送短信',
  create_todo: '创建工单',
  db_query: '查数据库',
}
const toolLabel = (key: string) => TOOL_LABELS[key] ?? key

const agentName = (id: string) => agents.agents.find((a) => a.id === id)?.name ?? id

const typeLabel: Record<WorkflowNode['type'], string> = {
  start: '开始',
  agent: 'Agent',
  tool: '工具',
  decision: '判断',
  end: '结束',
}

const runTone: Record<WorkflowRun['status'], 'info' | 'success' | 'danger' | 'muted'> = {
  running: 'info',
  success: 'success',
  failed: 'danger',
  cancelled: 'muted',
}

const runLabel: Record<WorkflowRun['status'], string> = {
  running: '运行中',
  success: '成功',
  failed: '失败',
  cancelled: '已取消',
}

/** 工作流内绑定的 Agent 列表 */
function agentsOf(w: WorkflowDetail): string[] {
  return Array.from(new Set(Object.values(w.agent_bindings)))
}

/** 工作流内使用的工具 key 列表（去重） */
function toolsOf(w: WorkflowDetail): string[] {
  const keys = new Set<string>()
  for (const list of Object.values(w.tool_chain)) list.forEach((k) => keys.add(k))
  return Array.from(keys)
}

/** 工作流的 Agent 节点（详情抽屉中用于指派） */
const agentNodes = computed(() => activeWf.value?.nodes.filter((n) => n.type === 'agent') ?? [])

const lastRun = (w: WorkflowDetail) => w.history[0]

function loadAll() {
  void Promise.all([wf.fetchAll(), agents.fetchAll()])
}

onMounted(loadAll)

function refresh() {
  loadAll()
}

function openDetail(id: string) {
  detailId.value = id
  detailOpen.value = true
}

function toggleWf(w: WorkflowDetail) {
  wf.toggleEnabled(w.id)
}

function runNow(w: WorkflowDetail) {
  wf.simulateRun(w.id)
}

function assignNode(nodeId: string, agentId: string) {
  const w = activeWf.value
  if (w) wf.assignNodeAgent(w.id, nodeId, agentId)
}

/* ---------------- LangGraph 风格节点图（横向分层布局，SVG 连线 + HTML 节点） ---------------- */
const NODE_W = 132
const NODE_H = 54
const GAP_X = 28
const GAP_Y = 18
const PAD = 14

interface GraphItem {
  node: WorkflowNode
  x: number
  y: number
}
interface GraphEdge {
  from: string
  to: string
  condition?: string
  x1: number
  y1: number
  x2: number
  y2: number
}
interface GraphLayout {
  width: number
  height: number
  cols: GraphItem[][]
  edges: GraphEdge[]
}

/** 按「最长路径分层」计算各节点所在列（层），再横向排布（决策分支自然分叉） */
function buildGraph(w: WorkflowDetail): GraphLayout {
  const startId = w.nodes.find((n) => n.type === 'start')?.id ?? w.nodes[0]?.id ?? ''
  const adj: Record<string, string[]> = {}
  for (const n of w.nodes) adj[n.id] = []
  for (const e of w.edges) {
    if (adj[e.from]) adj[e.from].push(e.to)
  }

  // 从 start 可达性 BFS
  const reach = new Set<string>()
  const queue = [startId]
  while (queue.length) {
    const u = queue.shift() as string
    if (reach.has(u)) continue
    reach.add(u)
    for (const v of adj[u] ?? []) queue.push(v)
  }

  // Kahn 拓扑排序（仅可达子图）
  const indeg: Record<string, number> = {}
  for (const n of w.nodes) indeg[n.id] = 0
  for (const e of w.edges) {
    if (reach.has(e.from) && reach.has(e.to)) indeg[e.to] = (indeg[e.to] ?? 0) + 1
  }
  const order: string[] = []
  const seed = Array.from(reach).filter((id) => indeg[id] === 0)
  const visited = new Set<string>()
  const pending = [...seed]
  while (pending.length) {
    const u = pending.shift() as string
    if (visited.has(u)) continue
    visited.add(u)
    order.push(u)
    for (const v of adj[u] ?? []) {
      indeg[v] = (indeg[v] ?? 0) - 1
      if (indeg[v] === 0) pending.push(v)
    }
  }

  // 最长路径分层
  const layer: Record<string, number> = {}
  for (const id of order) layer[id] = 0
  for (const u of order) {
    for (const v of adj[u] ?? []) {
      layer[v] = Math.max(layer[v] ?? 0, (layer[u] ?? 0) + 1)
    }
  }

  const maxLayer = Math.max(0, ...w.nodes.map((n) => layer[n.id] ?? 0))
  const cols: GraphItem[][] = []
  for (let l = 0; l <= maxLayer; l++) {
    cols.push(
      w.nodes
        .filter((n) => (layer[n.id] ?? -1) === l)
        .map((node) => ({ node, x: 0, y: 0 })),
    )
  }

  const maxRows = Math.max(1, ...cols.map((c) => c.length))
  const width = PAD * 2 + (maxLayer + 1) * NODE_W + maxLayer * GAP_X
  const height = PAD * 2 + maxRows * NODE_H + (maxRows - 1) * GAP_Y
  for (let c = 0; c <= maxLayer; c++) {
    const items = cols[c]
    const blockH = items.length * NODE_H + (items.length - 1) * GAP_Y
    const startY = PAD + (height - blockH) / 2
    items.forEach((it, r) => {
      it.x = PAD + c * (NODE_W + GAP_X)
      it.y = startY + r * (NODE_H + GAP_Y)
    })
  }

  const pos = (id: string): GraphItem | undefined => {
    for (const c of cols) {
      const found = c.find((it) => it.node.id === id)
      if (found) return found
    }
    return undefined
  }

  const edges: GraphEdge[] = []
  for (const e of w.edges) {
    const u = pos(e.from)
    const v = pos(e.to)
    if (!u || !v) continue
    edges.push({
      from: e.from,
      to: e.to,
      condition: e.condition,
      x1: u.x + NODE_W,
      y1: u.y + NODE_H / 2,
      x2: v.x,
      y2: v.y + NODE_H / 2,
    })
  }

  return { width, height, cols, edges }
}

const graph = computed<GraphLayout | null>(() => (activeWf.value ? buildGraph(activeWf.value) : null))
</script>

<template>
  <div class="workflow-center">
    <!-- 顶部汇总统计 -->
    <div class="stats-row">
      <template v-if="wf.loading && !wf.details.length">
        <Skeleton v-for="i in 4" :key="i" :rows="2" class="stat-skel" />
      </template>
      <template v-else>
        <div class="stat-card">
          <div class="stat-label">工作流总数</div>
          <div class="stat-value">{{ wf.details.length }}</div>
          <div class="stat-hint">预置模板 + 自定义</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">已启用</div>
          <div class="stat-value" style="color: var(--sf-success)">{{ wf.enabled.length }}/{{ wf.details.length }}</div>
          <div class="stat-hint">总览总开关已映射</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">运行中</div>
          <div class="stat-value" style="color: var(--sf-info)">
            {{ wf.running.length }}
          </div>
          <div class="stat-hint">含模拟运行</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">最近失败</div>
          <div class="stat-value" :style="{ color: wf.failed.length ? 'var(--sf-danger)' : 'var(--sf-warning)' }">
            {{ wf.failed.length }}
          </div>
          <div class="stat-hint">已回显为资源告警</div>
        </div>
      </template>
    </div>

    <!-- 理念提示条 -->
    <div class="notice-bar">
      <SfIcon name="magic" :size="14" />
      <span>
        工作流是 Agent 执行链路：总览驾驶舱可一键启停全部工作流；Agent 配置页可指派 Agent 到节点；
        运行异常会回显为资源管理页告警。数据由 mock 驱动，点击「运行一次」可查看模拟执行。
      </span>
      <button type="button" class="btn ghost refresh-btn" @click="refresh">
        <SfIcon name="refresh" :size="13" :class="{ spin: wf.loading }" /> 刷新
      </button>
    </div>

    <!-- 工作流卡片列表 -->
    <div class="section-head">
      <div class="toolbar-title">预置工作流模板</div>
      <span class="toolbar-hint">共 {{ wf.details.length }} 个 · 已启用 {{ wf.enabled.length }} 个</span>
    </div>

    <div v-if="wf.loading && !wf.details.length" class="wf-grid">
      <Skeleton v-for="i in 4" :key="i" :rows="10" class="wf-skel" />
    </div>
    <div v-else class="wf-grid">
      <article v-for="w in wf.details" :key="w.id" class="wf-card" :class="{ disabled: !w.enabled }">
        <header class="wf-head">
          <div class="wf-title">
            <SfIcon name="workflow" :size="15" class="wf-icon" />
            <span class="wf-name">{{ w.name }}</span>
            <StatusBadge
              :label="wf.running.includes(w) ? '运行中' : w.enabled ? '已启用' : '已停用'"
              :tone="wf.running.includes(w) ? 'info' : w.enabled ? 'success' : 'muted'"
            />
          </div>
          <button
            type="button"
            class="switch"
            :class="{ on: w.enabled }"
            :title="w.enabled ? '停用该工作流' : '启用该工作流'"
            @click="toggleWf(w)"
          >
            <span class="knob" />
          </button>
        </header>

        <p class="wf-desc">{{ w.description }}</p>

        <div class="wf-trigger">
          <SfIcon name="clock" :size="12" />
          <span>{{ w.trigger }}</span>
        </div>

        <!-- 节点链路缩略（横向流程示意） -->
        <div class="card-graph" :title="`${w.nodes.length} 个节点（点击「详情」查看完整状态机图）`">
          <template v-for="(n, i) in w.nodes" :key="n.id">
            <span class="graph-pill" :class="`k-${n.type}`">{{ n.name }}</span>
            <span v-if="i < w.nodes.length - 1" class="graph-arrow">→</span>
          </template>
        </div>

        <div class="wf-links">
          <div class="link-group">
            <span class="link-label"><SfIcon name="agent" :size="12" /> Agent</span>
            <div class="chips">
              <span v-for="id in agentsOf(w)" :key="id" class="chip agent">{{ agentName(id) }}</span>
            </div>
          </div>
          <div class="link-group">
            <span class="link-label"><SfIcon name="database" :size="12" /> 工具链</span>
            <div class="chips">
              <span v-for="k in toolsOf(w)" :key="k" class="chip tool">{{ toolLabel(k) }}</span>
            </div>
          </div>
        </div>

        <footer class="wf-foot">
          <span class="last-run">
            <template v-if="lastRun(w)">
              <StatusBadge :label="runLabel[lastRun(w)!.status]" :tone="runTone[lastRun(w)!.status]" />
              <span class="run-time">{{ formatDateTime(lastRun(w)!.started_at) }}</span>
            </template>
            <template v-else>
              <span class="run-empty">暂无运行记录</span>
            </template>
          </span>
          <span class="wf-actions">
            <a class="link-btn" @click="openDetail(w.id)">
              <SfIcon name="external" :size="13" /> 详情
            </a>
            <button
              type="button"
              class="btn primary run-btn"
              :disabled="!w.enabled"
              :title="w.enabled ? '运行一次（模拟）' : '请先启用该工作流'"
              @click="runNow(w)"
            >
              <SfIcon name="send" :size="12" /> 运行一次
            </button>
          </span>
        </footer>
      </article>
    </div>

    <!-- 详情抽屉 -->
    <Drawer :open="detailOpen" :width="860" :title="activeWf ? activeWf.name : '工作流详情'" @close="detailOpen = false">
      <template v-if="activeWf && graph">
        <div class="detail-head">
          <div class="detail-title">
            <span class="detail-desc">{{ activeWf.description }}</span>
            <StatusBadge
              :label="wf.running.includes(activeWf) ? '运行中' : activeWf.enabled ? '已启用' : '已停用'"
              :tone="wf.running.includes(activeWf) ? 'info' : activeWf.enabled ? 'success' : 'muted'"
            />
          </div>
          <button
            type="button"
            class="switch"
            :class="{ on: activeWf.enabled }"
            @click="toggleWf(activeWf)"
          >
            <span class="knob" />
          </button>
        </div>

        <section class="detail-sec">
          <h4 class="sec-title"><SfIcon name="clock" :size="13" /> 触发条件</h4>
          <div class="trigger-box">{{ activeWf.trigger }}</div>
        </section>

        <section class="detail-sec">
          <h4 class="sec-title"><SfIcon name="workflow" :size="13" /> 节点图（LangGraph 状态机）</h4>
          <div class="graph-legend">
            <span v-for="t in (['start', 'agent', 'tool', 'decision', 'end'] as const)" :key="t" class="legend-item">
              <span class="legend-dot" :class="`k-${t}`" /> {{ typeLabel[t] }}
            </span>
          </div>
          <div class="graph-scroll">
            <div class="graph-wrap" :style="{ width: `${graph.width}px`, height: `${graph.height}px` }">
              <svg class="graph-svg" :width="graph.width" :height="graph.height" :viewBox="`0 0 ${graph.width} ${graph.height}`">
                <defs>
                  <marker id="wf-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--sf-border-strong, #94a3b8)" />
                  </marker>
                </defs>
                <g v-for="e in graph.edges" :key="`${e.from}-${e.to}`">
                  <line
                    class="graph-edge"
                    :x1="e.x1"
                    :y1="e.y1"
                    :x2="e.x2"
                    :y2="e.y2"
                    marker-end="url(#wf-arrow)"
                  />
                  <text
                    v-if="e.condition"
                    class="graph-cond"
                    :x="(e.x1 + e.x2) / 2"
                    :y="(e.y1 + e.y2) / 2 - 5"
                  >
                    {{ e.condition }}
                  </text>
                </g>
              </svg>
              <div v-for="(col, ci) in graph.cols" :key="ci" class="graph-layer">
                <div
                  v-for="it in col"
                  :key="it.node.id"
                  class="graph-node"
                  :class="[`k-${it.node.type}`, { running: it.node.status === 'running' }]"
                  :style="{ left: `${it.x}px`, top: `${it.y}px`, width: `${NODE_W}px`, height: `${NODE_H}px` }"
                  :title="it.node.description"
                >
                  <span class="node-name">{{ it.node.name }}</span>
                  <span class="node-type">{{ typeLabel[it.node.type] }}</span>
                  <span v-if="it.node.type === 'agent' && it.node.agent_id" class="node-agent">
                    {{ agentName(it.node.agent_id) }}
                  </span>
                  <span v-if="it.node.type === 'tool' && it.node.tool_keys" class="node-tools">
                    {{ it.node.tool_keys.map(toolLabel).join(' / ') }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="detail-sec">
          <h4 class="sec-title"><SfIcon name="agent" :size="13" /> Agent 绑定（可指派）</h4>
          <div class="bind-list">
            <div v-for="node in agentNodes" :key="node.id" class="bind-row">
              <span class="bind-node">{{ node.name }}</span>
              <span class="bind-arrow">→</span>
              <select
                class="bind-select"
                :value="activeWf.agent_bindings[node.id] ?? ''"
                @change="assignNode(node.id, ($event.target as HTMLSelectElement).value)"
              >
                <option v-for="a in agents.agents" :key="a.id" :value="a.id">
                  {{ a.name }}（{{ a.id }}）
                </option>
              </select>
            </div>
          </div>
          <div class="bind-note">
            <SfIcon name="link" :size="12" />
            指派后同步更新 Agent 侧「绑定工作流」，与 Agent 配置页保持一致
          </div>
        </section>

        <section class="detail-sec">
          <h4 class="sec-title"><SfIcon name="database" :size="13" /> 工具链</h4>
          <div class="tool-list">
            <div v-for="(keys, nodeId) in activeWf.tool_chain" :key="nodeId" class="tool-row">
              <span class="tool-node">{{ activeWf.nodes.find((n) => n.id === nodeId)?.name ?? nodeId }}</span>
              <span class="chips">
                <span v-for="k in keys" :key="k" class="chip tool">{{ toolLabel(k) }}</span>
              </span>
            </div>
          </div>
        </section>

        <section class="detail-sec">
          <h4 class="sec-title"><SfIcon name="term" :size="13" /> 运行历史 / 日志（{{ activeWf.history.length }} 条）</h4>
          <div v-if="!activeWf.history.length" class="hist-empty">
            暂无运行记录，点击下方「立即运行」触发一次模拟执行
          </div>
          <div v-else class="hist-list">
            <div v-for="h in activeWf.history" :key="h.id" class="hist-item" :class="h.status">
              <div class="hist-top">
                <span class="hist-id">{{ h.id }}</span>
                <StatusBadge :label="runLabel[h.status]" :tone="runTone[h.status]" />
                <span class="hist-time">
                  {{ formatDateTime(h.started_at) }}{{ h.ended_at ? ` → ${formatDateTime(h.ended_at)}` : '' }}
                </span>
              </div>
              <div class="hist-out">{{ h.output_summary ?? '—' }}</div>
              <div v-if="h.error_message" class="hist-err">
                <SfIcon name="alert" :size="12" /> {{ h.error_message }}
              </div>
            </div>
          </div>
        </section>

        <div class="detail-foot">
          <button
            type="button"
            class="btn primary"
            :disabled="!activeWf.enabled"
            :title="activeWf.enabled ? '运行一次（模拟）' : '请先启用该工作流'"
            @click="runNow(activeWf)"
          >
            <SfIcon name="send" :size="13" /> 立即运行
          </button>
          <button type="button" class="btn ghost" @click="detailOpen = false">关闭</button>
        </div>
      </template>
    </Drawer>

    <AIFloatingAssistant context="workflows" />
  </div>
</template>

<style scoped>
.workflow-center {
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

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-top: 2px;
}
.toolbar-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--sf-text-secondary);
}
.toolbar-hint {
  font-size: 12px;
  color: var(--sf-text-faint);
}

/* 卡片列表 */
.wf-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: var(--sf-space-3);
  align-items: start;
}
.wf-skel {
  height: 300px;
}
.wf-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  box-shadow: var(--sf-shadow);
  transition: opacity 0.2s ease;
}
.wf-card.disabled {
  opacity: 0.66;
}
.wf-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.wf-title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 14px;
  font-weight: 600;
  color: var(--sf-text);
  min-width: 0;
  flex-wrap: wrap;
}
.wf-icon {
  color: var(--sf-primary);
  flex-shrink: 0;
}
.wf-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.wf-desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.55;
  color: var(--sf-text-secondary);
}
.wf-trigger {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--sf-text-faint);
}
.wf-trigger .sf-icon {
  margin-top: 2px;
  flex-shrink: 0;
}

/* 卡片节点链路缩略 */
.card-graph {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  padding: 8px 10px;
  border: 1px dashed var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-bg);
}
.graph-pill {
  padding: 2px 7px;
  border-radius: 8px;
  font-size: 11px;
  line-height: 16px;
  white-space: nowrap;
  max-width: 108px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.k-start {
  color: var(--sf-info);
  background: var(--sf-info-soft);
}
.k-agent {
  color: var(--sf-success);
  background: var(--sf-success-soft);
}
.k-tool {
  color: var(--sf-warning);
  background: var(--sf-warning-soft);
}
.k-decision {
  color: var(--sf-danger);
  background: var(--sf-danger-soft);
}
.k-end {
  color: var(--sf-text-secondary);
  background: var(--sf-bg);
  border: 1px solid var(--sf-border);
}
.graph-arrow {
  color: var(--sf-text-faint);
  font-size: 11px;
}

/* Agent / 工具链 */
.wf-links {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.link-group {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12px;
}
.link-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--sf-text-faint);
  flex-shrink: 0;
  padding-top: 2px;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.chip {
  padding: 1px 8px;
  border-radius: 9px;
  font-size: 11px;
  line-height: 17px;
  white-space: nowrap;
}
.chip.agent {
  color: var(--sf-success);
  background: var(--sf-success-soft);
}
.chip.tool {
  color: var(--sf-warning);
  background: var(--sf-warning-soft);
}

.wf-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border-top: 1px solid var(--sf-border);
  padding-top: 10px;
}
.last-run {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--sf-text-faint);
  min-width: 0;
}
.run-empty {
  color: var(--sf-text-faint);
}
.wf-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.link-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--sf-primary);
  cursor: pointer;
  user-select: none;
}
.link-btn:hover {
  text-decoration: underline;
}
.run-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 详情抽屉 */
.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.detail-title {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.detail-desc {
  font-size: 13px;
  color: var(--sf-text-secondary);
  line-height: 1.6;
}

.detail-sec {
  margin-top: 4px;
  margin-bottom: 16px;
}
.sec-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--sf-text);
}
.trigger-box {
  padding: 10px 12px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-bg);
  font-size: 12px;
  line-height: 1.6;
  color: var(--sf-text-secondary);
}

/* 节点图 */
.graph-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 11px;
  color: var(--sf-text-faint);
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 3px;
}
.graph-scroll {
  overflow-x: auto;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-bg);
  padding: 6px 0;
}
.graph-wrap {
  position: relative;
  margin: 0 auto;
}
.graph-svg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.graph-edge {
  stroke: var(--sf-border-strong, #94a3b8);
  stroke-width: 1.5;
}
.graph-cond {
  fill: var(--sf-text-faint);
  font-size: 10px;
  text-anchor: middle;
  paint-order: stroke;
  stroke: var(--sf-surface);
  stroke-width: 3px;
}
.graph-layer {
  position: absolute;
  inset: 0;
}
.graph-node {
  position: absolute;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 1px;
  padding: 5px 8px;
  border: 1px solid var(--sf-border);
  border-radius: 9px;
  background: var(--sf-surface);
  box-shadow: var(--sf-shadow-sm);
  overflow: hidden;
  text-align: center;
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
}
.graph-node .node-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--sf-text);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.graph-node .node-type {
  font-size: 10px;
  color: var(--sf-text-faint);
}
.graph-node .node-agent,
.graph-node .node-tools {
  font-size: 9px;
  color: var(--sf-text-faint);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.graph-node.running {
  border-color: var(--sf-info);
  box-shadow: 0 0 0 2px var(--sf-info-soft), var(--sf-shadow);
}

/* Agent 绑定 */
.bind-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.bind-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.bind-node {
  font-size: 12px;
  font-weight: 600;
  color: var(--sf-text);
  min-width: 96px;
}
.bind-arrow {
  color: var(--sf-text-faint);
}
.bind-select {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text);
  font-size: 12px;
}
.bind-note {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 11px;
  color: var(--sf-text-faint);
}

/* 工具链 */
.tool-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.tool-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
}
.tool-node {
  font-size: 12px;
  font-weight: 600;
  color: var(--sf-text);
  min-width: 96px;
}

/* 运行历史 */
.hist-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.hist-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 10px 12px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
}
.hist-item.failed {
  border-left: 3px solid var(--sf-danger);
}
.hist-item.success {
  border-left: 3px solid var(--sf-success);
}
.hist-item.running {
  border-left: 3px solid var(--sf-info);
  background: var(--sf-info-soft);
}
.hist-top {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.hist-id {
  font-size: 11px;
  font-weight: 700;
  color: var(--sf-text-faint);
  font-variant-numeric: tabular-nums;
}
.hist-time {
  font-size: 11px;
  color: var(--sf-text-faint);
  margin-left: auto;
}
.hist-out {
  font-size: 12px;
  color: var(--sf-text-secondary);
  line-height: 1.55;
}
.hist-err {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  font-size: 12px;
  color: var(--sf-danger);
}
.hist-empty {
  padding: 26px 0;
  text-align: center;
  font-size: 12px;
  color: var(--sf-text-faint);
}

.detail-foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--sf-border);
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

@media (max-width: 1100px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .wf-grid {
    grid-template-columns: 1fr;
  }
}
</style>