import http from './http'
import { useMock } from './mock'
import { buildSettingsView as mockSettings, mockDelay } from '@/mocks'
import type { SettingsView, LLMConfig, EmailConfig, AppearanceConfig, GlobalModelParams } from '@/types'

/** 系统设置视图，对应 GET /settings */
export async function fetchSettingsView(): Promise<SettingsView> {
  if (useMock()) {
    return mockDelay(mockSettings())
  }
  const { data } = await http.get<SettingsView>('/settings')
  return data
}

/** 更新 LLM / API 配置 */
export async function updateLLMConfig(payload: Partial<LLMConfig>): Promise<void> {
  if (useMock()) {
    await mockDelay(null, 300)
    return
  }
  await http.put('/settings/llm', payload)
}

/** 更新邮件提醒配置 */
export async function updateEmailConfig(payload: Partial<EmailConfig>): Promise<void> {
  if (useMock()) {
    await mockDelay(null, 300)
    return
  }
  await http.put('/settings/email', payload)
}

/** 更新外观 / AI 气泡主题 */
export async function updateAppearanceConfig(payload: Partial<AppearanceConfig>): Promise<void> {
  if (useMock()) {
    await mockDelay(null, 300)
    return
  }
  await http.put('/settings/appearance', payload)
}

/** 更新全局模型微调参数 */
export async function updateGlobalModelParams(payload: Partial<GlobalModelParams>): Promise<void> {
  if (useMock()) {
    await mockDelay(null, 300)
    return
  }
  await http.put('/settings/global-model-params', payload)
}

/** 切换渠道启用 / 停用 */
export async function toggleChannel(key: string): Promise<{ code: string; message: string; data: { key: string; enabled: boolean; connected: boolean } }> {
  if (useMock()) {
    await mockDelay(null, 300)
    return { code: 'SUCCESS', message: '渠道状态已切换', data: { key, enabled: true, connected: true } }
  }
  const { data } = await http.put(`/settings/channels/${key}/toggle`)
  return data
}

