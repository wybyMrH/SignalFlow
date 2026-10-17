<script setup lang="ts">
/**
 * Agent 与 Skill 配置中心（position 3）：
 * 侧边栏「Agent 配置」入口对应的管理页。
 * 理念：总览驾驶舱的「Agent 启用状态」不是静态展示，而是映射到这里的真实启停；
 * 每个 Agent 可配置工具调用权限、绑定工作流、加载 Skill；可新建自定义 Agent。
 * 所有数据由 mock 驱动（VITE_USE_MOCK=false 无缝切真实后端）。
 */
import { computed, onMounted, ref } from 'vue'

import AIFloatingAssistant from '@/components/ai/AIFloatingAssistant.vue'
import Drawer from '@/components/common/Drawer.vue'
import SfIcon from '@/components/common/SfIcon.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { fetchAgentToolCatalog, fetchSkillCatalog, fetchWorkflowCatalog } from '@/api/agents'
import { useAgentsStore } from '@/stores/agents'
import { relativeDay } from '@/utils'
import type { AgentStatus, AgentToolDef, SkillDef, WorkflowCatalogItem } from '@/types'

const agentsStore = useAgentsStore()

const loading = ref(true)
const catalog = ref<AgentToolDef[]>([])
const skills = ref<SkillDef[]>([])
const workflows = ref<WorkflowCatalogItem[]>([])
const activeTab = ref<'agents' | 'skills'>('agents')

const skillLoading = ref(false)
const skillNewOpen = ref(false)
const newSkillName = ref('')
const newSkillCategory = ref('政务')
const newSkillDesc = ref('')

/** 新建 Agent 抽屉 */
const createOpen = ref(false)
const newName = ref('')
const newCategory = ref('回复生成')
const newScenario = ref('')
const newTools = ref<string[]>([])
const newWorkflows = ref<string[]>([])

/** 配置抽屉（编辑既有 Agent） */
const configOpen = ref(false)
const configAgent = ref<AgentStatus | null>(null)
const configTools = ref<string[]>([])
const configWorkflows = ref<string[]>([])
const configScenario = ref('')

const categoryTone: Record<string, 'info' | 'success' | 'warning' | 'neutral' | 'danger'> = {
  内容生成: 'info',
  回复生成: 'success',
  分析研判: 'warning',
  诉求处置: 'danger',
}

const toolCategoryOrder = ['检索', '生成', '分析', '处置', '通知']

/** 按类别分组工具目录 */
const groupedTools = computed(() => {
  const groups: Array<{ category: string; items: AgentToolDef[] }> = []
  for (const cat of toolCategoryOrder) {
    const items = catalog.value.filter((t) => t.category === cat)
    if (items.length) groups.push({ category: cat, items })
  }
  const rest = catalog.value.filter((t) => !toolCategoryOrder.includes(t.category))
  if (rest.length) groups.push({ category: '其他', items: rest })
  return groups
})

const workflowName = (id: string) => workflows.value.find((w) => w.id === id)?.name ?? id

function loadAll() {
  loading.value = true
  agentsStore.fetchAll().finally(() => {
    loading.value = false
  })
  fetchAgentToolCatalog().then((d) => (catalog.value = d))
  fetchWorkflowCatalog().then((d) => (workflows.value = d))
  fetchSkills()
}

async function fetchSkills() {
  skillLoading.value = true
  try {
    skills.value = await fetchSkillCatalog()
  } finally {
    skillLoading.value = false
  }
}

onMounted(loadAll)

function toggleAgent(a: AgentStatus) {
  agentsStore.toggleAgent(a.id)
}

function openCreate() {
  newName.value = ''
  newCategory.value = '回复生成'
  newScenario.value = ''
  newTools.value = []
  newWorkflows.value = []
  createOpen.value = true
}

