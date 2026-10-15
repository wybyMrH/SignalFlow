import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchAgentStatuses } from '@/api/agents'
import type { AgentStatus } from '@/types'

/**
 * Agent 中心 store：预置 Agent 列表 + 启停开关。
 * 理念：总览驾驶舱的「Agent 启用状态」与「Agent 配置中心」开关共享同一数据源，
 * 总览看到的开关状态就是真实的 Agent 启停状态，实现「展示 → 配置 → 执行」闭环。
 */
export const useAgentsStore = defineStore('agents', () => {
  const agents = ref<AgentStatus[]>([])
  const loading = ref(false)

  const enabledAgents = computed(() => agents.value.filter((a) => a.enabled))
  const disabledAgents = computed(() => agents.value.filter((a) => !a.enabled))
  const totalRunCount = computed(() => agents.value.reduce((s, a) => s + a.run_count, 0))
  const avgReliability = computed(() => {
    if (!agents.value.length) return 0
    return Math.round(agents.value.reduce((s, a) => s + a.reliability, 0) / agents.value.length)
  })

  async function fetchAll(force = false) {
    if (!force && agents.value.length) {
      // mock 阶段避免已配置状态（Agent 启停/绑定）被重复拉取覆盖，
      // 保证「总览 ↔ 配置中心 ↔ 工作流节点指派」同源闭环。
      return agents.value
    }
    loading.value = true
    try {
      agents.value = await fetchAgentStatuses()
    } finally {
      loading.value = false
    }
  }

  /** 开关 Agent（总览与配置中心联动：总览开关真实映射到 Agent 启停） */
  function toggleAgent(id: string) {
    const a = agents.value.find((x) => x.id === id)
    if (a) a.enabled = !a.enabled
  }

  return {
    agents,
    loading,
    enabledAgents,
    disabledAgents,
    totalRunCount,
    avgReliability,
    fetchAll,
    toggleAgent,
  }
})