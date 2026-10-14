/**
 * Mock 政务适配数据（FS-6 最小页）：诉求分级、督办、政策告知、审计留痕。
 */

import type { GovOverview } from '@/types'

export function buildGovOverview(): GovOverview {
  return {
    classifications: [
      { level: 'A', label: '紧急敏感', count: 2, pct: 4.2, tone: 'danger' },
      { level: 'B', label: '重点诉求', count: 11, pct: 22.9, tone: 'warning' },
      { level: 'C', label: '一般事项', count: 28, pct: 58.3, tone: 'info' },
      { level: 'D', label: '咨询建议', count: 7, pct: 14.6, tone: 'neutral' },
    ],
    supervisions: [
      { level: '一级督办', label: '市级督办事项', count: 1, overdue: 0 },
      { level: '二级督办', label: '部门督办事项', count: 3, overdue: 1 },
      { level: '三级督办', label: '窗口整改事项', count: 8, overdue: 2 },
    ],
    notices: [
      { id: 'N4001', title: '大厅高峰预约分流公告', content: '10 月 15 日起 9:00-11:00 实行预约分流，请优先线上取号。', status: 'published', scope: '全渠道', sent_count: 1284, updated_at: '2026-10-12T09:00:00Z' },
      { id: 'N4002', title: '叫号系统故障应急说明', content: '今日上午 9:20-10:05 叫号系统临时故障，已恢复正常。', status: 'draft', scope: '大厅广播', sent_count: 0, updated_at: '2026-10-14T10:30:00Z' },
    ],
    audits: [
      { id: 'A5001', action: '导出诉求分级报告', operator: '系统管理员', time: '2026-10-14 10:12', target: '诉求分级报表' },
      { id: 'A5002', action: '发布政策告知', operator: '政务内容组-何静', time: '2026-10-12 09:01', target: 'N4001' },
      { id: 'A5003', action: '修改督办状态', operator: '运营管理组-张莉', time: '2026-10-11 16:40', target: '二级督办-叫号跳号' },
      { id: 'A5004', action: '删除草稿', operator: '政务内容组-何静', time: '2026-10-09 14:22', target: '草稿-政策问答' },
    ],
    updated_at: new Date().toISOString(),
  }
}