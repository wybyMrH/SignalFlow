import http from './http'
import { useMock } from './mock'
import { buildGovOverview as mockGov, mockDelay } from '@/mocks'
import type { GovOverview } from '@/types'

/** 政务适配总览，对应 GET /gov/overview */
export async function fetchGovOverview(): Promise<GovOverview> {
  if (useMock()) {
    return mockDelay(mockGov())
  }
  const { data } = await http.get<GovOverview>('/gov/overview')
  return data
}