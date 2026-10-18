/**
 * Mock 洞察主题数据源（LangGraph 工作流产物的模拟）。
 *
 * 主题定义静态化（模拟分析结果），反馈数/客户数/证据链基于 feedbackDb 动态计算，
 * 保证「主题 -> 原始反馈」证据链可下钻且口径自洽。
 */

import type { InsightDashboard, InsightTopic, PriorityScoreCard, ScoreDimension, TopicEvidence, TopicTrend } from '@/types'
import { excerpt, visibleFeedbacks } from './feedbackDb'
import { sourceLabels } from '@/utils/labels'

/** 主题基础定义（静态，模拟工作流聚类 + 优先级评估结果） */
interface TopicDef {
  id: string
  title: string
  short: string
  trend: TopicTrend
  strength: number
  priority_score: number
  level: InsightTopic['score_card']['level']
  dimensions: Array<Pick<ScoreDimension, 'key' | 'label' | 'score' | 'max' | 'note'>>
}

const topicDefs: TopicDef[] = [
  {
    id: 't1',
    title: '办事材料重复提交',
    short: '材料复用未落地，线上线下清单不一致',
    trend: 'up',
    strength: 82,
    priority_score: 88,
    level: 'critical',
    dimensions: [
      { key: 'impact', label: '影响面', score: 22, max: 25, note: '涉及不动产/社保/企业注册等多事项' },
      { key: 'urgency', label: '紧迫度', score: 23, max: 25, note: '近 7 天反馈上升 18%' },
      { key: 'feasibility', label: '可行性', score: 20, max: 25, note: '材料库共享为既有规划' },
      { key: 'severity', label: '严重度', score: 23, max: 25, note: '线下要求与线上申报冲突' },
    ],
  },
  {
    id: 't2',
    title: '大厅等候时间过长',
    short: '高峰排队超 1 小时，动态开窗不足',
    trend: 'up',
    strength: 90,
    priority_score: 92,
    level: 'critical',
    dimensions: [
      { key: 'impact', label: '影响面', score: 24, max: 25, note: '涉社保/医保等高频窗口' },
      { key: 'urgency', label: '紧迫度', score: 24, max: 25, note: '节假日高峰连续爆满' },
      { key: 'feasibility', label: '可行性', score: 22, max: 25, note: '预约量驱动动态开窗可行' },
      { key: 'severity', label: '严重度', score: 22, max: 25, note: '叫号系统故障放大不满' },
    ],
  },
  {
    id: 't3',
    title: '线上预约系统不稳定',
    short: '预约丢失/改签失败，短信提醒缺失',
    trend: 'up',
    strength: 74,
    priority_score: 80,
    level: 'high',
    dimensions: [
      { key: 'impact', label: '影响面', score: 19, max: 25, note: '影响预约全链路' },
      { key: 'urgency', label: '紧迫度', score: 21, max: 25, note: '凌晨维护回滚丢数据' },
      { key: 'feasibility', label: '可行性', score: 20, max: 25, note: '容灾与消息补发可快速修复' },
      { key: 'severity', label: '严重度', score: 20, max: 25, note: '白跑一趟风险高' },
    ],
  },
  {
    id: 't4',
    title: '政策咨询响应偏慢',
    short: '热线转接多、口径不一，答复超时',
    trend: 'flat',
    strength: 68,
    priority_score: 72,
    level: 'high',
    dimensions: [
      { key: 'impact', label: '影响面', score: 18, max: 25, note: '涉及政策解读多口径' },
      { key: 'urgency', label: '紧迫度', score: 18, max: 25, note: '5 个工作日才回复' },
      { key: 'feasibility', label: '可行性', score: 19, max: 25, note: '知识库问答可标准化' },
      { key: 'severity', label: '严重度', score: 17, max: 25, note: '信息不透明易引发投诉' },
    ],
  },
  {
    id: 't5',
    title: '窗口服务体验不一',
    short: 'AB 岗交接不清，答复口径不统一',
    trend: 'flat',
    strength: 58,
    priority_score: 62,
    level: 'medium',
    dimensions: [
      { key: 'impact', label: '影响面', score: 16, max: 25, note: '窗口服务标准化缺失' },
      { key: 'urgency', label: '紧迫度', score: 15, max: 25, note: '正面评价同时存在，非线性恶化' },
      { key: 'feasibility', label: '可行性', score: 16, max: 25, note: '话术与交接规范易落地' },
      { key: 'severity', label: '严重度', score: 15, max: 25, note: '重复排队引发二次投诉' },
    ],
  },
  {
    id: 't6',
    title: '老年与无障碍服务不足',
    short: '适老化操作缺失，无障碍通道管理弱',
    trend: 'up',
    strength: 55,
    priority_score: 70,
    level: 'high',
    dimensions: [
      { key: 'impact', label: '影响面', score: 17, max: 25, note: '老年/残障群体高频受影响' },
      { key: 'urgency', label: '紧迫度', score: 18, max: 25, note: '公共服务均等化要求' },
      { key: 'feasibility', label: '可行性', score: 17, max: 25, note: '人工通道与适老改造可并行' },
      { key: 'severity', label: '严重度', score: 18, max: 25, note: '涉及特殊群体权益' },
    ],
  },
  {
    id: 't7',
    title: '停车与指引不清晰',
    short: '入口无指示，余位信息缺失',
    trend: 'down',
    strength: 40,
    priority_score: 45,
    level: 'low',
    dimensions: [
      { key: 'impact', label: '影响面', score: 12, max: 25, note: '主要影响首次到访' },
      { key: 'urgency', label: '紧迫度', score: 10, max: 25, note: '趋势回落' },
      { key: 'feasibility', label: '可行性', score: 12, max: 25, note: '指示牌与余位屏成本低' },
      { key: 'severity', label: '严重度', score: 11, max: 25, note: '体验问题为主' },
    ],
  },
  {
    id: 't8',
    title: '移动端 APP 操作不便',
    short: '入口深、步骤多，适老化与稳定性差',
    trend: 'flat',
    strength: 66,
    priority_score: 60,
    level: 'medium',
    dimensions: [
      { key: 'impact', label: '影响面', score: 16, max: 25, note: '线上渠道主力人群' },
      { key: 'urgency', label: '紧迫度', score: 15, max: 25, note: '推送失效影响进度透明' },
      { key: 'feasibility', label: '可行性', score: 15, max: 25, note: '交互重构周期较长' },
      { key: 'severity', label: '严重度', score: 14, max: 25, note: '闪退/人脸难通过阻断办理' },
    ],
  },
]

