/**
 * AI 工作台 Mock 数据层：工作流状态、自动化规则、对话响应。
 * 所有数据均基于公开的政企服务场景生成，不涉及真实客户隐私。
 */

import type {
  AIAutomationRule,
  AIChatMessage,
  AIWorkflowStatus,
  DashboardMetrics,
} from '@/types'
import { computeDashboardMetrics } from './dashboard'

/** AI 工作流运行状态（动态生成，每次调用有微小变化） */
export function getAIWorkflows(): AIWorkflowStatus[] {
  const now = new Date()
  return [
    {
      id: 'wf-001',
      name: '工单智能分类',
      status: 'running',
      progress: 67,
      started_at: new Date(now.getTime() - 12 * 60000).toISOString(),
      eta: '约 3 分钟',
      detail: '正在对今日 12 条新工单进行主题聚类与优先级评估',
    },
    {
      id: 'wf-002',
      name: '舆情情感监测',
      status: 'running',
      progress: 45,
      started_at: new Date(now.getTime() - 25 * 60000).toISOString(),
      eta: '约 8 分钟',
      detail: '分析近 7 天热线与门户反馈情感倾向',
    },
    {
      id: 'wf-003',
      name: '重复问题自动汇总',
      status: 'completed',
      progress: 100,
      started_at: new Date(now.getTime() - 60 * 60000).toISOString(),
      detail: '已识别 3 组高频重复提问，生成统一话术建议',
    },
    {
      id: 'wf-004',
      name: '政策知识库同步',
      status: 'queued',
      progress: 0,
      started_at: now.toISOString(),
      detail: '等待夜间批量更新窗口（02:00）',
    },
    {
      id: 'wf-005',
      name: '高优先级自动升级',
      status: 'running',
      progress: 82,
      started_at: new Date(now.getTime() - 5 * 60000).toISOString(),
      eta: '约 1 分钟',
      detail: '检测到 1 条 P5 级投诉，正在推送值班负责人',
    },
  ]
}

/** AI 自动化规则（面向政企场景） */
export function getAIAutomationRules(): AIAutomationRule[] {
  return [
    {
      id: 'rule-001',
      name: '自动分类新工单',
      description: '根据内容关键词与历史聚类模型，自动为新提交工单分配主题标签与优先级',
      enabled: true,
      scenario: '工单接入',
      icon: 'tags',
      tone: 'primary',
      stats: '今日已自动分类 12 条',
    },
    {
      id: 'rule-002',
      name: '重复问题自动回复',
      description: '对匹配到知识库高频问答模板的工单，自动生成统一规范回复并进入待审批队列',
      enabled: true,
      scenario: '回复生成',
      icon: 'message',
      tone: 'success',
      stats: '今日已命中 5 条',
    },
    {
      id: 'rule-003',
      name: '高优先级自动升级',
      description: 'P4+ 工单或情感极负面反馈，自动推送至值班负责人并生成督办任务',
      enabled: true,
      scenario: '风险预警',
      icon: 'alert',
      tone: 'warning',
      stats: '今日已升级 2 条',
    },
    {
      id: 'rule-004',
      name: '情感负面实时预警',
      description: '监测热线/门户/评价渠道，连续出现负面情感反馈时触发预警通知',
      enabled: false,
      scenario: '舆情监测',
      icon: 'sentiment',
      tone: 'danger',
      stats: '上次触发：昨天 14:32',
    },
    {
      id: 'rule-005',
      name: '材料清单智能校验',
      description: '根据办理事项自动匹配所需材料清单，发现重复提交时提示历史材料复用',
      enabled: true,
      scenario: '办事辅助',
      icon: 'checklist',
      tone: 'info',
      stats: '本月减少重复提交 38 次',
    },
    {
      id: 'rule-006',
      name: '预约爽约自动提醒',
      description: '预约前 1 小时通过短信/APP 推送提醒，爽约后自动释放号源',
      enabled: false,
      scenario: '预约管理',
      icon: 'clock',
      tone: 'info',
      stats: '待启用',
    },
  ]
}

