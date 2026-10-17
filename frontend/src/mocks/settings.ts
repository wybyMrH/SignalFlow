/**
 * Mock 系统设置页数据：渠道接入状态与全量配置分区。
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
    llm: {
      provider: 'openai',
      model: 'gpt-4o-mini',
      api_key_mask: '••••••sk12',
      temperature: 0.2,
      max_tokens: 2048,
      timeout_seconds: 60,
    },
    email: {
      enabled: false,
      smtp_server: '',
      smtp_port: 587,
      sender: '',
      password_mask: '',
    },
    appearance: {
      ai_bubble_theme: 'blue',
    },
    global_model_params: {
      context_window: 4096,
      tone: 'professional',
    },
    server: {
      app_env: 'development',
      app_host: '0.0.0.0',
      app_port: 8000,
      log_level: 'INFO',
    },
    agent_prompts: [
      { id: 'AG-001', name: '反馈聚类 Agent', category: '分析研判', scenario: '基于主题相似度对反馈进行聚类，识别重复诉求与热点问题。', enabled: true },
      { id: 'AG-002', name: '优先级评估 Agent', category: '分析研判', scenario: '根据 RICE 模型与影响面评估反馈优先级，给出处理建议。', enabled: true },
      { id: 'AG-003', name: '回复生成 Agent', category: '回复生成', scenario: '结合政策条文与历史回复，为反馈生成礼貌、准确的回复草稿。', enabled: true },
      { id: 'AG-004', name: '趋势预警 Agent', category: '诉求处置', scenario: '监控反馈量与情感变化趋势，提前识别群体性诉求风险。', enabled: false },
    ],
    ai_note: '本阶段洞察由模拟工作流生成；接入 LiteLLM 网关后切换真实 LLM 输出。',
    auth_note: '统一身份认证接入位已预留，本阶段不启用登录。',
    updated_at: new Date().toISOString(),
  }
}
