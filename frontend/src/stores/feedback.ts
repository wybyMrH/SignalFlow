import { reactive, ref } from 'vue'
import { defineStore } from 'pinia'

import { autoApproveByAI, generateAIReplyDraft } from '@/api/ai'
import { fetchFeedbackList, fetchFeedbackStats, updateFeedbackStatus } from '@/api/feedback'
import type { FeedbackListQuery, FeedbackStats, FeedbackStatus, FeedbackView } from '@/types'

/**
 * 反馈管理状态（FS-2 数据层，mock 驱动）。
 * 查询条件与后端 GET /feedbacks 契约对齐；状态流转回写本地列表。
 * AI 能力扩展：AI 生成回复草稿、AI 自动审批。
 */
export const useFeedbackStore = defineStore('feedback', () => {
  const query = reactive<FeedbackListQuery>({
    source: '',
    status: '',
    keyword: '',
    topic_id: undefined,
    page: 1,
    page_size: 20,
  })

  const items = ref<FeedbackView[]>([])
  const total = ref(0)
  const loading = ref(false)

  /** 总览页待处理快捷列表（独立于查询条件，不影响反馈管理页筛选） */
  const pendingItems = ref<FeedbackView[]>([])
  const pendingLoading = ref(false)

  /** AI 操作状态 */
  const aiDraftLoading = ref<string | null>(null)
  const aiApproveLoading = ref<string | null>(null)
  const aiDrafts = ref<Record<string, string>>({})

  /** 反馈状态统计 */
  const stats = ref<FeedbackStats | null>(null)
  const statsLoading = ref(false)

  async function fetchPage() {
    loading.value = true
    try {
      const data = await fetchFeedbackList({ ...query })
      items.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchPending(limit = 6) {
    pendingLoading.value = true
    try {
      const data = await fetchFeedbackList({ status: 'new', page: 1, page_size: limit })
      pendingItems.value = data.items
    } finally {
      pendingLoading.value = false
    }
  }

  async function fetchStats() {
    statsLoading.value = true
    try {
      stats.value = await fetchFeedbackStats()
    } finally {
      statsLoading.value = false
    }
  }

  function setFilter(patch: Partial<FeedbackListQuery>) {
    if (!('page' in patch)) patch.page = 1
    Object.assign(query, patch)
  }

  async function setStatus(id: string, status: FeedbackStatus, reviewer?: string, replyContent?: string | null) {
    const row = await updateFeedbackStatus(id, status, reviewer, replyContent)
    const i = items.value.findIndex((r) => r.id === id)
    if (i >= 0) items.value[i] = row
    const p = pendingItems.value.findIndex((r) => r.id === id)
    if (p >= 0) pendingItems.value[p] = row
  }

  /** AI 生成回复草稿 */
  async function generateReply(id: string, content: string) {
    aiDraftLoading.value = id
    try {
      const draft = await generateAIReplyDraft(content)
      aiDrafts.value[id] = draft
      await setStatus(id, 'ai_reviewing', 'AI助手')
    } finally {
      aiDraftLoading.value = null
    }
  }

  /** AI 自动审批：自动生成统一话术并标记 AI 已回复 */
  async function autoApprove(id: string, content: string) {
    aiApproveLoading.value = id
    try {
      const { reply, status } = await autoApproveByAI(id, content)
      aiDrafts.value[id] = reply
      await setStatus(id, status, 'AI自动审批')
    } finally {
      aiApproveLoading.value = null
    }
  }

  /** 清除 AI 草稿 */
  function clearDraft(id: string) {
    delete aiDrafts.value[id]
  }

  return {
    query, items, total, loading,
    pendingItems, pendingLoading,
    aiDraftLoading, aiApproveLoading, aiDrafts,
    stats, statsLoading,
    fetchPage, fetchPending, fetchStats, setFilter, setStatus,
    generateReply, autoApprove, clearDraft,
  }
})