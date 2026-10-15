/**
 * SignalFlow 前端共享类型
 * 与后端 app/schemas 对齐；mock 阶段的展示扩展字段放入 FeedbackView / 专用视图类型，
 * 真实后端就绪后由前端从基础实体 + 关联接口组装，避免类型污染后端契约。
 */

/** 反馈来源渠道 */
export type FeedbackSource = 'ticket' | 'review' | 'interview' | 'sales' | 'hotline' | 'portal'

/** 反馈状态（与后端枚举对齐；含 AI 扩展状态） */
export type FeedbackStatus = 'new' | 'analyzing' | 'ai_reviewing' | 'ai_replied' | 'resolved' | 'replied' | 'closed'

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

/** 反馈视图模型：基础实体 + 前端展示扩展（主题归属/优先级/情感/处理人/回复内容） */
export interface FeedbackView extends Feedback {
  topic_id?: string | null
  topic_title?: string | null
  priority?: number
  sentiment?: Sentiment
  reviewer?: string | null
  /** 已发送的正式回复内容（历史回复展示） */
  reply_content?: string | null
  replied_at?: string | null
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

/** 区域诉求分布（政务） */
export interface GovRegionShare {
  region: string
  count: number
  pct: number
  trend: 'up' | 'flat' | 'down'
  hot_issue: string
  departments: string[]
}

/** 热点主题聚类（政务） */
export interface GovHotTopic {
  id: string
  title: string
  summary: string
  coverage: number
  growth: number
  regions: string[]
  department: string
  root_cause: string
  evidence: string
  task_status: 'pending' | 'generated'
  task_id?: string
}

/** 舆情预警等级（政务）：蓝 → 黄 → 橙 → 红 */
export type GovAlertLevel = 'blue' | 'yellow' | 'orange' | 'red'

/** 舆情与风险预警（政务） */
export interface GovAlertItem {
  id: string
  level: GovAlertLevel
  title: string
  summary: string
  trigger: string
  regions: string[]
  evidence_count: number
  dispatched: boolean
  dispatched_to?: string
}

/** 政策告知（政务） */
export interface GovPolicyNotice {
  id: string
  title: string
  content: string
  status: 'draft' | 'published'
  scope: string
  channel: string
  sent_count: number
  read_rate: number
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
  period: string
  generated_at: string
  summary: {
    total_count: number
    weekly_new: number
    pending_count: number
    overdue_count: number
    resolve_rate: number
    highest_alert: GovAlertLevel | null
  }
  classifications: GovClassification[]
  supervisions: GovSupervision[]
  regions: GovRegionShare[]
  topics: GovHotTopic[]
  alerts: GovAlertItem[]
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

/** AI 工作流运行状态 */
export interface AIWorkflowStatus {
  id: string
  name: string
  status: 'running' | 'completed' | 'failed' | 'queued'
  progress: number
  started_at: string
  eta?: string
  detail?: string
}

/** AI 自动化规则配置 */
export interface AIAutomationRule {
  id: string
  name: string
  description: string
  enabled: boolean
  scenario: string
  icon: string
  tone: 'primary' | 'success' | 'warning' | 'info' | 'danger'
  stats?: string
}

/** AI 对话消息 */
export interface AIChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  workflow_refs?: string[]
  sources?: string[]
}

/** 反馈状态统计 */
export interface FeedbackStats {
  total: number
  new: number
  analyzing: number
  ai_reviewing: number
  ai_replied: number
  resolved: number
  replied: number
  closed: number
  high_priority: number
}

/** 自动分类候选类别 */
export interface ClassificationAlternative {
  topic: string
  confidence: number
}

/** 自动分类结果（单条反馈） */
export interface AutoClassificationResult {
  feedback_id: string
  content: string
  suggested_topic: string
  confidence: number
  alternatives: ClassificationAlternative[]
  needs_review: boolean
  processed_at: string
  reviewer_note?: string
}

/** 去重合并组成员 */
export interface DedupMember {
  feedback_id: string
  content: string
  similarity: number
}

/** 去重合并组 */
export interface DedupGroup {
  group_id: string
  representative_id: string
  members: DedupMember[]
  merged_topic: string
  status: 'pending' | 'merged' | 'dismissed'
  merged_at?: string
  repeat_count: number
}

/** 优先级评分因子（RICE 模型维度） */
export interface PriorityFactor {
  key: string
  label: string
  weight: number
  value: number
  max: number
  note: string
}

/** 优先级规则 */
export interface PriorityRule {
  id: string
  name: string
  enabled: boolean
  description: string
  factors: PriorityFactor[]
  threshold: number
  auto_escalate: boolean
  updated_at: string
}

/** 优先级调整记录 */
export interface PriorityAdjustment {
  feedback_id: string
  old_priority: number
  new_priority: number
  reason: string
  triggered_by: string
  adjusted_at: string
}

/** 自动化执行概览（日维度） */
export interface AutomationExecutionSummary {
  date: string
  classified_count: number
  review_queue_count: number
  deduped_group_count: number
  saved_feedback_count: number
  priority_adjusted_count: number
  auto_escalated_count: number
  avg_confidence: number
  manual_review_rate: number
}

/** 企业线索阶段（推销联动：识别 → 确认 → 推送销售/CSM） */
export type BusinessLeadStage = 'identified' | 'qualified' | 'pushed'

/** 企业合作线索（从反馈语义匹配产品目录后识别） */
export interface BusinessLead {
  id: string
  feedback_id: string
  content: string
  company_name: string
  /** 所属行业 */
  industry: string
  /** 企业类型：国企/央企/私企/外企/事业单位/医疗机构/教育机构等 */
  company_type: string
  /** 规模带 */
  size_band: string
  matched_product: string
  match_reason: string
  /** 客户价值 0-100 */
  value_score: number
  confidence: number
  stage: BusinessLeadStage
  created_at: string
}

/** 行业分布条目 */
export interface IndustryShare {
  industry: string
  count: number
  pct: number
  trend: TopicTrend
}

/** 市场动向信号类型 */
export type MarketSignalType = 'opportunity' | 'gap' | 'risk' | 'shift'

/** 市场动向信号（AI 从反馈趋势中提炼） */
export interface MarketSignal {
  id: string
  title: string
  type: MarketSignalType
  summary: string
  /** 支撑证据（反馈）数 */
  evidence_count: number
  /** 影响强度 0-100 */
  severity: number
  related_industries: string[]
  created_at: string
}

/** 共性需求归纳 */
export interface CommonNeed {
  id: string
  title: string
  description: string
  feedback_count: number
  customer_count: number
  industries: string[]
  /** 对应产品能力（机会映射） */
  product_potential: string
  priority: number
  status: 'open' | 'planned' | 'shipped'
}

/** 商务洞察总览（可视化报告头部统计） */
export interface BusinessInsightSummary {
  total_leads: number
  qualified_leads: number
  pushed_leads: number
  industry_count: number
  total_feedback_count: number
  customer_count: number
  market_signal_count: number
  common_need_count: number
  report_period: string
  generated_at: string
}