/** 基于当前数据生成 AI 对话回复 */
function buildReply(metrics: DashboardMetrics, query: string): string {
  const q = query.toLowerCase()

  if (q.includes('工单') || q.includes('情况') || q.includes('多少') || q.includes('今天')) {
    return (
      `今日工单概览：\n` +
      `• 新接入工单 **${metrics.total_feedbacks}** 条，待处理 **${metrics.pending}** 条\n` +
      `• 高优先级（P4+）**${metrics.high_priority}** 条，已解决 **${metrics.resolved_today}** 条\n` +
      `• 平均解决时长 **${metrics.avg_resolve_hours}** 小时\n` +
      `• 主要渠道：热线 ${Math.round(metrics.total_feedbacks * 0.35)} 条、工单系统 ${Math.round(metrics.total_feedbacks * 0.25)} 条、门户 ${Math.round(metrics.total_feedbacks * 0.2)} 条\n\n` +
      `如需下钻到具体工单列表，请点击下方「反馈管理」导航。`
    )
  }

  if (q.includes('自动') || q.includes('规则') || q.includes('配置')) {
    return (
      `当前已启用 4 项自动化规则：\n` +
      `1. **自动分类新工单** — 今日已自动处理 12 条\n` +
      `2. **重复问题自动回复** — 命中 5 条高频问答\n` +
      `3. **高优先级自动升级** — 已升级 2 条至值班负责人\n` +
      `4. **材料清单智能校验** — 本月减少重复提交 38 次\n\n` +
      `您可以在「洞察与决策」→「AI 自动化」中调整规则开关与阈值。`
    )
  }

  if (q.includes('流程') || q.includes('工作流') || q.includes('状态')) {
    return (
      `当前有 3 个工作流正在运行：\n` +
      `• 工单智能分类（67%）— 预计 3 分钟完成\n` +
      `• 舆情情感监测（45%）— 预计 8 分钟完成\n` +
      `• 高优先级自动升级（82%）— 预计 1 分钟完成\n\n` +
      `另有 1 项已完成（重复问题汇总），1 项等待夜间窗口执行。`
    )
  }

  if (q.includes('政策') || q.includes('知识库') || q.includes('回复')) {
    return (
      `知识库目前涵盖以下政策领域（本地模拟数据）：\n` +
      `• 社保转移与异地就医备案\n` +
      `• 房屋租赁备案与不动产登记\n` +
      `• 生育津贴与灵活就业参保\n` +
      `• 企业年金与营业执照变更\n\n` +
      `对于高频咨询问题，AI 已生成标准化话术模板 12 套，可直接用于自动回复或审批建议。`
    )
  }

  if (q.includes('推荐') || q.includes('建议') || q.includes('怎么')) {
    return (
      `基于当前数据，我建议优先关注以下事项：\n` +
      `1. **大厅等候时间**仍是首要痛点（11 条反馈，强度 90），建议推进「动态开窗」优化任务\n` +
      `2. **材料重复提交**问题突出，可优先启用「材料清单智能校验」规则\n` +
      `3. 今日有 **${metrics.high_priority}** 条高优先级工单未处理，其中 1 条已触发自动升级\n\n` +
      `需要我帮您起草具体整改方案或生成回复话术吗？`
    )
  }

  return (
    `您好，我是 SignalFlow 智能助手，可以帮助您：\n` +
    `• 查询工单概况与统计数据\n` +
    `• 查看 AI 工作流运行状态与自动化规则\n` +
    `• 检索政策知识库并生成标准化回复\n` +
    `• 提供整改建议与优先级排序\n\n` +
    `请问今天需要我协助处理什么？您可以尝试输入「今天工单情况」「自动回复怎么配置」「大厅排队怎么解决」等。`
  )
}

let messageId = 0
function nextId() {
  messageId += 1
  return `msg-${String(messageId).padStart(3, '0')}`
}

/** AI 对话：接收用户输入，返回助手回复（mock 工作流） */
export async function sendAIChat(query: string, _history: AIChatMessage[]): Promise<AIChatMessage> {
  const metrics = computeDashboardMetrics()
  const reply = buildReply(metrics, query)

  // 模拟工作流调用延迟（根据查询复杂度）
  const delay = Math.min(600 + query.length * 8, 1800)
  await new Promise((r) => setTimeout(r, delay))

  return {
    id: nextId(),
    role: 'assistant',
    content: reply,
    timestamp: new Date().toISOString(),
    workflow_refs: ['wf-001', 'wf-002'],
    sources: ['知识库 v2026.10', '工单数据库', '政策文件库'],
  }
}

/** AI 初始欢迎语 */
export function getAIWelcomeMessage(): AIChatMessage {
  return {
    id: nextId(),
    role: 'assistant',
    content:
      '您好，我是 SignalFlow 智能助手。\n' +
      '我可以帮您查询工单统计、查看 AI 工作流状态、检索政策知识库，或根据历史数据给出整改建议。\n' +
      '试试问我「今天工单情况如何」或「最近有什么高频问题」。',
    timestamp: new Date().toISOString(),
  }
}

