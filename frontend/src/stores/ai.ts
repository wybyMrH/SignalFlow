import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  fetchAIAutomationRules,
  fetchAIWelcome,
  fetchAIWorkflows,
  sendAIChatMessage,
} from '@/api/ai'
import type { AIAutomationRule, AIChatMessage, AIWorkflowStatus } from '@/types'

/**
 * AI 工作台状态：工作流状态、自动化规则、对话历史。
 * 独立的 AI store，避免与 insights/feedback store 耦合。
 */
export const useAIStore = defineStore('ai', () => {
  const workflows = ref<AIWorkflowStatus[]>([])
  const rules = ref<AIAutomationRule[]>([])
  const messages = ref<AIChatMessage[]>([])

  const workflowsLoading = ref(false)
  const rulesLoading = ref(false)
  const chatLoading = ref(false)

  const runningWorkflows = computed(() => workflows.value.filter((w) => w.status === 'running'))
  const completedToday = computed(() => workflows.value.filter((w) => w.status === 'completed').length)

  async function fetchWorkflows() {
    workflowsLoading.value = true
    try {
      workflows.value = await fetchAIWorkflows()
    } finally {
      workflowsLoading.value = false
    }
  }

  async function fetchRules() {
    rulesLoading.value = true
    try {
      rules.value = await fetchAIAutomationRules()
    } finally {
      rulesLoading.value = false
    }
  }

  async function initChat() {
    if (messages.value.length === 0) {
      const welcome = await fetchAIWelcome()
      messages.value.push(welcome)
    }
  }

  async function sendMessage(query: string) {
    const userMsg: AIChatMessage = {
      id: `msg-u-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    }
    messages.value.push(userMsg)
    chatLoading.value = true
    try {
      const reply = await sendAIChatMessage(query, messages.value)
      messages.value.push(reply)
    } finally {
      chatLoading.value = false
    }
  }

  function toggleRule(ruleId: string) {
    const rule = rules.value.find((r) => r.id === ruleId)
    if (rule) rule.enabled = !rule.enabled
  }

  return {
    workflows,
    rules,
    messages,
    workflowsLoading,
    rulesLoading,
    chatLoading,
    runningWorkflows,
    completedToday,
    fetchWorkflows,
    fetchRules,
    initChat,
    sendMessage,
    toggleRule,
  }
})
