import http from './http'
import { useMock } from './mock'
import { computeDashboardMetrics as mockMetrics, mockDelay } from '@/mocks'
import type { DashboardMetrics } from '@/types'

/** 总览工作台指标，对应 GET /dashboard/metrics */
export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  if (useMock()) {
    return mockDelay(mockMetrics(), 260)
  }
  const { data } = await http.get<DashboardMetrics>('/dashboard/metrics')
  return data
}