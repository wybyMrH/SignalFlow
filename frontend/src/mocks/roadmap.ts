/**
 * Mock 路线图/任务/回复草稿数据（决策行动闭环的模拟数据）。
 * 提供只读聚合 + 写操作（创建任务/状态流转/草稿回传），模拟微型后端。
 */

import type { ReplyDraft, RoadmapBoard, RoadmapItem, TaskItem, TaskStatus, DraftStatus } from '@/types'
import { feedbackDb } from './feedbackDb'

const daysAgoIso = (n: number) => new Date(Date.now() - n * 86400_000).toISOString()
const hoursAgoIso = (n: number) => new Date(Date.now() - n * 3600_000).toISOString()
const dateFromToday = (n: number) => new Date(Date.now() + n * 86400_000).toISOString().slice(0, 10)

export const roadmapItems: RoadmapItem[] = [
  {
    id: 'R2001',
    title: '材料复用与一网通办改造',
    topic_id: 't1',
    status: 'in_progress',
    version: 'v1.2',
    owner: '数据治理组',
    due_date: dateFromToday(28),
    progress: 45,
    task_count: 4,
    created_at: daysAgoIso(28),
  },
  {
    id: 'R2002',
    title: '大厅动态开窗与排队提示',
    topic_id: 't2',
    status: 'planning',
    version: 'v1.3',
    owner: '运营管理组',
    due_date: dateFromToday(44),
    progress: 0,
    task_count: 2,
    created_at: daysAgoIso(17),
  },
  {
    id: 'R2003',
    title: '预约系统容灾与消息补发',
    topic_id: 't3',
    status: 'scheduled',
    version: 'v1.1',
    owner: '平台研发组',
    due_date: dateFromToday(7),
    progress: 20,
    task_count: 3,
    created_at: daysAgoIso(13),
  },
  {
    id: 'R2004',
    title: '政策知识库问答上线',
    topic_id: 't4',
    status: 'released',
    version: 'v1.0',
    owner: '政务内容组',
    due_date: dateFromToday(-18),
    progress: 100,
    task_count: 3,
    created_at: daysAgoIso(64),
  },
]

export const roadmapTasks: TaskItem[] = [
  { id: 'TK1001', roadmap_id: 'R2001', title: '材料目录对齐（13 个高频事项）', status: 'done', owner: '数据治理组', priority: 1, created_at: daysAgoIso(26) },
  { id: 'TK1002', roadmap_id: 'R2001', title: '电子材料库接口联调', status: 'doing', owner: '平台研发组', priority: 1, created_at: daysAgoIso(20) },
  { id: 'TK1003', roadmap_id: 'R2001', title: '窗口免提交规则试点', status: 'doing', owner: '运营管理组', priority: 2, created_at: daysAgoIso(12) },
  { id: 'TK1004', roadmap_id: 'R2001', title: '线上清单与线下口径统一', status: 'todo', owner: '政务内容组', priority: 2, created_at: daysAgoIso(8) },
  { id: 'TK1005', roadmap_id: 'R2002', title: '高峰时段取号数据分析', status: 'todo', owner: '运营管理组', priority: 1, created_at: daysAgoIso(10) },
  { id: 'TK1006', roadmap_id: 'R2002', title: '动态开窗规则评审', status: 'todo', owner: '运营管理组', priority: 3, created_at: daysAgoIso(7) },
  { id: 'TK1007', roadmap_id: 'R2003', title: '预约数据每日快照备份', status: 'doing', owner: '平台研发组', priority: 1, created_at: daysAgoIso(9) },
  { id: 'TK1008', roadmap_id: 'R2003', title: '短信提醒补偿任务', status: 'todo', owner: '平台研发组', priority: 2, created_at: daysAgoIso(6) },
  { id: 'TK1009', roadmap_id: 'R2003', title: '改签幂等与重试修复', status: 'todo', owner: '平台研发组', priority: 1, created_at: daysAgoIso(5) },
  { id: 'TK1010', roadmap_id: 'R2004', title: '政策问答语料整理', status: 'done', owner: '政务内容组', priority: 1, created_at: daysAgoIso(59) },
  { id: 'TK1011', roadmap_id: 'R2004', title: '问答系统评测通过', status: 'done', owner: '平台研发组', priority: 2, created_at: daysAgoIso(38) },
  { id: 'TK1012', roadmap_id: 'R2004', title: '对外发布与值班培训', status: 'done', owner: '运营管理组', priority: 3, created_at: daysAgoIso(23) },
]