/** 基于反馈内容生成 AI 回复草稿（模拟知识库检索） */
export async function generateAIReply(content: string): Promise<string> {
  const delay = Math.min(400 + content.length * 6, 1500)
  await new Promise((r) => setTimeout(r, delay))

  const lower = content.toLowerCase()

  if (lower.includes('排队') || lower.includes('等候') || lower.includes('叫号')) {
    return (
      '您好，关于大厅排队等候问题，我们已记录并反馈至运营管理组。\n\n' +
      '当前已采取以下措施：\n' +
      '1. 高峰期（9:00-11:00, 14:00-16:00）已增开 2 个综合窗口\n' +
      '2. 叫号系统已升级，新增微信实时排队提醒功能\n' +
      '3. 针对老年群体，保留人工取号通道并提供优先服务\n\n' +
      '预计下周五前完成动态开窗系统的联调测试，届时将根据实时客流自动调整开放窗口数量。\n' +
      '如需进一步协助，请拨打服务热线 12345 或到 2 号窗口咨询。'
    )
  }

  if (lower.includes('材料') || lower.includes('重复') || lower.includes('复印')) {
    return (
      '您好，关于材料重复提交的问题，我们正在推进「一网通办」材料共享机制。\n\n' +
      '目前可采取以下方式减少重复提交：\n' +
      '1. 通过「政务通」APP 完成实名认证后，系统自动调取电子证照\n' +
      '2. 同类型业务在 30 天内可使用历史材料，无需重复提交\n' +
      '3. 房屋租赁备案、社保转移等高频事项已接入材料复用接口\n\n' +
      '如需查询您的历史材料清单或申请电子证照调用，可到 5 号窗口办理，或致电 12345 按 3 号键转接材料审核专席。'
    )
  }

  if (lower.includes('预约') || lower.includes('爽约') || lower.includes('取消')) {
    return (
      '您好，关于预约系统相关问题，我们已核实并处理。\n\n' +
      '说明如下：\n' +
      '1. 预约成功后系统将在办理前 1 小时发送短信提醒\n' +
      '2. 如因故无法到场，请提前 2 小时在 APP 或网站取消预约\n' +
      '3. 连续 3 次爽约将暂停预约权限 7 天，现场取号不受影响\n\n' +
      '如需重新预约或查询预约记录，请登录「政务服务网」→「我的预约」，或拨打 12345 按 2 号键。'
    )
  }

  if (lower.includes('政策') || lower.includes('咨询') || lower.includes('答复')) {
    return (
      '您好，关于政策咨询问题，已转接至政策解读专员处理。\n\n' +
      '根据您的问题类型，相关政策如下：\n' +
      '• 社保转移：需在原参保地开具《参保缴费凭证》，至现参保地申请转入\n' +
      '• 生育津贴：连续缴费满 12 个月且生育时参保状态正常即可申领\n' +
      '• 异地就医备案：可通过「国家医保服务平台」APP 在线办理\n\n' +
      '如需获取完整政策文件或申请一对一政策解读，请拨打 12345 按 5 号键，或到 3 号窗口「政策咨询专席」办理。'
    )
  }

  return (
    '您好，感谢您的反馈。我们已收到您的诉求并安排专人跟进处理。\n\n' +
    '通常处理时效：\n' +
    '• 一般咨询类：1-2 个工作日\n' +
    '• 业务办理类：3-5 个工作日\n' +
    '• 投诉建议类：5-7 个工作日\n\n' +
    '您可通过以下方式查询进度：\n' +
    '1. 「政务服务网」→「我的工单」输入编号查询\n' +
    '2. 拨打 12345 按 1 号键查询工单状态\n' +
    '3. 关注微信公众号「XX政务」，绑定后实时接收进度推送\n\n' +
    '再次感谢您的监督与支持，我们将持续改进服务质量。'
  )
}

