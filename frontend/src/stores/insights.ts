import { ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchDashboardMetrics } from '@/api/dashboard'
import { createTaskApi, fetchInsightDashboard, fetchRoadmapBoard, updateDraftStatusApi, updateTaskStatusApi } from '@/api/insights'
import type { DashboardMetrics, DraftStatus, InsightDashboard, RoadmapBoard, TaskStatus } from '@/types'

/**
 * 洞察与决策状态（FS-1 总览指标 + FS-3 洞察看板 + FS-4 路线图，mock 驱动）。
 * 页面组件只消费本 store，不直接调用 api；按页面切片拆分独立加载器，避免无关数据联动。
 */
export const useInsightsStore = defineStore('insights', () => {
  const metrics = ref<DashboardMetrics | null>(null)
  const dashboard = ref<InsightDashboard | null>(null)
  const roadmap = ref<RoadmapBoard | null>(null)

  const metricsLoading = ref(false)
  const dashboardLoading = ref(false)
  const roadmapLoading = ref(false)

  async function fetchMetrics() {
    metricsLoading.value = true
    try {
      metrics.value = await fetchDashboardMetrics()
    } finally {
      metricsLoading.value = false
    }
  }

  async function fetchDashboard() {
    dashboardLoading.value = true
    try {
      dashboard.value = await fetchInsightDashboard()
    } finally {
      dashboardLoading.value = false
    }
  }

  async function fetchRoadmap() {
    roadmapLoading.value = true
    try {
      roadmap.value = await fetchRoadmapBoard()
    } finally {
      roadmapLoading.value = false
    }
  }

  /** FS-4：从洞察主题创建任务 */
  async function createTask(input: { roadmap_id: string; title: string; owner: string; priority: number }) {
    const task = await createTaskApi(input)
    if (roadmap.value) {
      roadmap.value.tasks.unshift(task)
      const item = roadmap.value.items.find((r) => r.id === input.roadmap_id)
      if (item) item.task_count = roadmap.value.tasks.filter((t) => t.roadmap_id === item.id).length
    }
    return task
  }

  /** FS-4：任务状态流转 */
  async function changeTaskStatus(taskId: string, status: TaskStatus) {
    const updated = await updateTaskStatusApi(taskId, status)
    if (roadmap.value) {
      const i = roadmap.value.tasks.findIndex((t) => t.id === taskId)
      if (i >= 0) roadmap.value.tasks[i] = updated
    }
    return updated
  }

  /** FS-5：回复草稿状态流转（sent 时 mock 同步回写反馈为 replied） */
  async function changeDraftStatus(draftId: string, status: DraftStatus) {
    const updated = await updateDraftStatusApi(draftId, status)
    if (roadmap.value) {
      const i = roadmap.value.drafts.findIndex((d) => d.id === draftId)
      if (i >= 0) roadmap.value.drafts[i] = updated
    }
    return updated
  }

  return {
    metrics,
    dashboard,
    roadmap,
    metricsLoading,
    dashboardLoading,
    roadmapLoading,
    fetchMetrics,
    fetchDashboard,
    fetchRoadmap,
    createTask,
    changeTaskStatus,
    changeDraftStatus,
  }
})