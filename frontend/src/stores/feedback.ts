import { reactive, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchFeedbackList, updateFeedbackStatus } from '@/api/feedback'
import type { FeedbackListQuery, FeedbackStatus, FeedbackView } from '@/types'

/**
 * 反馈管理状态（FS-2 数据层，mock 驱动）。
 * 查询条件与后端 GET /feedbacks 契约对齐；状态流转回写本地列表。
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

  function setFilter(patch: Partial<FeedbackListQuery>) {
    if (!('page' in patch)) patch.page = 1
    Object.assign(query, patch)
  }

  async function setStatus(id: string, status: FeedbackStatus, reviewer?: string) {
    const row = await updateFeedbackStatus(id, status, reviewer)
    const i = items.value.findIndex((r) => r.id === id)
    if (i >= 0) items.value[i] = row
    const p = pendingItems.value.findIndex((r) => r.id === id)
    if (p >= 0) pendingItems.value[p] = row
  }

  return { query, items, total, loading, pendingItems, pendingLoading, fetchPage, fetchPending, setFilter, setStatus }
})