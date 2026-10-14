/**
 * 展示层标签映射：将契约枚举映射为界面文案。
 * 文案遵循「字段 Label ≤ 4 字」的紧凑规范（见 docs/frontend-development-plan.md §5.2）。
 */
import type { FeedbackSource, FeedbackStatus, PriorityLevel, Sentiment } from '@/types'

export const sourceLabels: Record<FeedbackSource, string> = {
  ticket: '工单',
  review: '在线评价',
  interview: '客户访谈',
  sales: '商务侧',
  hotline: '服务热线',
  portal: '服务门户',
}

export const statusLabels: Record<FeedbackStatus, string> = {
  new: '新增',
  analyzing: '分析中',
  ai_reviewing: 'AI审核中',
  ai_replied: 'AI已回复',
  resolved: '已解决',
  replied: '已回复',
  closed: '已关闭',
}

export const statusTone: Record<FeedbackStatus, 'info' | 'warning' | 'success' | 'neutral' | 'muted'> = {
  new: 'info',
  analyzing: 'warning',
  ai_reviewing: 'info',
  ai_replied: 'success',
  resolved: 'success',
  replied: 'success',
  closed: 'muted',
}

export const sentimentLabels: Record<Sentiment, string> = {
  negative: '负面',
  neutral: '中性',
  positive: '正向',
}

export const sentimentTone: Record<Sentiment, 'danger' | 'info' | 'success'> = {
  negative: 'danger',
  neutral: 'info',
  positive: 'success',
}

export const priorityLabels: Record<PriorityLevel, string> = {
  critical: '紧急',
  high: '高',
  medium: '中',
  low: '低',
}

export const priorityTone: Record<PriorityLevel, 'danger' | 'warning' | 'info' | 'neutral'> = {
  critical: 'danger',
  high: 'warning',
  medium: 'info',
  low: 'neutral',
}