function handleCreate() {
  const name = newName.value.trim()
  if (!name) return
  const nextNo = agentsStore.agents.length + 1
  const agent: AgentStatus = {
    id: `AG-${String(nextNo).padStart(3, '0')}`,
    name,
    category: newCategory.value,
    scenario: newScenario.value.trim() || '自定义业务场景，待补充说明',
    enabled: true,
    tools: catalog.value.filter((t) => newTools.value.includes(t.key)).map((t) => t.name),
    bound_workflow_ids: newWorkflows.value,
    run_count: 0,
    reliability: 100,
    last_run_at: undefined,
    preset: false,
  }
  agentsStore.agents.push(agent)
  createOpen.value = false
}

function openConfig(a: AgentStatus) {
  configAgent.value = a
  configTools.value = catalog.value.filter((t) => a.tools.includes(t.name)).map((t) => t.key)
  configWorkflows.value = [...a.bound_workflow_ids]
  configScenario.value = a.scenario || ''
  configOpen.value = true
}

function saveConfig() {
  const a = configAgent.value
  if (!a) return
  a.tools = catalog.value.filter((t) => configTools.value.includes(t.key)).map((t) => t.name)
  a.bound_workflow_ids = [...configWorkflows.value]
  a.scenario = configScenario.value.trim() || a.scenario
  configOpen.value = false
}

function toggleSkill(s: SkillDef) {
  s.enabled = !s.enabled
}

function handleCreateSkill() {
  const name = newSkillName.value.trim()
  if (!name) return
  skills.value.push({
    id: `SK-CUSTOM-${Date.now().toString().slice(-4)}`,
    name,
    category: newSkillCategory.value,
    description: newSkillDesc.value.trim() || '自定义能力包，待完善说明',
    enabled: true,
    owner_agent_ids: [],
  })
  newSkillName.value = ''
  newSkillDesc.value = ''
  skillNewOpen.value = false
}

const skillOwnerNames = (ids: string[]) =>
  ids
    .map((id) => agentsStore.agents.find((a) => a.id === id)?.name ?? id)
    .join('、') || '未指派 Agent'
</script>