/** AI 气泡助手：根据反馈内容给出回复建议（更简短的提示） */
export async function getAIReplySuggestion(content: string): Promise<string> {
  await new Promise((r) => setTimeout(r, 300))

  const lower = content.toLowerCase()

  if (lower.includes('排队') || lower.includes('等候')) {
    return '建议回复：已增开窗口+叫号升级+老人优先通道，预计下周五完成动态开窗系统联调。'
  }
  if (lower.includes('材料') || lower.includes('重复')) {
    return '建议回复：推行政务通 APP 电子证照自动调取，同类型业务 30 天内免重复提交。'
  }
  if (lower.includes('预约')) {
    return '建议回复：说明预约提醒机制、取消规则及爽约处理政策，提供重新预约入口。'
  }
  if (lower.includes('态度') || lower.includes('服务')) {
    return '建议回复：致歉+承诺加强培训+提供投诉渠道，必要时安排回访。'
  }
  if (lower.includes('app') || lower.includes('手机') || lower.includes('闪退')) {
    return '建议回复：收集设备型号与系统版本，提供临时解决方案（网页版/电话预约），承诺技术修复。'
  }
  return '建议回复：确认收到诉求+说明处理时效+提供查询渠道+表达感谢与改进决心。'
}

// ---------- 自动化中心 Mock 数据 ----------

import type {
  AutoClassificationResult,
  DedupGroup,
  PriorityRule,
  PriorityAdjustment,
  AutomationExecutionSummary,
} from '@/types'

/** 自动分类结果模拟 */
export function getAutoClassificationResults(): AutoClassificationResult[] {
  return [
    {
      feedback_id: 'F1061',
      content: '大厅排队时间太长，等了快两个小时还没叫到号，希望能增加窗口。',
      suggested_topic: '大厅等候时间',
      confidence: 0.94,
      alternatives: [
        { topic: '叫号系统', confidence: 0.78 },
        { topic: '人员配置', confidence: 0.62 },
      ],
      needs_review: false,
      processed_at: new Date().toISOString(),
    },
    {
      feedback_id: 'F1062',
      content: '窗口工作人员态度恶劣，问了两句话就不耐烦了。',
      suggested_topic: '服务态度',
      confidence: 0.89,
      alternatives: [
        { topic: '投诉建议', confidence: 0.71 },
        { topic: '人员培训', confidence: 0.55 },
      ],
      needs_review: false,
      processed_at: new Date().toISOString(),
    },
    {
      feedback_id: 'F1063',
      content: '社保转移需要什么材料？我已经在原参保地开了证明，接下来怎么做？',
      suggested_topic: '社保转移',
      confidence: 0.67,
      alternatives: [
        { topic: '材料清单', confidence: 0.58 },
        { topic: '异地就医', confidence: 0.41 },
      ],
      needs_review: true,
      processed_at: new Date().toISOString(),
      reviewer_note: '涉及材料+流程，建议拆分为「社保转移」+「材料清单」两个主题',
    },
    {
      feedback_id: 'F1064',
      content: 'APP 总是闪退，一提交材料就卡死，安卓手机。',
      suggested_topic: '系统故障',
      confidence: 0.91,
      alternatives: [
        { topic: 'APP 使用', confidence: 0.83 },
        { topic: '材料提交', confidence: 0.45 },
      ],
      needs_review: false,
      processed_at: new Date().toISOString(),
    },
    {
      feedback_id: 'F1065',
      content: '昨天预约了今天 9 点的号，结果窗口没开，白跑一趟。',
      suggested_topic: '预约管理',
      confidence: 0.72,
      alternatives: [
        { topic: '窗口开放', confidence: 0.68 },
        { topic: '通知服务', confidence: 0.51 },
      ],
      needs_review: true,
      processed_at: new Date().toISOString(),
      reviewer_note: '涉及爽约+窗口开放，需确认是否为预约系统同步问题',
    },
    {
      feedback_id: 'F1066',
      content: '生育津贴怎么领？需要连续缴费多久？',
      suggested_topic: '生育津贴',
      confidence: 0.88,
      alternatives: [
        { topic: '社保政策', confidence: 0.74 },
        { topic: '灵活就业', confidence: 0.33 },
      ],
      needs_review: false,
      processed_at: new Date().toISOString(),
    },
    {
      feedback_id: 'F1067',
      content: '同样的事情要跑好几趟，每次带的材料都差不多，为什么不能共享？',
      suggested_topic: '材料重复提交',
      confidence: 0.95,
      alternatives: [
        { topic: '一网通办', confidence: 0.81 },
        { topic: '信息共享', confidence: 0.76 },
      ],
      needs_review: false,
      processed_at: new Date().toISOString(),
    },
    {
      feedback_id: 'F1068',
      content: '咨询一下企业年金的相关政策，公司打算给上。',
      suggested_topic: '企业年金',
      confidence: 0.58,
      alternatives: [
        { topic: '社保政策', confidence: 0.52 },
        { topic: '养老保险', confidence: 0.48 },
      ],
      needs_review: true,
      processed_at: new Date().toISOString(),
      reviewer_note: '置信度偏低，需人工确认是否归入「社保政策」大类',
    },
  ]
}

