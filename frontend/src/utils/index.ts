/** 通用工具函数（骨架占位，按需扩展） */

/** 格式化日期时间（本地时区，24 小时制） */
export function formatDateTime(value: string | Date): string {
  const d = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleString('zh-CN', { hour12: false })
}

/** 只格式化日期（YYYY-MM-DD） */
export function formatDate(value: string | Date): string {
  const d = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleDateString('zh-CN')
}

/** 相对时间：仅显示"今天/昨天/N天前"（紧凑展示） */
export function relativeDay(value: string | Date): string {
  const d = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(d.getTime())) return String(value)
  const today = new Date()
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime()
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  const diff = Math.round((start - target) / 86400000)
  if (diff <= 0) return '今天'
  if (diff === 1) return '昨天'
  if (diff <= 7) return `${diff} 天前`
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

/** 合并过滤后的 class 名 */
export function cn(...parts: Array<string | undefined | null | false>): string {
  return parts.filter(Boolean).join(' ')
}