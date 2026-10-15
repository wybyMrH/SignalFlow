import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchWorkflowDetails } from '@/api/workflows'
import { useAgentsStore } from '@/stores/agents'
import type { WorkflowDetail } from '@/types'

/**
 * 工作流配置 store：预置工作流模板 + 启停开关 + 模拟运行。
 * 理念：总览驾驶舱的「工作流启用状态」、工作流配置页开关与 Agent 绑定共用同一数据源，
 * 运行异常会回显到资源管理页告警，形成「展示 → 配置 → 执行 → 观测」闭环。
 */
export const useWorkflowsStore = defineStore('workflows', () => {
  const details = ref<WorkflowDetail[]>([])
  const loading = ref(false)
  const lastError = ref<string | null>(null)

  const enabled = computed(() => details.value.filter((w) => w.enabled))
  const disabled = computed(() => details.value.filter((w) => !w.enabled))
  /** 存在运行中历史的工作流 */
  const running = computed(() =>
    details.value.filter((w) => w.history.some((h) => h.status === 'running')),
  )
  /** 最近一次运行失败的工作流（用于资源管理页回显告警） */
  const failed = computed(() =>
    details.value.filter((w) => w.history.some((h) => h.status === 'failed')),
  )

  function byId(id: string): WorkflowDetail | undefined {
    return details.value.find((w) => w.id === id)
  }

  async function fetchAll(force = false) {
    if (!force && details.value.length) {
      // mock 阶段避免已配置状态（开关/绑定/模拟运行历史）被重复拉取覆盖，
      // 保证「总览开关 → 配置页 → 资源告警」同源闭环在 SPA 导航内真实保留。
      return details.value
    }
    loading.value = true
    try {
      details.value = await fetchWorkflowDetails()
      lastError.value = null
    } catch (e) {
      lastError.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  /** 启停工作流（总览总开关与配置页开关共用，真实映射） */
  function toggleEnabled(id: string) {
    const w = byId(id)
    if (w) w.enabled = !w.enabled
  }

  /** 总览总开关：一键启用/停用全部工作流，映射每个工作流的实际启用状态 */
  function toggleAll(allOn: boolean) {
    for (const w of details.value) w.enabled = allOn
  }

  /**
   * 将 Agent 指派到工作流节点：同步更新工作流绑定与 Agent 侧 bound_workflow_ids，
   * 使「Agent 配置页 ↔ 工作流配置页」双向保持一致。
   */
  function assignNodeAgent(workflowId: string, nodeId: string, agentId: string) {
    const w = byId(workflowId)
    if (!w || !agentId) return
    const node = w.nodes.find((n) => n.id === nodeId)
    if (!node) return
    node.agent_id = agentId
    w.agent_bindings = { ...w.agent_bindings, [nodeId]: agentId }
    w.updated_at = new Date().toISOString()

    const agentsStore = useAgentsStore()
    const agent = agentsStore.agents.find((a) => a.id === agentId)
    if (agent && !agent.bound_workflow_ids.includes(workflowId)) {
      agent.bound_workflow_ids.push(workflowId)
    }
  }

  /** 模拟运行一次工作流：先追加 running 历史，随后落地为 success（可运行的模拟案例） */
  function simulateRun(id: string) {
    const w = byId(id)
    if (!w || !w.enabled) return
    const runId = `R-${Date.now().toString().slice(-8)}`
    w.history.unshift({
      id: runId,
      started_at: new Date().toISOString(),
      status: 'running',
      output_summary: '节点任务执行中…',
    })
    for (const n of w.nodes) {
      if (n.type !== 'start' && n.type !== 'end') n.status = 'running'
    }
    window.setTimeout(() => {
      const run = w.history.find((h) => h.id === runId)
      if (run) {
        run.ended_at = new Date().toISOString()
        run.status = 'success'
        run.output_summary = `模拟执行完成：${w.nodes
          .filter((n) => n.type === 'agent')
          .map((n) => n.name)
          .join(' → ')} 节点已按配置顺序执行`
      }
      for (const n of w.nodes) {
        if (n.type !== 'start' && n.type !== 'end') n.status = 'success'
      }
    }, 1800)
  }

  return {
    details,
    loading,
    lastError,
    enabled,
    disabled,
    running,
    failed,
    byId,
    fetchAll,
    toggleEnabled,
    toggleAll,
    assignNodeAgent,
    simulateRun,
  }
})