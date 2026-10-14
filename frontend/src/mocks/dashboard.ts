/**
 * Mock 总览工作台指标：基于 feedbackDb 实时聚合，保证「总览数字 -> 明细列表」口径一致。
 */

import type { ChannelShare, DashboardMetrics, FeedbackStatus, TrendPoint } from '@/types'
import { feedbackDb } from './feedbackDb'
import { sourceLabels } from '@/utils/labels'

const RESOLVED_STATUSES: FeedbackStatus[] = ['resolved', 'replied', 'closed']
const PENDING_STATUSES: FeedbackStatus[] = ['new', 'analyzing']

/** 近 N 天（含今天）日期序列，UTC 日期键 */
function recentDays(n: number): string[] {
  const days: string[] = []
  const now = new Date()
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i)
    days.push(d.toISOString().slice(0, 10))
  }
  return days
}

export function computeDashboardMetrics(): DashboardMetrics {
  const total = feedbackDb.length
  const pending = feedbackDb.filter((r) => PENDING_STATUSES.includes(r.status)).length
  const highPriority = feedbackDb.filter((r) => (r.priority ?? 0) >= 4 && PENDING_STATUSES.includes(r.status)).length

  const todayKey = new Date().toISOString().slice(0, 10)
  const resolvedToday = feedbackDb.filter(
    (r) => RESOLVED_STATUSES.includes(r.status) && r.updated_at.slice(0, 10) === todayKey,
  ).length

  const days = recentDays(14)
  const trend: TrendPoint[] = days.map((day) => {
    const count = feedbackDb.filter((r) => r.created_at.slice(0, 10) === day).length
    const resolved = feedbackDb.filter(
      (r) => RESOLVED_STATUSES.includes(r.status) && r.updated_at.slice(0, 10) === day,
    ).length
    const label = day.slice(5)
    return { date: day, label, count, resolved }
  })

  const bySource = new Map<string, number>()
  for (const r of feedbackDb) bySource.set(r.source, (bySource.get(r.source) ?? 0) + 1)
  const channels: ChannelShare[] = [...bySource.entries()]
    .map(([channel, count]) => ({
      channel: channel as ChannelShare['channel'],
      label: sourceLabels[channel as keyof typeof sourceLabels] ?? channel,
      count,
      pct: total ? Math.round((count / total) * 1000) / 10 : 0,
    }))
    .sort((a, b) => b.count - a.count)

  return {
    total_feedbacks: total,
    deduped_topics: 8,
    pending,
    resolved_today: resolvedToday,
    high_priority: highPriority,
    avg_resolve_hours: 23.6,
    mock_mode: true,
    updated_at: new Date().toISOString(),
    trend,
    channels,
  }
}