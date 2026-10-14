import http from './http'
import { useMock } from './mock'
import { createFeedback as mockCreate, getFeedback as mockGet, listFeedbacks as mockList, mockDelay, updateFeedbackStatus as mockUpdate } from '@/mocks'
import type { Feedback, FeedbackCreate, FeedbackListQuery, FeedbackStatus, FeedbackView, Paged } from '@/types'

/** 反馈列表（分页 + 筛选），对应 GET /feedbacks */
export async function fetchFeedbackList(query: FeedbackListQuery = {}): Promise<Paged<FeedbackView>> {
  if (useMock()) {
    return mockDelay(mockList(query))
  }
  const { data } = await http.get<Paged<FeedbackView>>('/feedbacks', { params: query })
  return data
}

/** 反馈详情，对应 GET /feedbacks/{id} */
export async function fetchFeedback(id: string): Promise<Feedback> {
  if (useMock()) {
    const row = mockGet(id)
    if (!row) return Promise.reject(new Error('反馈不存在'))
    return mockDelay(row)
  }
  const { data } = await http.get<Feedback>(`/feedbacks/${id}`)
  return data
}

/** 创建反馈，对应 POST /feedbacks */
export async function createFeedback(payload: FeedbackCreate): Promise<Feedback> {
  if (useMock()) {
    return mockDelay(mockCreate(payload))
  }
  const { data } = await http.post<Feedback>('/feedbacks', payload)
  return data
}

/** 反馈状态流转，对应 PATCH /feedbacks/{id}/status */
export async function updateFeedbackStatus(id: string, status: FeedbackStatus, reviewer?: string): Promise<FeedbackView> {
  if (useMock()) {
    const row = mockUpdate(id, status, reviewer)
    if (!row) return Promise.reject(new Error('反馈不存在'))
    return mockDelay(row)
  }
  const { data } = await http.patch<FeedbackView>(`/feedbacks/${id}/status`, { status, reviewer })
  return data
}