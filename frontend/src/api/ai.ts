import http from './http'
import { useMock } from './mock'
import { getAIAutomationRules, getAIWorkflows, sendAIChat, getAIWelcomeMessage, mockDelay, generateAIReply, getAIReplySuggestion } from '@/mocks'
import type { AIAutomationRule, AIChatMessage, AIWorkflowStatus, FeedbackStatus } from '@/types'

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
