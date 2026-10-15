import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  fetchAIAutomationRules,
  fetchAIWelcome,
  fetchAIWorkflows,
  sendAIChatMessage,
  fetchAutoClassification,
  fetchDedupGroups,
  fetchPriorityRules,
  fetchPriorityAdjustments,
  fetchAutomationSummary,
  fetchBusinessLeads,
  fetchIndustryShares,
  fetchMarketSignals,
  fetchCommonNeeds,
  fetchBusinessInsightSummary,
} from '@/api/ai'
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
  IndustryShare,
  MarketSignal,
  PriorityAdjustment,
  PriorityRule,
} from '@/types'

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

  // 自动化中心
  const classificationResults = ref<AutoClassificationResult[]>([])
  const dedupGroups = ref<DedupGroup[]>([])
  const priorityRules = ref<PriorityRule[]>([])
  const priorityAdjustments = ref<PriorityAdjustment[]>([])
  const automationSummary = ref<AutomationExecutionSummary | null>(null)

  const classificationLoading = ref(false)
  const dedupLoading = ref(false)
  const priorityRulesLoading = ref(false)
  const adjustmentsLoading = ref(false)
  const summaryLoading = ref(false)

  // 商务洞察
  const businessLeads = ref<BusinessLead[]>([])
  const industryShares = ref<IndustryShare[]>([])
  const marketSignals = ref<MarketSignal[]>([])
  const commonNeeds = ref<CommonNeed[]>([])
  const businessSummary = ref<BusinessInsightSummary | null>(null)

  const leadsLoading = ref(false)
  const industriesLoading = ref(false)
  const signalsLoading = ref(false)
  const needsLoading = ref(false)
  const businessSummaryLoading = ref(false)

  const runningWorkflows = computed(() => workflows.value.filter((w) => w.status === 'running'))
  const completedToday = computed(() => workflows.value.filter((w) => w.status === 'completed').length)

  const reviewQueue = computed(() => classificationResults.value.filter((r) => r.needs_review))
  const pendingDedupGroups = computed(() => dedupGroups.value.filter((g) => g.status === 'pending'))
  const enabledPriorityRules = computed(() => priorityRules.value.filter((r) => r.enabled))

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

  // 自动化中心 actions
  async function fetchClassification() {
    classificationLoading.value = true
    try {
      classificationResults.value = await fetchAutoClassification()
    } finally {
      classificationLoading.value = false
    }
  }

  async function fetchDedup() {
    dedupLoading.value = true
    try {
      dedupGroups.value = await fetchDedupGroups()
    } finally {
      dedupLoading.value = false
    }
  }

  async function fetchPriorityRuleList() {
    priorityRulesLoading.value = true
    try {
      priorityRules.value = await fetchPriorityRules()
    } finally {
      priorityRulesLoading.value = false
    }
  }

  async function fetchAdjustments() {
    adjustmentsLoading.value = true
    try {
      priorityAdjustments.value = await fetchPriorityAdjustments()
    } finally {
      adjustmentsLoading.value = false
    }
  }

  async function fetchAutomationSummaryData() {
    summaryLoading.value = true
    try {
      automationSummary.value = await fetchAutomationSummary()
    } finally {
      summaryLoading.value = false
    }
  }

  async function loadAutomationCenter() {
    await Promise.all([
      fetchClassification(),
      fetchDedup(),
      fetchPriorityRuleList(),
      fetchAdjustments(),
      fetchAutomationSummaryData(),
    ])
  }

  function togglePriorityRule(ruleId: string) {
    const rule = priorityRules.value.find((r) => r.id === ruleId)
    if (rule) rule.enabled = !rule.enabled
  }

  function resolveDedupGroup(groupId: string, action: 'merge' | 'dismiss') {
    const g = dedupGroups.value.find((x) => x.group_id === groupId)
    if (g) g.status = action === 'merge' ? 'merged' : 'dismissed'
  }

  function confirmClassification(feedbackId: string) {
    const r = classificationResults.value.find((x) => x.feedback_id === feedbackId)
    if (r) r.needs_review = false
  }

  // 商务洞察 actions
  async function fetchBusinessLeadsList() {
    leadsLoading.value = true
    try {
      businessLeads.value = await fetchBusinessLeads()
    } finally {
      leadsLoading.value = false
    }
  }

  async function fetchIndustryShareList() {
    industriesLoading.value = true
    try {
      industryShares.value = await fetchIndustryShares()
    } finally {
      industriesLoading.value = false
    }
  }

  async function fetchMarketSignalList() {
    signalsLoading.value = true
    try {
      marketSignals.value = await fetchMarketSignals()
    } finally {
      signalsLoading.value = false
    }
  }

  async function fetchCommonNeedList() {
    needsLoading.value = true
    try {
      commonNeeds.value = await fetchCommonNeeds()
    } finally {
      needsLoading.value = false
    }
  }

  async function fetchBusinessSummaryData() {
    businessSummaryLoading.value = true
    try {
      businessSummary.value = await fetchBusinessInsightSummary()
    } finally {
      businessSummaryLoading.value = false
    }
  }

  async function loadBusinessCenter() {
    await Promise.all([
      fetchBusinessLeadsList(),
      fetchIndustryShareList(),
      fetchMarketSignalList(),
      fetchCommonNeedList(),
      fetchBusinessSummaryData(),
    ])
  }

  function advanceLeadStage(leadId: string) {
    const lead = businessLeads.value.find((l) => l.id === leadId)
    if (!lead) return
    if (lead.stage === 'identified') lead.stage = 'qualified'
    else if (lead.stage === 'qualified') lead.stage = 'pushed'
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
    // 自动化中心
    classificationResults,
    dedupGroups,
    priorityRules,
    priorityAdjustments,
    automationSummary,
    classificationLoading,
    dedupLoading,
    priorityRulesLoading,
    adjustmentsLoading,
    summaryLoading,
    reviewQueue,
    pendingDedupGroups,
    enabledPriorityRules,
    fetchClassification,
    fetchDedup,
    fetchPriorityRuleList,
    fetchAdjustments,
    fetchAutomationSummaryData,
    loadAutomationCenter,
    togglePriorityRule,
    resolveDedupGroup,
    confirmClassification,
    // 商务洞察
    businessLeads,
    industryShares,
    marketSignals,
    commonNeeds,
    businessSummary,
    leadsLoading,
    industriesLoading,
    signalsLoading,
    needsLoading,
    businessSummaryLoading,
    fetchBusinessLeadsList,
    fetchIndustryShareList,
    fetchMarketSignalList,
    fetchCommonNeedList,
    fetchBusinessSummaryData,
    loadBusinessCenter,
    advanceLeadStage,
  }
})
