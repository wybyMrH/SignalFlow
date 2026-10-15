import http from './http'
import { useMock } from './mock'
import { getResourceDetail, mockDelay } from '@/mocks'
import type { ResourceDetail } from '@/types'

/**
 * 获取资源管理详情（服务器/数据库/API/日志/告警）。
 * 真实后端契约对应 GET /resources/overview（本阶段 mock 驱动）。
 * 总览「资源健康」卡与资源管理页共用同一数据源，展示与运维配置闭环。
 */
export async function fetchResourceDetail(): Promise<ResourceDetail> {
  if (useMock()) {
    return mockDelay(getResourceDetail(), 320)
  }
  const { data } = await http.get<ResourceDetail>('/resources/overview')
  return data
}