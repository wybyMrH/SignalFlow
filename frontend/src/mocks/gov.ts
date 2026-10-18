/**
 * Mock 政务适配数据（FS-6 政务统计扩展）：
 * 诉求分级、督办事项、区域分布、热点主题、舆情预警、政策告知、审计留痕。
 * 覆盖规划文档 §6.3：诉求分级督办、热点主题聚类、痛点成因、舆情蓝黄橙红预警、
 * 治理任务生成、政策告知与脱敏公开。全部 AI 仅提炼候选，处置/公开需人工确认。
 */

import type { GovOverview } from '@/types'

const mockUtc = (daysAgo: number, h: number, m: number) => {
  const d = new Date()
  d.setUTCDate(d.getUTCDate() - daysAgo)
  d.setUTCHours(h, m, 0, 0)
  return d.toISOString()
}
const timeStr = (daysAgo: number, h: number, m: number) => {
  const d = new Date()
  d.setDate(d.getDate() - daysAgo)
  d.setHours(h, m, 0, 0)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(h)}:${p(m)}`
}
const dayStr = (d: Date) => `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`
const periodStart = dayStr(new Date(Date.now() - 30 * 86400_000))
const periodEnd = dayStr(new Date())

export function buildGovOverview(): GovOverview {
  return {
    period: `${periodStart} ~ ${periodEnd}`,
    generated_at: new Date().toISOString(),
    summary: {
      total_count: 48,
      weekly_new: 7,
      pending_count: 12,
      overdue_count: 3,
      resolve_rate: 0.812,
      highest_alert: 'orange',
    },
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
    regions: [
      { region: '玄武区', count: 12, pct: 25, trend: 'up', hot_issue: '电梯加装审批', departments: ['住建局', '规划局'] },
      { region: '秦淮区', count: 9, pct: 18.8, trend: 'flat', hot_issue: '幼儿园学位', departments: ['教育局'] },
      { region: '建邺区', count: 8, pct: 16.7, trend: 'flat', hot_issue: '停车收费调整', departments: ['城管局', '交管'] },
      { region: '鼓楼区', count: 7, pct: 14.6, trend: 'down', hot_issue: '窗口叫号等待', departments: ['政务办'] },
      { region: '栖霞区', count: 6, pct: 12.5, trend: 'up', hot_issue: '就业补贴申领', departments: ['人社局'] },
      { region: '雨花台区', count: 6, pct: 12.5, trend: 'down', hot_issue: '供暖管网报修', departments: ['住建局', '水务局'] },
    ],
    topics: [
      {
        id: 'GT-2601',
        title: '老旧小区加装电梯审批周期偏长',
        summary: '居民对既有住宅加装电梯的审批流程、出资分摊与管线迁移意见集中，多部门协同耗时超过法定时限。',
        coverage: 23,
        growth: 42,
        regions: ['玄武区', '鼓楼区'],
        department: '住建局',
        root_cause: '流程壁垒：规划、住建、属地街道分头审批，管线迁移缺乏牵头部门',
        evidence: '「加了半年还在公示，说是管线迁移要等市政排期，到底谁牵头？」',
        task_status: 'generated',
        task_id: 'GT-2601-治理',
      },
      {
        id: 'GT-2602',
        title: '高校毕业生就业补贴申领门槛不清',
        summary: '应届生对补贴对象、申领材料与到账周期疑问集中，线上线下答复口径存在不一致。',
        coverage: 17,
        growth: 28,
        regions: ['栖霞区', '秦淮区'],
        department: '人社局',
        root_cause: '政策告知不足：细则更新后未同步各渠道，问答知识库滞后',
        evidence: '「公告写的是毕业两年内，窗口又说按毕业证日期，到底按哪个？」',
        task_status: 'pending',
      },
      {
        id: 'GT-2603',
        title: '幼儿园入园学位缺口引发排队焦虑',
        summary: '家长集中反映公办园学位不足、报名渠道扎堆，多个业主群出现转发焦虑情绪。',
        coverage: 15,
        growth: 35,
        regions: ['秦淮区', '建邺区'],
        department: '教育局',
        root_cause: '供需缺口：片区学位规划滞后于人口导入，信息公开节奏慢',
        evidence: '「同一时间只能报一个园，系统又卡，错过就没有学位了？」',
        task_status: 'pending',
      },
      {
        id: 'GT-2604',
        title: '政务大厅叫号等待时长上升',
        summary: '窗口业务高峰时段排队超过 40 分钟，老年人不会线上预约导致到店返工。',
        coverage: 11,
        growth: -8,
        regions: ['鼓楼区'],
        department: '政务办',
        root_cause: '服务流程：高峰分流不足，线下引导与线上预约未打通',
        evidence: '「取了号还要等一个小时，说好的一窗受理呢？」',
        task_status: 'pending',
      },
    ],
    alerts: [
      {
        id: 'BR-001',
        level: 'blue',
        title: '停车收费调整咨询增多',
        summary: '多小区业主群讨论新一轮道路停车收费调整，以咨询为主，暂未发现聚集风险。',
        trigger: '敏感词「收费上涨」频次 +180%，情绪偏中性',
        regions: ['建邺区'],
        evidence_count: 6,
        dispatched: false,
      },
      {
        id: 'YE-002',
        level: 'yellow',
        title: '幼儿园学位舆情升温',
        summary: '家长群转发热议学位缺口，出现「错过报名就没有学位」等焦虑表述，需口径统一。',
        trigger: '异常量级 + 情绪分析呈焦虑主导',
        regions: ['秦淮区', '建邺区'],
        evidence_count: 15,
        dispatched: false,
      },
      {
        id: 'OR-003',
        level: 'orange',
        title: '电梯加装业主矛盾聚集',
        summary: '同一小区低层业主联合反对加装方案，存在群体性事件苗头，建议属地提前介入。',
        trigger: '集中爆发式诉求 + 对立情绪指数 0.72',
        regions: ['玄武区'],
        evidence_count: 9,
        dispatched: false,
      },
      {
        id: 'RD-004',
        level: 'red',
        title: '南部片区供暖管网故障影响面扩大',
        summary: '供暖管线爆裂影响 3 个小区供热，伴随医疗与退费诉求，需应急抢修联动。',
        trigger: '公共安全关键词 + 紧急件自动标记',
        regions: ['雨花台区'],
        evidence_count: 12,
        dispatched: true,
        dispatched_to: '住建局应急专班',
      },
    ],
    notices: [
      {
        id: 'N4001',
        title: '大厅高峰预约分流公告',
        content: '10 月 15 日起 9:00-11:00 实行预约分流，请优先线上取号。',
        status: 'published',
        scope: '全渠道',
        channel: '短信 + APP 推送',
        sent_count: 1284,
        read_rate: 0.76,
        updated_at: mockUtc(2, 9, 0),
      },
      {
        id: 'N4002',
        title: '叫号系统故障应急说明',
        content: '今日上午 9:20-10:05 叫号系统临时故障，已恢复正常。',
        status: 'draft',
        scope: '大厅广播',
        channel: '现场广播',
        sent_count: 0,
        read_rate: 0,
        updated_at: mockUtc(0, 2, 30),
      },
      {
        id: 'N4003',
        title: '就业补贴申领细则更新提醒',
        content: '高校毕业生就业补贴申领细则已更新，请按最新材料清单申报。',
        status: 'published',
        scope: '栖霞区 + 秦淮区',
        channel: '政务网 + 短信',
        sent_count: 862,
        read_rate: 0.91,
        updated_at: mockUtc(1, 7, 20),
      },
    ],
    audits: [
      { id: 'A5001', action: '导出诉求分级报告', operator: '系统管理员', time: timeStr(0, 10, 12), target: '诉求分级报表' },
      { id: 'A5002', action: '发布政策告知', operator: '政务内容组-何静', time: timeStr(2, 9, 1), target: 'N4001' },
      { id: 'A5003', action: '修改督办状态', operator: '运营管理组-张莉', time: timeStr(1, 16, 40), target: '二级督办-叫号跳号' },
      { id: 'A5004', action: '生成治理任务', operator: '系统管理员', time: timeStr(1, 11, 5), target: 'GT-2601 加装电梯' },
      { id: 'A5005', action: '删除草稿', operator: '政务内容组-何静', time: timeStr(2, 14, 22), target: '草稿-政策问答' },
    ],
    updated_at: new Date().toISOString(),
  }
}