function makeScoreCard(def: TopicDef): PriorityScoreCard {
  const total = def.dimensions.reduce((sum, d) => sum + d.score, 0)
  return { total, max: 100, level: def.level, dimensions: def.dimensions }
}

/** 动态组装主题（计数/证据链/最近信号时间） */
export function buildTopics(): InsightTopic[] {
  return topicDefs.map((def) => {
    const rows = visibleFeedbacks()
      .filter((r) => r.topic_id === def.id)
      .sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0) || b.created_at.localeCompare(a.created_at))

    const evidence: TopicEvidence[] = rows.slice(0, 5).map((r) => ({
      feedback_id: r.id,
      excerpt: excerpt(r.content),
      author: r.author ?? '匿名',
      source: r.source as TopicEvidence['source'],
      source_label: sourceLabels[r.source as TopicEvidence['source']],
      created_at: r.created_at,
      sentiment: r.sentiment ?? 'neutral',
    }))

    const customers = new Set(rows.map((r) => r.author ?? '匿名')).size

    return {
      id: def.id,
      title: def.title,
      short: def.short,
      feedback_count: rows.length,
      customer_count: customers,
      trend: def.trend,
      strength: def.strength,
      priority_score: def.priority_score,
      score_card: makeScoreCard(def),
      evidence,
      last_seen_at: rows.length ? rows[0]?.created_at ?? '' : '',
      updated_at: rows.length ? rows[0]?.updated_at ?? '' : '',
    }
  })
}

/** 洞察看板（排序：优先级分降序） */
export function computeInsightDashboard(): InsightDashboard {
  const items = buildTopics().sort((a, b) => b.priority_score - a.priority_score)
  return { items, total: items.length, generated_at: new Date().toISOString() }
}