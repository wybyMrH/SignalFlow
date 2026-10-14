/**
 * Mock 系统设置页数据：渠道接入状态与说明。
 */

import type { SettingsView } from '@/types'
import { sourceLabels } from '@/utils/labels'

export function buildSettingsView(): SettingsView {
  return {
    mock_mode: true,
    channels: [
      { key: 'ticket', label: sourceLabels.ticket, enabled: true, connected: true, last_sync: '2026-10-14T18:30:00Z', incoming: 12, note: '工单系统已对接' },
      { key: 'portal', label: sourceLabels.portal, enabled: true, connected: true, last_sync: '2026-10-14T18:30:00Z', incoming: 9, note: '门户留言已对接' },
      { key: 'review', label: sourceLabels.review, enabled: true, connected: true, last_sync: '2026-10-14T18:20:00Z', incoming: 7, note: '评价中心已对接' },
      { key: 'hotline', label: sourceLabels.hotline, enabled: true, connected: true, last_sync: '2026-10-14T18:15:00Z', incoming: 11, note: '热线录音转写待接 LLM' },
      { key: 'interview', label: sourceLabels.interview, enabled: true, connected: false, last_sync: null, incoming: 0, note: '访谈为线下导入，未接自动同步' },
      { key: 'sales', label: sourceLabels.sales, enabled: false, connected: false, last_sync: null, incoming: 0, note: '商务侧反馈待开通' },
    ],
    ai_note: '本阶段洞察由模拟工作流生成；接入 LiteLLM 网关后切换真实 LLM 输出。',
    auth_note: '政务版统一身份认证接入位已预留，本阶段不启用登录。',
    updated_at: new Date().toISOString(),
  }
}