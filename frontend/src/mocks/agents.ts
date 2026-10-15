import type { AgentStatus, AgentToolDef, SkillDef, WorkflowCatalogItem } from '@/types'

/**
 * 预置 Agent 列表（Mock）：
 * 供总览驾驶舱「Agent 与工作流」状态卡与后续「Agent 配置中心」复用。
 * 理念：Agent 不是孤立展示，而是可开关、可指派工具与工作流、
 * 与自动化/资源/工作流配置形成闭环的执行单元。
 */
const hoursAgo = (n: number) => new Date(Date.now() - n * 3600_000).toISOString()

export function getAgentStatuses(): AgentStatus[] {
  return [
    {
      id: 'AG-001',
      name: '政策公告 Agent',
      category: '内容生成',
      scenario: '根据政策变化自动草拟对外公告，联动发布公告工作流',
      enabled: true,
      tools: ['查政策库', '生成公告稿', '发送通知'],
      bound_workflow_ids: ['WF-PUBLISH-NOTICE'],
      run_count: 126,
      reliability: 96,
      last_run_at: hoursAgo(3),
      preset: true,
    },
    {
      id: 'AG-002',
      name: '商单回复 Agent',
      category: '回复生成',
      scenario: '对接企业商机与询价反馈，生成专业报价与跟进话术',
      enabled: true,
      tools: ['查商务线索', '生成回复', '更新跟进状态'],
      bound_workflow_ids: ['WF-LEAD-REPLY'],
      run_count: 84,
      reliability: 93,
      last_run_at: hoursAgo(6),
      preset: true,
    },
    {
      id: 'AG-003',
      name: '舆情聚类 Agent',
      category: '分析研判',
      scenario: '多条舆论指向同一论点时自动聚类，形成统一处置建议',
      enabled: true,
      tools: ['文本聚类', '情感分析', '生成处置建议'],
      bound_workflow_ids: ['WF-SENTIMENT-ALERT'],
      run_count: 210,
      reliability: 91,
      last_run_at: hoursAgo(1),
      preset: true,
    },
    {
      id: 'AG-004',
      name: '邻里诉求 Agent',
      category: '诉求处置',
      scenario: '专门处理邻里纠纷类诉求，按属地映射到社区网格',
      enabled: false,
      tools: ['诉求分级', '属地派单', '生成回复'],
      bound_workflow_ids: ['WF-NEIGHBOR-REQ'],
      run_count: 32,
      reliability: 88,
      last_run_at: hoursAgo(48),
      preset: true,
    },
    {
      id: 'AG-005',
      name: '反馈自动回复 Agent',
      category: '回复生成',
      scenario: '对高频咨询自动生成规范回复草稿，进入人工审批队列',
      enabled: true,
      tools: ['知识库检索', '话术生成', '审批入队'],
      bound_workflow_ids: ['WF-AUTO-REPLY'],
      run_count: 402,
      reliability: 97,
      last_run_at: hoursAgo(0.5),
      preset: true,
    },
  ]
}

/**
 * Agent 可配置工具目录（Mock）：
 * 供 Agent 配置中心「配置工具」抽屉勾选，与真实工具/工作流能力对应。
 * 工具即 Agent 可调用的原子能力，绑定后 Agent 才能在对应场景闭环执行。
 */