/** 去重合并组模拟 */
export function getDedupGroups(): DedupGroup[] {
  return [
    {
      group_id: 'DG-001',
      representative_id: 'F1001',
      members: [
        { feedback_id: 'F1001', content: '大厅排队时间太长，建议增加窗口', similarity: 1.0 },
        { feedback_id: 'F1003', content: '等了两个小时，排队系统能不能优化一下', similarity: 0.91 },
        { feedback_id: 'F1005', content: '高峰期窗口太少，建议增派人手', similarity: 0.87 },
        { feedback_id: 'F1007', content: '排队叫号太慢，老年人站不住', similarity: 0.84 },
      ],
      merged_topic: '大厅等候时间',
      status: 'merged',
      merged_at: new Date().toISOString(),
      repeat_count: 4,
    },
    {
      group_id: 'DG-002',
      representative_id: 'F1002',
      members: [
        { feedback_id: 'F1002', content: '材料需要重复提交，上次办过的还要重新复印', similarity: 1.0 },
        { feedback_id: 'F1004', content: '同样的材料交了好几遍，不同窗口要求不一样', similarity: 0.93 },
        { feedback_id: 'F1006', content: '复印件都带了，说格式不对要重新复印', similarity: 0.78 },
      ],
      merged_topic: '材料重复提交',
      status: 'merged',
      merged_at: new Date().toISOString(),
      repeat_count: 3,
    },
    {
      group_id: 'DG-003',
      representative_id: 'F1062',
      members: [
        { feedback_id: 'F1062', content: '窗口工作人员态度恶劣，问了两句话就不耐烦了。', similarity: 1.0 },
        { feedback_id: 'F1010', content: '工作人员态度很差，咨询问题爱答不理', similarity: 0.89 },
      ],
      merged_topic: '服务态度',
      status: 'pending',
      repeat_count: 2,
    },
    {
      group_id: 'DG-004',
      representative_id: 'F1064',
      members: [
        { feedback_id: 'F1064', content: 'APP 总是闪退，一提交材料就卡死，安卓手机。', similarity: 1.0 },
        { feedback_id: 'F1012', content: '手机 APP 打开就闪退，根本用不了', similarity: 0.85 },
        { feedback_id: 'F1015', content: '安卓版 APP 频繁崩溃，什么时候修复', similarity: 0.82 },
      ],
      merged_topic: 'APP 闪退/崩溃',
      status: 'pending',
      repeat_count: 3,
    },
    {
      group_id: 'DG-005',
      representative_id: 'F1016',
      members: [
        { feedback_id: 'F1016', content: '预约了号结果爽约，系统没有提醒', similarity: 1.0 },
        { feedback_id: 'F1065', content: '昨天预约了今天 9 点的号，结果窗口没开，白跑一趟。', similarity: 0.74 },
      ],
      merged_topic: '预约爽约/提醒缺失',
      status: 'pending',
      repeat_count: 2,
    },
  ]
}

