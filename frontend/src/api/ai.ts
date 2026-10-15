import http from './http'
import { useMock } from './mock'
import { getAIAutomationRules, getAIWorkflows, sendAIChat, getAIWelcomeMessage, mockDelay, generateAIReply, getAIReplySuggestion } from '@/mocks'
import type {
  AIAutomationRule,
  AIChatMessage,
  AIWorkflowStatus,
  AutoClassificationResult,
  AutomationExecutionSummary,
  BusinessInsightSummary,
  BusinessLead,
  CommonNeed,
  DedupGroup,
  FeedbackStatus,
  IndustryShare,
  MarketSignal,
  PriorityAdjustment,
  PriorityRule,
} from '@/types'

/** 获取 AI 工作流运行状态 */
export async function fetchAIWorkflows(): Promise<AIWorkflowStatus[]> {
  if (useMock()) {
    return mockDelay(getAIWorkflows(), 260)
  }
  const { data } = await http.get<AIWorkflowStatus[]>('/ai/workflows')
  return data
}

/** 获取 AI 自动化规则列表 */
export async function fetchAIAutomationRules(): Promise<AIAutomationRule[]> {
  if (useMock()) {
    return mockDelay(getAIAutomationRules(), 200)
  }
  const { data } = await http.get<AIAutomationRule[]>('/ai/automation-rules')
  return data
}

/** 发送 AI 对话消息，返回助手回复 */
export async function sendAIChatMessage(
  query: string,
  history: AIChatMessage[],
): Promise<AIChatMessage> {
  if (useMock()) {
    return sendAIChat(query, history)
  }
  const { data } = await http.post<AIChatMessage>('/ai/chat', { query, history })
  return data
}

/** 获取 AI 欢迎语 */
export async function fetchAIWelcome(): Promise<AIChatMessage> {
  if (useMock()) {
    return mockDelay(getAIWelcomeMessage(), 120)
  }
  const { data } = await http.get<AIChatMessage>('/ai/chat/welcome')
  return data
}

/** AI 生成回复草稿（基于知识库/政策库查询） */
export async function generateAIReplyDraft(content: string): Promise<string> {
  if (useMock()) {
    return generateAIReply(content)
  }
  const { data } = await http.post<string>('/ai/reply-draft', { content })
  return data
}

/** AI 气泡助手：获取回复建议 */
export async function fetchAIReplySuggestion(content: string): Promise<string> {
  if (useMock()) {
    return getAIReplySuggestion(content)
  }
  const { data } = await http.post<string>('/ai/reply-suggestion', { content })
  return data
}

/** AI 自动审批：对重复/无用提问自动统一话术回复 */
export async function autoApproveByAI(id: string, content: string): Promise<{ reply: string; status: FeedbackStatus }> {
  if (useMock()) {
    const reply = await generateAIReply(content)
    return mockDelay({ reply, status: 'ai_replied' as FeedbackStatus }, 600)
  }
  const { data } = await http.post<{ reply: string; status: FeedbackStatus }>(`/ai/auto-approve/${id}`, { content })
  return data
}

/** 获取自动分类结果列表 */
export async function fetchAutoClassification(): Promise<AutoClassificationResult[]> {
  if (useMock()) {
    const { getAutoClassificationResults } = await import('@/mocks/ai')
    return mockDelay(getAutoClassificationResults(), 340)
  }
  const { data } = await http.get<AutoClassificationResult[]>('/ai/automation/classification')
  return data
}

/** 获取去重合并组列表 */
export async function fetchDedupGroups(): Promise<DedupGroup[]> {
  if (useMock()) {
    const { getDedupGroups } = await import('@/mocks/ai')
    return mockDelay(getDedupGroups(), 280)
  }
  const { data } = await http.get<DedupGroup[]>('/ai/automation/dedup')
  return data
}

/** 获取优先级规则列表 */
export async function fetchPriorityRules(): Promise<PriorityRule[]> {
  if (useMock()) {
    const { getPriorityRules } = await import('@/mocks/ai')
    return mockDelay(getPriorityRules(), 220)
  }
  const { data } = await http.get<PriorityRule[]>('/ai/automation/priority-rules')
  return data
}

/** 获取优先级调整记录 */
export async function fetchPriorityAdjustments(): Promise<PriorityAdjustment[]> {
  if (useMock()) {
    const { getPriorityAdjustments } = await import('@/mocks/ai')
    return mockDelay(getPriorityAdjustments(), 260)
  }
  const { data } = await http.get<PriorityAdjustment[]>('/ai/automation/priority-adjustments')
  return data
}

/** 获取自动化执行概览 */
export async function fetchAutomationSummary(): Promise<AutomationExecutionSummary> {
  if (useMock()) {
    const { getAutomationExecutionSummary } = await import('@/mocks/ai')
    return mockDelay(getAutomationExecutionSummary(), 180)
  }
  const { data } = await http.get<AutomationExecutionSummary>('/ai/automation/summary')
  return data
}

/** 获取企业合作线索列表 */
export async function fetchBusinessLeads(): Promise<BusinessLead[]> {
  if (useMock()) {
    const { getBusinessLeads } = await import('@/mocks/ai')
    return mockDelay(getBusinessLeads(), 300)
  }
  const { data } = await http.get<BusinessLead[]>('/ai/business/leads')
  return data
}

/** 获取行业分布 */
export async function fetchIndustryShares(): Promise<IndustryShare[]> {
  if (useMock()) {
    const { getIndustryShares } = await import('@/mocks/ai')
    return mockDelay(getIndustryShares(), 240)
  }
  const { data } = await http.get<IndustryShare[]>('/ai/business/industries')
  return data
}

/** 获取市场动向信号 */
export async function fetchMarketSignals(): Promise<MarketSignal[]> {
  if (useMock()) {
    const { getMarketSignals } = await import('@/mocks/ai')
    return mockDelay(getMarketSignals(), 260)
  }
  const { data } = await http.get<MarketSignal[]>('/ai/business/signals')
  return data
}

/** 获取共性需求归纳 */
export async function fetchCommonNeeds(): Promise<CommonNeed[]> {
  if (useMock()) {
    const { getCommonNeeds } = await import('@/mocks/ai')
    return mockDelay(getCommonNeeds(), 220)
  }
  const { data } = await http.get<CommonNeed[]>('/ai/business/common-needs')
  return data
}

/** 获取商务洞察总览 */
export async function fetchBusinessInsightSummary(): Promise<BusinessInsightSummary> {
  if (useMock()) {
    const { getBusinessInsightSummary } = await import('@/mocks/ai')
    return mockDelay(getBusinessInsightSummary(), 160)
  }
  const { data } = await http.get<BusinessInsightSummary>('/ai/business/summary')
  return data
}
