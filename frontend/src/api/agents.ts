import http from './http'
import { useMock } from './mock'
import { getAgentStatuses, getAgentToolCatalog, getSkillCatalog, getWorkflowCatalog, mockDelay } from '@/mocks'
import type { AgentStatus, AgentToolDef, SkillDef, WorkflowCatalogItem } from '@/types'

/**
 * 获取预置 Agent 列表。
 * 总览驾驶舱「Agent 与工作流」状态卡与「Agent 配置中心」共用；
 * 真实后端契约对应 GET /agents（本阶段 mock 驱动）。
 */
export async function fetchAgentStatuses(): Promise<AgentStatus[]> {
  if (useMock()) {
    return mockDelay(getAgentStatuses(), 220)
  }
  const { data } = await http.get<AgentStatus[]>('/agents')
  return data
}

/** 获取 Agent 可配置工具目录（真实契约 GET /agents/tools） */
export async function fetchAgentToolCatalog(): Promise<AgentToolDef[]> {
  if (useMock()) {
    return mockDelay(getAgentToolCatalog(), 120)
  }
  const { data } = await http.get<AgentToolDef[]>('/agents/tools')
  return data
}

/** 获取工作流目录（Agent 绑定工作流用；真实契约 GET /workflows/catalog） */
export async function fetchWorkflowCatalog(): Promise<WorkflowCatalogItem[]> {
  if (useMock()) {
    return mockDelay(getWorkflowCatalog(), 120)
  }
  const { data } = await http.get<WorkflowCatalogItem[]>('/workflows/catalog')
  return data
}

/** 获取 Skill 目录（Agent 可加载能力包；真实契约 GET /skills/catalog） */
export async function fetchSkillCatalog(): Promise<SkillDef[]> {
  if (useMock()) {
    return mockDelay(getSkillCatalog(), 120)
  }
  const { data } = await http.get<SkillDef[]>('/skills/catalog')
  return data
}