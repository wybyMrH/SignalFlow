/**
 * SignalFlow 前端共享类型
 * 与后端 app/schemas 对齐；mock 阶段的展示扩展字段放入 FeedbackView / 专用视图类型，
 * 真实后端就绪后由前端从基础实体 + 关联接口组装，避免类型污染后端契约。
 */

/** 反馈来源渠道 */
export type FeedbackSource = 'ticket' | 'review' | 'interview' | 'sales' | 'hotline' | 'portal'

/** 反馈状态（与后端枚举对齐） */
export type FeedbackStatus = 'new' | 'analyzing' | 'resolved' | 'replied' | 'closed'

/** 情感倾向 */
export type Sentiment = 'negative' | 'neutral' | 'positive'

/** 反馈实体（对应后端 FeedbackRead；字段名保持与后端一致） */
export interface Feedback {
  id: string
  tenant_id: string
  source: string
  source_ref: string | null
  content: string
  author: string | null
  status: FeedbackStatus
  created_at: string
  updated_at: string
}

/** 反馈视图模型：基础实体 + 前端展示扩展（主题归属/优先级/情感/处理人） */
export interface FeedbackView extends Feedback {
  topic_id?: string | null
  topic_title?: string | null
  priority?: number
  sentiment?: Sentiment
  reviewer?: string | null
}

/** 创建反馈请求体（对应后端 FeedbackCreate） */
export interface FeedbackCreate {
  source: string
  source_ref?: string | null
  content: string
  author?: string | null
}

/** 反馈列表查询参数 */
export interface FeedbackListQuery {
  source?: FeedbackSource | ''
  status?: FeedbackStatus | ''
  keyword?: string
  topic_id?: string
  page?: number
  page_size?: number
}

/** 分页响应 */
export interface Paged<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** 主题趋势 */
export type TopicTrend = 'up' | 'flat' | 'down'

/** 优先级评分维度（可解释打分卡） */
export interface ScoreDimension {
  key: string
  label: string
  score: number
  max: number
  note: string
}

/** 优先级等级 */
export type PriorityLevel = 'critical' | 'high' | 'medium' | 'low'

/** 优先级评分卡 */
export interface PriorityScoreCard {
  total: number
  max: number
  level: PriorityLevel
  dimensions: ScoreDimension[]
}

/** 主题证据链条目（可追溯到原始反馈） */
export interface TopicEvidence {
  feedback_id: string
  excerpt: string
  author: string
  source: FeedbackSource
  source_label: string
  created_at: string
  sentiment: Sentiment
}

/** 洞察主题（LangGraph 工作流产物；mock 阶段由模拟数据提供） */
export interface InsightTopic {
  id: string
  title: string
  short: string
  feedback_count: number
  customer_count: number
  trend: TopicTrend
  /** 信号强度 0-100 */
  strength: number
  /** 优先级总分 0-100 */
  priority_score: number
  score_card: PriorityScoreCard
  evidence: TopicEvidence[]
  last_seen_at: string
  updated_at: string
}

/** 洞察看板响应 */
export interface InsightDashboard {
  items: InsightTopic[]
  total: number
  generated_at: string
  skeleton?: boolean
}

/** 路线图状态 */
export type RoadmapStatus = 'planning' | 'in_progress' | 'scheduled' | 'released'

/** 任务状态 */
export type TaskStatus = 'todo' | 'doing' | 'done'

/** 回复草稿状态 */
export type DraftStatus = 'draft' | 'approved' | 'sent'

/** 路线图看板项 */
export interface RoadmapItem {
  id: string
  title: string
  topic_id?: string | null
  status: RoadmapStatus
  version: string
  owner: string
  due_date: string
  progress: number
  task_count: number
  created_at: string
}

/** 产品任务 */
export interface TaskItem {
  id: string
  roadmap_id: string
  title: string
  status: TaskStatus
  owner: string
  priority: number
  created_at: string
}

/** 客户回复草稿（AI 起草，人工确认后回传） */
export interface ReplyDraft {
  id: string
  feedback_id: string
  excerpt: string
  draft: string
  tone: string
  status: DraftStatus
  updated_at: string
}

/** 路线图看板聚合 */
export interface RoadmapBoard {
  items: RoadmapItem[]
  tasks: TaskItem[]
  drafts: ReplyDraft[]
}

/** 趋势点 */
export interface TrendPoint {
  date: string
  label: string
  count: number
  resolved: number
}

/** 渠道占比 */
export interface ChannelShare {
  channel: FeedbackSource
  label: string
  count: number
  pct: number
}

/** 总览工作台指标 */
export interface DashboardMetrics {
  total_feedbacks: number
  deduped_topics: number
  pending: number
  resolved_today: number
  high_priority: number
  avg_resolve_hours: number
  mock_mode: boolean
  updated_at: string
  trend: TrendPoint[]
  channels: ChannelShare[]
}

/** 诉求分级（政务） */
export interface GovClassification {
  level: string
  label: string
  count: number
  pct: number
  tone: 'danger' | 'warning' | 'info' | 'neutral'
}

/** 督办分级（政务） */
export interface GovSupervision {
  level: string
  label: string
  count: number
  overdue: number
}

/** 政策告知（政务） */
export interface GovPolicyNotice {
  id: string
  title: string
  content: string
  status: 'draft' | 'published'
  scope: string
  sent_count: number
  updated_at: string
}

/** 审计留痕（政务） */
export interface GovAuditRecord {
  id: string
  action: string
  operator: string
  time: string
  target: string
}

/** 政务适配总览 */
export interface GovOverview {
  classifications: GovClassification[]
  supervisions: GovSupervision[]
  notices: GovPolicyNotice[]
  audits: GovAuditRecord[]
  updated_at: string
}

/** 渠道接入状态 */
export interface ChannelStatus {
  key: FeedbackSource
  label: string
  enabled: boolean
  connected: boolean
  last_sync: string | null
  incoming: number
  note: string
}

/** 系统设置视图 */
export interface SettingsView {
  mock_mode: boolean
  channels: ChannelStatus[]
  ai_note: string
  auth_note: string
  updated_at: string
}