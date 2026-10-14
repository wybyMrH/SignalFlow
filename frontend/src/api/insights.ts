import http from './http'
import { useMock } from './mock'
import {
  buildRoadmapBoard as mockRoadmap,
  createTask as mockCreateTask,
  mockDelay,
  updateDraftStatus as mockUpdateDraft,
  updateTaskStatus as mockUpdateTask,
} from '@/mocks'
import type { DraftStatus, InsightDashboard, ReplyDraft, RoadmapBoard, TaskItem, TaskStatus } from '@/types'
import { computeInsightDashboard as mockInsights } from '@/mocks/topics'

/** 洞察看板（主题/痛点/优先级），对应 GET /insights */
export async function fetchInsightDashboard(): Promise<InsightDashboard> {
  if (useMock()) {
    return mockDelay(mockInsights(), 320)
  }
  const { data } = await http.get<InsightDashboard>('/insights')
  return data
}

/** 路线图看板，对应 GET /roadmap/board */
export async function fetchRoadmapBoard(): Promise<RoadmapBoard> {
  if (useMock()) {
    return mockDelay(mockRoadmap())
  }
  const { data } = await http.get<RoadmapBoard>('/roadmap/board')
  return data
}

/** 新建任务，对应 POST /roadmap/tasks */
export async function createTaskApi(input: { roadmap_id: string; title: string; owner: string; priority: number }): Promise<TaskItem> {
  if (useMock()) {
    return mockDelay(mockCreateTask(input))
  }
  const { data } = await http.post<TaskItem>('/roadmap/tasks', input)
  return data
}

/** 任务状态流转，对应 PATCH /roadmap/tasks/{id}/status */
export async function updateTaskStatusApi(taskId: string, status: TaskStatus): Promise<TaskItem> {
  if (useMock()) {
    const row = mockUpdateTask(taskId, status)
    if (!row) return Promise.reject(new Error('任务不存在'))
    return mockDelay(row)
  }
  const { data } = await http.patch<TaskItem>(`/roadmap/tasks/${taskId}/status`, { status })
  return data
}

/** 草稿状态流转（含发送回写反馈），对应 PATCH /roadmap/drafts/{id}/status */
export async function updateDraftStatusApi(draftId: string, status: DraftStatus): Promise<ReplyDraft> {
  if (useMock()) {
    const row = mockUpdateDraft(draftId, status)
    if (!row) return Promise.reject(new Error('草稿不存在'))
    return mockDelay(row)
  }
  const { data } = await http.patch<ReplyDraft>(`/roadmap/drafts/${draftId}/status`, { status })
  return data
}