<template>
  <div class="agent-center">
    <!-- 顶部汇总统计 -->
    <div class="stats-row">
      <template v-if="loading">
        <Skeleton v-for="i in 4" :key="i" :rows="2" class="stat-skel" />
      </template>
      <template v-else>
        <div class="stat-card">
          <div class="stat-label">Agent 总数</div>
          <div class="stat-value">{{ agentsStore.agents.length }}</div>
          <div class="stat-hint">预置 {{ agentsStore.agents.filter((a) => a.preset).length }} 个</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">已启用</div>
          <div class="stat-value" style="color: var(--sf-info)">{{ agentsStore.enabledAgents.length }}</div>
          <div class="stat-hint">总览开关同源映射</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">近 30 天执行</div>
          <div class="stat-value">{{ agentsStore.totalRunCount }}</div>
          <div class="stat-hint">Agent 任务累计</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">平均成功率</div>
          <div class="stat-value">{{ agentsStore.avgReliability }}%</div>
          <div class="stat-hint">近 30 天口径</div>
        </div>
      </template>
    </div>

    <!-- 理念提示条 -->
    <div class="notice-bar">
      <SfIcon name="magic" :size="14" />
      <span>
        Agent/Skill 不是孤立展示：总览的「启用 Agent」开关映射到这里；每个 Agent 可配置工具权限、绑定工作流与加载
        Skill，形成「展示 → 配置 → 执行」闭环。
      </span>
    </div>

    <!-- Tab 切换 -->
    <div class="tabs">
      <button type="button" class="tab-btn" :class="{ active: activeTab === 'agents' }" @click="activeTab = 'agents'">
        <SfIcon name="agent" :size="14" /> Agent 管理
      </button>
      <button type="button" class="tab-btn" :class="{ active: activeTab === 'skills' }" @click="activeTab = 'skills'">
        <SfIcon name="magic" :size="14" /> Skill 目录
      </button>
    </div>

    <!-- Agent 管理 -->
    <template v-if="activeTab === 'agents'">
      <div class="page-toolbar">
        <div class="toolbar-title">预置与自定义 Agent</div>
        <button type="button" class="btn primary" @click="openCreate">
          <SfIcon name="plus" :size="14" /> 新建 Agent
        </button>
      </div>

      <div v-if="loading" class="agent-grid">
        <Skeleton v-for="i in 6" :key="i" :rows="6" class="agent-skel" />
      </div>
      <div v-else class="agent-grid">
        <article v-for="a in agentsStore.agents" :key="a.id" class="agent-card" :class="{ disabled: !a.enabled }">
          <header class="agent-card-head">
            <div class="agent-id">
              <SfIcon name="agent" :size="18" />
              <span>{{ a.name }}</span>
              <StatusBadge v-if="a.preset" label="预置" tone="muted" />
              <StatusBadge v-else label="自定义" tone="info" />
            </div>
            <button
              type="button"
              class="switch"
              :class="{ on: a.enabled }"
              :title="a.enabled ? '点击停用' : '点击启用'"
              @click="toggleAgent(a)"
            >
              <span class="knob" />
            </button>
          </header>
          <div class="agent-meta">
            <StatusBadge :label="a.category" :tone="categoryTone[a.category] ?? 'neutral'" />
            <span class="run-info">{{ a.run_count }} 次 / 近 30 天</span>
          </div>
          <p class="agent-scenario">{{ a.scenario }}</p>

          <div class="agent-section">
            <div class="section-label">工具权限</div>
            <div class="tool-chips">
              <span v-for="t in a.tools" :key="t" class="tool-chip">{{ t }}</span>
              <span v-if="!a.tools.length" class="tool-empty">未配置工具</span>
            </div>
          </div>

          <div class="agent-section">
            <div class="section-label">绑定工作流</div>
            <div class="wf-chips">
              <span v-for="w in a.bound_workflow_ids" :key="w" class="wf-chip">
                <SfIcon name="workflow" :size="10" /> {{ workflowName(w) }}
              </span>
              <span v-if="!a.bound_workflow_ids.length" class="tool-empty">未绑定</span>
            </div>
          </div>

          <footer class="agent-card-foot">
            <div class="agent-foot-stats">
              <span>成功率 <b class="num">{{ a.reliability }}%</b></span>
              <span v-if="a.last_run_at" class="last-run">最近 {{ relativeDay(a.last_run_at) }}</span>
              <span v-else class="last-run">未运行</span>
            </div>
            <button type="button" class="btn ghost" @click="openConfig(a)">
              <SfIcon name="settings" :size="13" /> 配置
            </button>
          </footer>
        </article>
      </div>
    </template>

    <!-- Skill 目录 -->
    <template v-else>
      <div class="page-toolbar">
        <div class="toolbar-title">领域能力包（Skill）</div>
        <button type="button" class="btn primary" @click="skillNewOpen = true">
          <SfIcon name="plus" :size="14" /> 新建 Skill
        </button>
      </div>

      <div v-if="skillLoading" class="skill-list">
        <Skeleton v-for="i in 5" :key="i" :rows="3" class="skill-skel" />
      </div>
      <div v-else class="skill-list">
        <article v-for="s in skills" :key="s.id" class="skill-item" :class="{ disabled: !s.enabled }">
          <div class="skill-icon"><SfIcon name="magic" :size="18" /></div>
          <div class="skill-main">
            <div class="skill-title">
              {{ s.name }}
              <StatusBadge :label="s.category" tone="info" />
            </div>
            <p class="skill-desc">{{ s.description }}</p>
            <div class="skill-owner">
              <SfIcon name="agent" :size="11" /> 已指派：{{ skillOwnerNames(s.owner_agent_ids) }}
            </div>
          </div>
          <button
            type="button"
            class="switch"
            :class="{ on: s.enabled }"
            :title="s.enabled ? '点击停用' : '点击启用'"
            @click="toggleSkill(s)"
          >
            <span class="knob" />
          </button>
        </article>
      </div>
    </template>

    <!-- 新建 Agent 抽屉 -->
    <Drawer :open="createOpen" title="新建 Agent" @close="createOpen = false">
      <form class="drawer-form" @submit.prevent="handleCreate">
        <label class="field">
          <span class="field-label">Agent 名称</span>
          <input v-model="newName" type="text" placeholder="如：采购寻源 Agent" required />
        </label>
        <label class="field">
          <span class="field-label">业务分类</span>
          <select v-model="newCategory">
            <option value="内容生成">内容生成</option>
            <option value="回复生成">回复生成</option>
            <option value="分析研判">分析研判</option>
            <option value="诉求处置">诉求处置</option>
          </select>
        </label>
        <label class="field">
          <span class="field-label">适用场景</span>
          <textarea v-model="newScenario" rows="3" placeholder="描述该 Agent 负责的业务场景与边界" />
        </label>
        <fieldset class="field">
          <span class="field-label">工具权限（可多选）</span>
          <div class="check-grid">
            <label v-for="t in catalog" :key="t.key" class="check-item">
              <input v-model="newTools" type="checkbox" :value="t.key" />
              <span>{{ t.name }}</span>
            </label>
            <span v-if="!catalog.length" class="tool-empty">工具目录加载中…</span>
          </div>
        </fieldset>
        <fieldset class="field">
          <span class="field-label">绑定工作流（可多选）</span>
          <div class="check-grid">
            <label v-for="w in workflows" :key="w.id" class="check-item">
              <input v-model="newWorkflows" type="checkbox" :value="w.id" />
              <span>{{ w.name }}</span>
            </label>
            <span v-if="!workflows.length" class="tool-empty">工作流目录加载中…</span>
          </div>
        </fieldset>
        <div class="drawer-actions">
          <button type="button" class="btn ghost" @click="createOpen = false">取消</button>
          <button type="submit" class="btn primary" :disabled="!newName.trim()">创建</button>
        </div>
      </form>
    </Drawer>

    <!-- 配置 Agent 抽屉 -->
    <Drawer :open="configOpen" :title="`配置 ${configAgent?.name ?? ''}`" :width="560" @close="configOpen = false">
      <div v-if="configAgent" class="drawer-form">
        <label class="field">
          <span class="field-label">角色提示词（scenario）</span>
          <textarea
            v-model="configScenario"
            rows="5"
            placeholder="定义该 Agent 的角色、职责边界与输出要求..."
          />
          <span class="field-hint">提示词影响该 Agent 在分类、研判与生成回复时的行为边界。</span>
        </label>
        <div class="field">
          <span class="field-label">工具调用权限</span>
          <div v-for="g in groupedTools" :key="g.category" class="tool-group">
            <div class="tool-group-label">{{ g.category }}</div>
            <label v-for="t in g.items" :key="t.key" class="check-item">
              <input v-model="configTools" type="checkbox" :value="t.key" />
              <span class="check-name">{{ t.name }}</span>
              <span class="check-desc">{{ t.description }}</span>
            </label>
          </div>
        </div>
        <div class="field">
          <span class="field-label">绑定工作流（LangGraph 节点指派）</span>
          <div class="check-grid">
            <label v-for="w in workflows" :key="w.id" class="check-item">
              <input v-model="configWorkflows" type="checkbox" :value="w.id" />
              <span>{{ w.name }}</span>
            </label>
          </div>
        </div>
        <div class="drawer-actions">
          <button type="button" class="btn ghost" @click="configOpen = false">取消</button>
          <button type="button" class="btn primary" @click="saveConfig">保存配置</button>
        </div>
      </div>
    </Drawer>

    <!-- 新建 Skill 抽屉 -->
    <Drawer :open="skillNewOpen" title="新建 Skill" @close="skillNewOpen = false">
      <form class="drawer-form" @submit.prevent="handleCreateSkill">
        <label class="field">
          <span class="field-label">Skill 名称</span>
          <input v-model="newSkillName" type="text" placeholder="如：督办提醒 Skill" required />
        </label>
        <label class="field">
          <span class="field-label">领域</span>
          <select v-model="newSkillCategory">
            <option value="政务">政务</option>
            <option value="商务">商务</option>
            <option value="分析">分析</option>
            <option value="回复生成">回复生成</option>
            <option value="诉求处置">诉求处置</option>
          </select>
        </label>
        <label class="field">
          <span class="field-label">能力说明</span>
          <textarea v-model="newSkillDesc" rows="3" placeholder="描述该能力包解决的问题与输出" />
        </label>
        <div class="drawer-actions">
          <button type="button" class="btn ghost" @click="skillNewOpen = false">取消</button>
          <button type="submit" class="btn primary" :disabled="!newSkillName.trim()">创建</button>
        </div>
      </form>
    </Drawer>

    <AIFloatingAssistant context="agents" />
  </div>