/** 优先级规则模拟（RICE 模型） */
export function getPriorityRules(): PriorityRule[] {
  return [
    {
      id: 'pr-001',
      name: '高负面情感自动升级',
      enabled: true,
      description: '当单条反馈被识别为强烈负面情感（置信度>0.85）且涉及服务态度/投诉时，自动上调优先级至 P4+',
      factors: [
        { key: 'reach', label: '影响范围', weight: 0.25, value: 85, max: 100, note: '负面情感易在社交平台扩散' },
        { key: 'impact', label: '影响深度', weight: 0.30, value: 90, max: 100, note: '直接关系群众对政务服务的信任度' },
        { key: 'confidence', label: '置信度', weight: 0.25, value: 88, max: 100, note: '情感识别模型准确率' },
        { key: 'effort', label: '解决成本', weight: 0.20, value: 30, max: 100, note: '培训+流程优化即可改善，成本较低' },
      ],
      threshold: 80,
      auto_escalate: true,
      updated_at: new Date().toISOString(),
    },
    {
      id: 'pr-002',
      name: '高频重复问题优先处理',
      enabled: true,
      description: '当周累计出现 3 次以上的同类重复反馈，自动提升处理优先级并触发标准化回复模板',
      factors: [
        { key: 'reach', label: '影响范围', weight: 0.30, value: 80, max: 100, note: '高频 = 多用户受影响' },
        { key: 'impact', label: '影响深度', weight: 0.25, value: 65, max: 100, note: '多为流程/系统问题，解决后满意度提升明显' },
        { key: 'confidence', label: '置信度', weight: 0.20, value: 92, max: 100, note: '去重组准确率' },
        { key: 'effort', label: '解决成本', weight: 0.25, value: 55, max: 100, note: '需协调多部门，中等成本' },
      ],
      threshold: 70,
      auto_escalate: true,
      updated_at: new Date().toISOString(),
    },
    {
      id: 'pr-003',
      name: '系统故障类紧急响应',
      enabled: true,
      description: 'APP/系统宕机、闪退、无法提交材料等技术故障，立即标记为紧急并通知技术团队',
      factors: [
        { key: 'reach', label: '影响范围', weight: 0.35, value: 95, max: 100, note: '线上渠道瘫痪影响所有线上用户' },
        { key: 'impact', label: '影响深度', weight: 0.30, value: 90, max: 100, note: '阻断业务办理，影响群众办事体验' },
        { key: 'confidence', label: '置信度', weight: 0.15, value: 85, max: 100, note: '技术故障关键词识别准确率' },
        { key: 'effort', label: '解决成本', weight: 0.20, value: 70, max: 100, note: '需技术团队介入，排查修复周期不确定' },
      ],
      threshold: 85,
      auto_escalate: true,
      updated_at: new Date().toISOString(),
    },
    {
      id: 'pr-004',
      name: '政策咨询类常规处理',
      enabled: true,
      description: '一般性政策咨询（社保、医保、公积金等），使用标准化话术自动回复并归入知识库',
      factors: [
        { key: 'reach', label: '影响范围', weight: 0.20, value: 60, max: 100, note: '单个用户咨询，影响范围有限' },
        { key: 'impact', label: '影响深度', weight: 0.20, value: 50, max: 100, note: '信息性问题，不直接涉及服务缺陷' },
        { key: 'confidence', label: '置信度', weight: 0.30, value: 90, max: 100, note: '政策类关键词匹配准确率高' },
        { key: 'effort', label: '解决成本', weight: 0.30, value: 15, max: 100, note: '知识库话术可直接回复，成本低' },
      ],
      threshold: 45,
      auto_escalate: false,
      updated_at: new Date().toISOString(),
    },
  ]
}

/** 优先级调整记录模拟 */
export function getPriorityAdjustments(): PriorityAdjustment[] {
  return [
    {
      feedback_id: 'F1062',
      old_priority: 2,
      new_priority: 5,
      reason: '情感负面置信度 0.94，触发「高负面情感自动升级」规则',
      triggered_by: 'pr-001',
      adjusted_at: new Date(Date.now() - 2 * 3600_000).toISOString(),
    },
    {
      feedback_id: 'F1064',
      old_priority: 1,
      new_priority: 4,
      reason: '系统故障类紧急响应规则命中：APP 闪退关键词 + 安卓设备',
      triggered_by: 'pr-003',
      adjusted_at: new Date(Date.now() - 1 * 3600_000).toISOString(),
    },
    {
      feedback_id: 'F1001',
      old_priority: 2,
      new_priority: 4,
      reason: '大厅等候时间属于高频重复问题（本周 11 次），触发自动升级',
      triggered_by: 'pr-002',
      adjusted_at: new Date(Date.now() - 4 * 3600_000).toISOString(),
    },
    {
      feedback_id: 'F1061',
      old_priority: 3,
      new_priority: 3,
      reason: '分类后重新评估，大厅等候时间与已有洞察主题一致，保持当前优先级',
      triggered_by: 'pr-002',
      adjusted_at: new Date(Date.now() - 30 * 60_000).toISOString(),
    },
  ]
}

/** 自动化执行概览模拟 */
export function getAutomationExecutionSummary(): AutomationExecutionSummary {
  const today = new Date().toISOString().slice(0, 10)
  return {
    date: today,
    classified_count: 47,
    review_queue_count: 6,
    deduped_group_count: 12,
    saved_feedback_count: 31,
    priority_adjusted_count: 8,
    auto_escalated_count: 3,
    avg_confidence: 0.84,
    manual_review_rate: 0.128,
  }
}

// ---------- 商务洞察（企业合作信息提炼与市场动向）Mock 数据 ----------