export function getAgentToolCatalog(): AgentToolDef[] {
  return [
    { key: 'police-search', name: '查政策库', category: '检索', description: '检索最新政策文件与解读，作为公告与回复的事实依据' },
    { key: 'db-query', name: '查数据库', category: '检索', description: '按自然语言查询反馈库/工单库，聚合统计口径' },
    { key: 'kb-search', name: '知识库检索', category: '检索', description: '检索产品知识库与历史回复，提升话术一致性' },
    { key: 'gov-compile', name: '生成公告稿', category: '生成', description: '按政策主题与面向对象生成规范公告草稿' },
    { key: 'reply-gen', name: '生成回复', category: '生成', description: '面向客户咨询/商单生成专业回复草稿' },
    { key: 'tone-gen', name: '话术生成', category: '生成', description: '基于情感与对象调整沟通话术与语气' },
    { key: 'cluster', name: '文本聚类', category: '分析', description: '对多条反馈/舆论做主题聚类，识别共性论点' },
    { key: 'sentiment', name: '情感分析', category: '分析', description: '判断反馈与舆论的情感倾向与强度' },
    { key: 'advice-gen', name: '生成处置建议', category: '分析', description: '综合聚类与情感结果生成统一处置建议' },
    { key: 'level-classify', name: '诉求分级', category: '处置', description: '按紧急度/影响面/区域对诉求分级' },
    { key: 'dispatch', name: '属地派单', category: '处置', description: '将诉求按属地/部门自动映射派单' },
    { key: 'approval-enqueue', name: '审批入队', category: '处置', description: '将生成草稿推入人工审批队列并附加依据' },
    { key: 'lead-update', name: '更新跟进状态', category: '处置', description: '更新商务线索跟进阶段与备注' },
    { key: 'notify', name: '发送通知', category: '通知', description: '通过站内信/短信/公众号推送结果' },
    { key: 'publish', name: '发布公告', category: '通知', description: '将审批通过的公告发布到对内/对外渠道' },
  ]
}

/** 工作流目录（Agent 配置中心绑定用；工作流配置页同源复用） */
export function getWorkflowCatalog(): WorkflowCatalogItem[] {
  return [
    { id: 'WF-AUTO-REPLY', name: '反馈自动回复', description: '新反馈入队 → AI 草拟 → 人工审批 → 回传' },
    { id: 'WF-LEAD-REPLY', name: '商单自动回复', description: '线索识别 → 报价/话术生成 → 跟进状态更新' },
    { id: 'WF-SENTIMENT-ALERT', name: '舆情监测与应急', description: '文本聚类 → 情感分析 → 预警 → 处置建议' },
    { id: 'WF-PUBLISH-NOTICE', name: '发布公告工作流', description: '政策检索 → 公告草拟 → 审批 → 渠道发布' },
    { id: 'WF-NEIGHBOR-REQ', name: '邻里诉求解决', description: '诉求分级 → 属地派单 → 回复生成 → 回访归档' },
    { id: 'WF-GOV-AGGREGATE', name: '多源诉求聚合', description: '多来源聚合 → 去重 → 共性分析 → 督办闭环' },
  ]
}

/**
 * Skill 目录（Mock）：
 * 面向业务场景预置的领域能力包，可由 Agent 加载后使用。
 * 理念：Skill 不是静态说明，而是 Agent 的执行能力来源——政务/商务/舆情
 * 等场景在 Agent/Skill 配置中心即可新建、启停、指派给 Agent。
 */
export function getSkillCatalog(): SkillDef[] {
  return [
    { id: 'SK-POLICY-COMPOSE', name: '政务公告撰写', category: '政务', description: '基于政策库与公告模板撰写规范对外公告', enabled: true, owner_agent_ids: ['AG-001'] },
    { id: 'SK-LEAD-REPLY', name: '商单报价回复', category: '商务', description: '结合产品目录生成报价与跟进话术', enabled: true, owner_agent_ids: ['AG-002'] },
    { id: 'SK-OPINION-CLUSTER', name: '舆情聚类研判', category: '分析', description: '多条舆论论点聚类与情感研判，输出统一处置建议', enabled: true, owner_agent_ids: ['AG-003'] },
    { id: 'SK-NEIGHBOR-DISPATCH', name: '邻里诉求派单', category: '诉求处置', description: '邻里纠纷分级与属地网格派单', enabled: true, owner_agent_ids: ['AG-004'] },
    { id: 'SK-FAQ-AUTOREPLY', name: '高频咨询自动回复', category: '回复生成', description: '高频咨询知识库检索与话术生成', enabled: true, owner_agent_ids: ['AG-005'] },
    { id: 'SK-INTERVIEW-EXTRACT', name: '访谈纪要提炼', category: '分析', description: '访谈纪要痛点/需求提炼，联动商务线索', enabled: true, owner_agent_ids: [] },
    { id: 'SK-SUPERVISION-REMIND', name: '督办事项提醒', category: '政务', description: '超期与临期督办事项自动提醒与升级', enabled: false, owner_agent_ids: [] },
  ]
}