</template>

<style scoped>
.agent-center {
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
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--sf-radius-sm);
  background: var(--sf-primary-soft);
  border: 1px solid var(--sf-primary-border);
  color: var(--sf-primary);
  font-size: 12px;
  line-height: 1.5;
}

.tabs {
  display: flex;
  gap: 6px;
  border-bottom: 1px solid var(--sf-border);
  padding-bottom: 0;
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

.page-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.toolbar-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--sf-text-secondary);
}

/* Agent 网格 */
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: var(--sf-space-3);
}
.agent-skel {
  height: 240px;
}
.agent-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  box-shadow: var(--sf-shadow);
  transition: opacity 0.15s ease;
}
.agent-card.disabled {
  opacity: 0.62;
}
.agent-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.agent-id {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--sf-text);
  min-width: 0;
}
.agent-id span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.agent-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.run-info {
  font-size: 12px;
  color: var(--sf-text-faint);
}
.agent-scenario {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--sf-text-secondary);
}
.agent-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.section-label {
  font-size: 11px;
  color: var(--sf-text-faint);
}
.tool-chips,
.wf-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.tool-chip {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  color: var(--sf-info);
  background: var(--sf-info-soft);
}
.wf-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  color: var(--sf-primary);
  background: var(--sf-primary-soft);
}
.tool-empty {
  font-size: 11px;
  color: var(--sf-text-faint);
}
.agent-card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--sf-border);
  padding-top: 10px;
}
.agent-foot-stats {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--sf-text-secondary);
}
.agent-foot-stats b {
  color: var(--sf-text);
}
.last-run {
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

/* Skill 列表 */
.skill-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
}
.skill-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  box-shadow: var(--sf-shadow);
  transition: opacity 0.15s ease;
}
.skill-item.disabled {
  opacity: 0.62;
}
.skill-icon {
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
.skill-main {
  flex: 1;
  min-width: 0;
}
.skill-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--sf-text);
}
.skill-desc {
  margin: 4px 0;
  font-size: 12px;
  color: var(--sf-text-secondary);
  line-height: 1.5;
}
.skill-owner {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--sf-text-faint);
}
.skill-skel {
  height: 84px;
}

