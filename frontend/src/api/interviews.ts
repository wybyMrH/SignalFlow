import http from './http'
import { useMock } from './mock'
import { getInterviewRecords, getInterviewSummary, getResourceHealth, mockDelay } from '@/mocks'
import type { InterviewExtraction, InterviewRecord, InterviewSummary, ResourceHealth } from '@/types'

/** 获取客户访谈记录列表 */
export async function fetchInterviewRecords(): Promise<InterviewRecord[]> {
  if (useMock()) {
    return mockDelay(getInterviewRecords(), 280)
  }
  const { data } = await http.get<InterviewRecord[]>('/interviews')
  return data
}

/** 获取客户访谈统计总览 */
export async function fetchInterviewSummary(): Promise<InterviewSummary> {
  if (useMock()) {
    return mockDelay(getInterviewSummary(), 160)
  }
  const { data } = await http.get<InterviewSummary>('/interviews/summary')
  return data
}

/** 对指定访谈执行 AI 提炼（模拟从录音/纪要中提炼痛点与需求） */
export async function runInterviewExtraction(id: string): Promise<InterviewExtraction> {
  if (useMock()) {
    const record = getInterviewRecords().find((r) => r.id === id)
    if (!record) throw new Error('interview not found')
    return mockDelay(
      {
        pain_points: ['批量建号运维成本高', '希望角色级权限模板'],
        needs: ['批量账号导入', '角色分组授权', '成员活跃度报表'],
        cooperation_intent: 'high' as const,
        matched_needs: ['批量账号与角色管理'],
        lead_candidate: true,
        lead_reason: '访谈中明确提及批量账号与角色分组能力，形成高意向合作线索',
        extracted_at: new Date().toISOString(),
      } satisfies InterviewExtraction,
      900,
    )
  }
  const { data } = await http.post<InterviewExtraction>(`/interviews/${id}/extract`)
  return data
}

/** 获取资源健康概况（总览驾驶舱展示用） */
export async function fetchResourceHealth(): Promise<ResourceHealth> {
  if (useMock()) {
    return mockDelay(getResourceHealth(), 200)
  }
  const { data } = await http.get<ResourceHealth>('/resources/health')
  return data
}