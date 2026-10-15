import http from './http'
import { useMock } from './mock'
import { getWorkflowDetails, mockDelay } from '@/mocks'
import type { WorkflowDetail } from '@/types'

/**
 * 获取工作流详情列表（节点图 / 触发条件 / Agent 绑定 / 工具链 / 运行历史）。
 * 真实后端契约对应 GET /workflows（本阶段 mock 驱动）。
 * 总览「工作流运行状态」、Agent 配置页绑定、资源管理页告警复用同一数据源，实现闭环。
 */
export async function fetchWorkflowDetails(): Promise<WorkflowDetail[]> {
  if (useMock()) {
    return mockDelay(getWorkflowDetails(), 320)
  }
  const { data } = await http.get<WorkflowDetail[]>('/workflows')
  return data
}