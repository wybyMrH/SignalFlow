/**
 * Mock 总览工作台指标：基于 rows 实时聚合，保证「总览数字 -> 明细列表」口径一致。
 */

import type { ChannelShare, DashboardMetrics, FeedbackStatus, TrendPoint } from '@/types'
import { visibleFeedbacks } from './feedbackDb'
import { sourceLabels } from '@/utils/labels'

const RESOLVED_STATUSES: FeedbackStatus[] = ['resolved', 'replied', 'closed']
const PENDING_STATUSES: FeedbackStatus[] = ['new', 'analyzing']

/** 近 N 天（含今天）日期序列，UTC 日期键（与反馈数据时间戳口径一致） */
function recentDays(n: number): string[] {
  const days: string[] = []
  const now = new Date()
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - i))
    days.push(d.toISOString().slice(0, 10))
  }
  return days
}

export function computeDashboardMetrics(): DashboardMetrics {
  // 统计口径只计入创建日期 <= 今天的可见反馈（未来预置样本到期后自动进入统计）
  const rows = visibleFeedbacks()
  const total = rows.length
  const pending = rows.filter((r) => PENDING_STATUSES.includes(r.status)).length
  const highPriority = rows.filter((r) => (r.priority ?? 0) >= 4 && PENDING_STATUSES.includes(r.status)).length

  const todayKey = new Date().toISOString().slice(0, 10)
  const resolvedToday = rows.filter(
    (r) => RESOLVED_STATUSES.includes(r.status) && r.updated_at.slice(0, 10) === todayKey,
  ).length

  const days = recentDays(14)
  const trend: TrendPoint[] = days.map((day) => {
    const count = rows.filter((r) => r.created_at.slice(0, 10) === day).length
    const resolved = rows.filter(
      (r) => RESOLVED_STATUSES.includes(r.status) && r.updated_at.slice(0, 10) === day,
    ).length
    const label = day.slice(5)
    return { date: day, label, count, resolved }
  })

  const bySource = new Map<string, number>()
  for (const r of rows) bySource.set(r.source, (bySource.get(r.source) ?? 0) + 1)
  const channels: ChannelShare[] = [...bySource.entries()]
    .map(([channel, count]) => ({
      channel: channel as ChannelShare['channel'],
      label: sourceLabels[channel as keyof typeof sourceLabels] ?? channel,
      count,
      pct: total ? Math.round((count / total) * 1000) / 10 : 0,
    }))
    .sort((a, b) => b.count - a.count)

  // 去重主题数：有归属主题的反馈涉及的不同主题数（与后端 InsightTopic 数量口径一致）
  const dedupedTopics = new Set(rows.map((r) => r.topic_id).filter(Boolean)).size

  // 平均解决时长：办结记录 updated_at - created_at 均值（小时，保留 1 位小数），与后端聚合口径一致
  const hours: number[] = []
  for (const r of rows) {
    if (RESOLVED_STATUSES.includes(r.status)) {
      const ms = new Date(r.updated_at).getTime() - new Date(r.created_at).getTime()
      if (!Number.isNaN(ms)) hours.push(ms / 3_600_000)
    }
  }
  const avgResolveHours = hours.length ? Math.round((hours.reduce((a, b) => a + b, 0) / hours.length) * 10) / 10 : 0

  return {
    total_feedbacks: total,
    deduped_topics: dedupedTopics,
    pending,
    resolved_today: resolvedToday,
    high_priority: highPriority,
    avg_resolve_hours: avgResolveHours,
    mock_mode: true,
    updated_at: new Date().toISOString(),
    trend,
    channels,
  }
}