export const replyDrafts: ReplyDraft[] = [
  {
    id: 'D3001',
    feedback_id: 'F1055',
    excerpt: '今天大厅叫号系统故障，工作人员手工登记排队，秩序混乱，等了近一小时。',
    draft: '您好，抱歉给您带来不便。今日上午叫号系统临时故障已修复，我们对排队秩序问题已启动复盘，后续将增加故障应急广播与手工叫号预案，感谢您的反馈。',
    tone: '致歉+整改承诺',
    status: 'draft',
    updated_at: hoursAgoIso(4),
  },
  {
    id: 'D3002',
    feedback_id: 'F1049',
    excerpt: '线上预约系统凌晨维护后数据回滚，白天的预约记录全部丢失，窗口不认补打的凭证。',
    draft: '您好，关于预约记录回滚问题我们正在核查数据链路，已为您恢复预约记录并短信通知，窗口将按恢复后的记录办理，给您造成不便非常抱歉。',
    tone: '致歉+处理进展',
    status: 'draft',
    updated_at: hoursAgoIso(27),
  },
  {
    id: 'D3003',
    feedback_id: 'F1053',
    excerpt: '昨日门户政策问答回复已读未回，今天热线又问了一遍，答复内容还不一致。',
    draft: '您好，您反映的政策问答未回复与口径不一致问题已转政务内容组，将在 1 个工作日内统一口径并书面回复，感谢监督。',
    tone: '说明+时限承诺',
    status: 'approved',
    updated_at: hoursAgoIso(5),
  },
]

export function buildRoadmapBoard(): RoadmapBoard {
  return {
    items: [...roadmapItems],
    tasks: [...roadmapTasks],
    drafts: [...replyDrafts],
  }
}

/** 新建任务（mock 写操作）：追加任务并同步路线图 task_count */
export function createTask(input: { roadmap_id: string; title: string; owner: string; priority: number }): TaskItem {
  const id = `TK${String(roadmapTasks.length + 1001)}`
  const task: TaskItem = {
    id,
    roadmap_id: input.roadmap_id,
    title: input.title,
    status: 'todo',
    owner: input.owner,
    priority: input.priority,
    created_at: new Date().toISOString(),
  }
  roadmapTasks.unshift(task)
  const item = roadmapItems.find((r) => r.id === input.roadmap_id)
  if (item) item.task_count = roadmapTasks.filter((t) => t.roadmap_id === item.id).length
  return task
}

/** 任务状态流转（mock 写操作） */
export function updateTaskStatus(taskId: string, status: TaskStatus): TaskItem | null {
  const task = roadmapTasks.find((t) => t.id === taskId)
  if (!task) return null
  task.status = status
  return { ...task }
}

/** 草稿状态流转（mock 写操作）：draft → approved → sent；发送后回写对应反馈为 replied */
export function updateDraftStatus(draftId: string, status: DraftStatus): ReplyDraft | null {
  const draft = replyDrafts.find((d) => d.id === draftId)
  if (!draft) return null
  draft.status = status
  draft.updated_at = new Date().toISOString()
  if (status === 'sent') {
    const row = feedbackDb.find((f) => f.id === draft.feedback_id)
    if (row && (row.status === 'new' || row.status === 'analyzing')) {
      row.status = 'replied'
      row.updated_at = new Date().toISOString()
      row.reviewer = row.reviewer ?? '智能回传'
    }
  }
  return { ...draft }
}