import type {
  BusinessInsightSummary,
  BusinessLead,
  CommonNeed,
  IndustryShare,
  MarketSignal,
} from '@/types'

/** 企业合作线索模拟（推销联动：从反馈语义匹配产品目录） */
export function getBusinessLeads(): BusinessLead[] {
  return [
    {
      id: 'BL-001',
      feedback_id: 'F1101',
      content: '我们公司有 400 多名设计师，现在每人单独建账号太麻烦，希望支持批量导入和角色分组。',
      company_name: '云帆数字设计',
      industry: '企业服务',
      company_type: '私企',
      size_band: '500-2000 人',
      matched_product: '企业版·批量账号管理',
      match_reason: '反馈提及「批量导入 + 角色分组」，与企业版多人协作能力语义匹配',
      value_score: 82,
      confidence: 0.91,
      stage: 'pushed',
      created_at: new Date(Date.now() - 2 * 86400_000).toISOString(),
    },
    {
      id: 'BL-002',
      feedback_id: 'F1102',
      content: '作为外包承接方，客户要求我们提供本地化部署版本，敏感数据不能出我们的机房。',
      company_name: '中科软联',
      industry: '软件外包',
      company_type: '私企',
      size_band: '200-500 人',
      matched_product: '私有化部署包',
      match_reason: '反馈提出「本地化部署 + 数据不出域」，匹配私有化版本需求',
      value_score: 78,
      confidence: 0.88,
      stage: 'qualified',
      created_at: new Date(Date.now() - 3 * 86400_000).toISOString(),
    },
    {
      id: 'BL-003',
      feedback_id: 'F1103',
      content: '我们是省属国企，需要和内部 OA、统一认证对接，账号体系要对齐集团标准。',
      company_name: '华东能源集团',
      industry: '能源化工',
      company_type: '国企',
      size_band: '2000 人以上',
      matched_product: '企业版·SSO/统一认证',
      match_reason: '反馈提及「统一认证 + 集团账号标准」，匹配 SSO 集成能力',
      value_score: 90,
      confidence: 0.95,
      stage: 'pushed',
      created_at: new Date(Date.now() - 5 * 86400_000).toISOString(),
    },
    {
      id: 'BL-004',
      feedback_id: 'F1104',
      content: '想基于贵司报表能力做二次开发，把反馈数据嵌入我们自己的 BI 看板。',
      company_name: '擎天数据科技',
      industry: '数据服务',
      company_type: '私企',
      size_band: '50-200 人',
      matched_product: '开放 API / Webhook',
      match_reason: '反馈提出「二次开发 + 嵌入 BI」，匹配开放 API 与数据集成能力',
      value_score: 68,
      confidence: 0.79,
      stage: 'identified',
      created_at: new Date(Date.now() - 1 * 86400_000).toISOString(),
    },
    {
      id: 'BL-005',
      feedback_id: 'F1105',
      content: '我们是外资企业，要求合同和数据处理符合欧盟 GDPR，需要审计日志和合规报告。',
      company_name: '联达精密制造',
      industry: '智能制造',
      company_type: '外企',
      size_band: '2000 人以上',
      matched_product: '企业版·审计日志与合规',
      match_reason: '反馈提及「GDPR + 审计日志」，匹配合规审计能力',
      value_score: 85,
      confidence: 0.9,
      stage: 'qualified',
      created_at: new Date(Date.now() - 4 * 86400_000).toISOString(),
    },
    {
      id: 'BL-006',
      feedback_id: 'F1106',
      content: '我们学校十几个分院都要用，希望分校级数据隔离，老师只看自己学院的数据。',
      company_name: '南州职业技术学院',
      industry: '教育',
      company_type: '事业单位',
      size_band: '2000 人以上',
      matched_product: '多租户·组织隔离',
      match_reason: '反馈提出「分院隔离 + 数据权限」，匹配多租户组织能力',
      value_score: 74,
      confidence: 0.83,
      stage: 'identified',
      created_at: new Date(Date.now() - 30 * 60_000).toISOString(),
    },
  ]
}

/** 行业分布模拟 */
export function getIndustryShares(): IndustryShare[] {
  return [
    { industry: '企业服务', count: 38, pct: 0.28, trend: 'up' },
    { industry: '智能制造', count: 31, pct: 0.23, trend: 'up' },
    { industry: '教育', count: 24, pct: 0.18, trend: 'flat' },
    { industry: '能源化工', count: 17, pct: 0.12, trend: 'up' },
    { industry: '数据服务', count: 15, pct: 0.11, trend: 'down' },
    { industry: '零售消费', count: 11, pct: 0.08, trend: 'flat' },
  ]
}