/* 抽屉表单 */
.drawer-form {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  border: none;
  padding: 0;
  margin: 0;
}
.field-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--sf-text-secondary);
}
.field input[type='text'],
.field select,
.field textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text);
  font-size: 13px;
  box-sizing: border-box;
}
.field textarea {
  resize: vertical;
  min-height: 60px;
}
.check-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}
.check-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 8px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  font-size: 12px;
  color: var(--sf-text);
  cursor: pointer;
  background: var(--sf-surface);
}
.tool-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}
.tool-group-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--sf-text-faint);
}
.check-name {
  flex-shrink: 0;
}
.check-desc {
  color: var(--sf-text-faint);
  line-height: 1.4;
}
.field-hint {
  font-size: 11px;
  color: var(--sf-text-faint);
  line-height: 1.4;
}
.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--sf-border);
}

/* 按钮 */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 12px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.btn:hover {
  border-color: var(--sf-primary-border);
}
.btn.primary {
  background: var(--sf-primary);
  border-color: var(--sf-primary);
  color: #fff;
}
.btn.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn.ghost {
  background: transparent;
  border-color: transparent;
  color: var(--sf-text-secondary);
}
.btn.ghost:hover {
  color: var(--sf-primary);
  background: var(--sf-primary-soft);
}

@media (max-width: 1100px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>