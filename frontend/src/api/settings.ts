import http from './http'
import { useMock } from './mock'
import { buildSettingsView as mockSettings, mockDelay } from '@/mocks'
import type { SettingsView } from '@/types'

/** 系统设置视图，对应 GET /settings */
export async function fetchSettingsView(): Promise<SettingsView> {
  if (useMock()) {
    return mockDelay(mockSettings())
  }
  const { data } = await http.get<SettingsView>('/settings')
  return data
}