/** 市场动向信号模拟 */
export function getMarketSignals(): MarketSignal[] {
  return [
    {
      id: 'MS-001',
      title: '私有化部署需求上升',
      type: 'opportunity',
      summary: '近 30 天「私有化 / 数据不出域」类反馈增长 42%，集中在制造与能源行业，建议重点跟进私有化版本售卖。',
      evidence_count: 23,
      severity: 88,
      related_industries: ['智能制造', '能源化工'],
      created_at: new Date(Date.now() - 6 * 3600_000).toISOString(),
    },
    {
      id: 'MS-002',
      title: '组织隔离成为教育行业刚需',
      type: 'gap',
      summary: '教育机构普遍提出分院/分校数据隔离诉求，当前产品按企业单租户设计，存在能力缺口。',
      evidence_count: 12,
      severity: 76,
      related_industries: ['教育'],
      created_at: new Date(Date.now() - 12 * 3600_000).toISOString(),
    },
    {
      id: 'MS-003',
      title: '开放 API 集成热度回落',
      type: 'shift',
      summary: '「二次开发 / API」类反馈占比由 16% 降至 8%，可能与企业转向成熟集成市场有关，需验证是需求转移还是渠道变化。',
      evidence_count: 9,
      severity: 52,
      related_industries: ['数据服务', '企业服务'],
      created_at: new Date(Date.now() - 18 * 3600_000).toISOString(),
    },
    {
      id: 'MS-004',
      title: '合规审计成为大型企业准入门槛',
      type: 'risk',
      summary: '500 人以上企业客户中 63% 提及审计日志或合规要求，若缺失将影响政企大单准入。',
      evidence_count: 27,
      severity: 81,
      related_industries: ['能源化工', '智能制造', '金融'],
      created_at: new Date(Date.now() - 26 * 3600_000).toISOString(),
    },
  ]
}

/** 共性需求归纳模拟 */
export function getCommonNeeds(): CommonNeed[] {
  return [
    {
      id: 'CN-001',
      title: '批量账号与角色管理',
      description: '大型组织需要批量导入成员、按部门/角色分组授权，减少单账号逐个配置的运维成本。',
      feedback_count: 34,
      customer_count: 12,
      industries: ['企业服务', '能源化工', '教育'],
      product_potential: '企业版·批量账号与 RBAC 角色分组',
      priority: 5,
      status: 'planned',
    },
    {
      id: 'CN-002',
      title: '私有化与数据不出域部署',
      description: '具备合规诉求的政企客户要求本地化部署，数据不允许离开自有机房或堡垒环境。',
      feedback_count: 29,
      customer_count: 9,
      industries: ['智能制造', '能源化工'],
      product_potential: '私有化部署包（Docker/K8s + 本地模型）',
      priority: 5,
      status: 'open',
    },
    {
      id: 'CN-003',
      title: '统一认证与集团账号对接',
      description: '国企与大型集团要求对接内部 OA、统一身份认证，账号体系需对齐集团标准。',
      feedback_count: 18,
      customer_count: 7,
      industries: ['能源化工', '智能制造'],
      product_potential: '企业版·SSO/标准协议联调',
      priority: 4,
      status: 'planned',
    },
    {
      id: 'CN-004',
      title: '审计日志与合规报告',
      description: '受 GDPR / 等保等约束的客户需要完整操作审计、留痕与合规导出能力。',
      feedback_count: 27,
      customer_count: 8,
      industries: ['智能制造', '能源化工', '数据服务'],
      product_potential: '企业版·审计日志与合规报表',
      priority: 4,
      status: 'open',
    },
  ]
}

/** 商务洞察总览（可视化报告头部统计）模拟 */
export function getBusinessInsightSummary(): BusinessInsightSummary {
  const today = new Date()
  const start = new Date(today.getTime() - 29 * 86400_000)
  return {
    total_leads: 6,
    qualified_leads: 3,
    pushed_leads: 2,
    industry_count: 6,
    total_feedback_count: 136,
    customer_count: 58,
    market_signal_count: 4,
    common_need_count: 4,
    report_period: `${start.toISOString().slice(0, 10)} ~ ${today.toISOString().slice(0, 10)}`,
    generated_at: today.toISOString(),
  }
}
