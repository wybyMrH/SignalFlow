/**
 * Mock 系统设置页数据：渠道接入状态与全量配置分区。
 */

import type { SettingsView } from '@/types'

export function buildSettingsView(): SettingsView {
  return {
    mock_mode: true,
    channels: [
      { key: 'portal', label: '门户留言', enabled: true, connected: true, last_sync: '2026-10-14T18:30:00Z', incoming: 9, note: '门户留言已对接' },
      { key: 'review', label: '评价中心', enabled: true, connected: true, last_sync: '2026-10-14T18:20:00Z', incoming: 7, note: '评价中心已对接' },
      { key: 'hotline', label: '热线录音', enabled: true, connected: true, last_sync: '2026-10-14T18:15:00Z', incoming: 11, note: '热线录音转写待接 LLM' },
      { key: 'interview', label: '客户访谈', enabled: true, connected: false, last_sync: null, incoming: 0, note: '访谈为线下导入，未接自动同步' },
      { key: 'ticket', label: '工单系统', enabled: true, connected: true, last_sync: '2026-10-14T18:30:00Z', incoming: 12, note: '工单系统已对接' },
      { key: 'sales', label: '商务反馈', enabled: false, connected: false, last_sync: null, incoming: 0, note: '商务侧反馈待开通' },
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
      { id: 'AG-001', name: '政策公告 Agent', category: '内容生成', scenario: '根据政策变化自动草拟对外公告，联动发布公告工作流。', enabled: true },
      { id: 'AG-002', name: '商单回复 Agent', category: '回复生成', scenario: '对接企业商机与询价反馈，生成专业报价与跟进话术。', enabled: true },
      { id: 'AG-003', name: '舆情聚类 Agent', category: '分析研判', scenario: '多条舆情指向同一论点时自动聚类，形成统一处置建议。', enabled: true },
      { id: 'AG-004', name: '邻里诉求 Agent', category: '诉求处置', scenario: '专门处理邻里纠纷类诉求，按属地映射到社区网格。', enabled: false },
      { id: 'AG-005', name: '反馈自动回复 Agent', category: '回复生成', scenario: '对高频咨询自动生成规范回复草稿，进入人工审批队列。', enabled: true },
    ],
    ai_note: '本阶段洞察由模拟工作流生成；接入 LiteLLM 网关后切换真实 LLM 输出。',
    auth_note: '统一身份认证接入位已预留，本阶段不启用登录。',
    updated_at: new Date().toISOString(),
  }
}
