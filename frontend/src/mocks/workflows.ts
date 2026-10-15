import type { WorkflowDetail } from '@/types'

/**
 * 工作流详情（Mock）：
 * 模拟 LangGraph 风格工作流：节点图 + 触发条件 + Agent 绑定 + 工具链 + 运行历史。
 * 理念：工作流不是孤立配置，而是 Agent 执行链路——
 * 总览「工作流运行状态」映射到这里；Agent 配置页指派 Agent 到节点；
 * 工作流异常会在资源管理页回显为告警。
 */
const minsAgo = (n: number) => new Date(Date.now() - n * 60_000).toISOString()

export function getWorkflowDetails(): WorkflowDetail[] {
  return [
    {
      id: 'WF-PUBLISH-NOTICE',
      name: '发布公告',
      description: '监测政策变化 → 草拟公告 → 人工确认 → 多渠道发布。',
      enabled: true,
      trigger: '定时：每日 09:00 检查政策库更新；事件：检测到新政策条目时立即触发',
      nodes: [
        { id: 'n-start', name: '开始', type: 'start', status: 'success' },
        { id: 'n-scan', name: '扫描政策库', type: 'tool', tool_keys: ['policy_search'], status: 'success', description: '检索今日新增/变更政策' },
        { id: 'n-dec', name: '是否有变更', type: 'decision', status: 'success', description: '分支：有变更 → 草拟；无变更 → 结束' },
        { id: 'n-draft', name: '草拟公告', type: 'agent', agent_id: 'AG-001', status: 'success', description: '政策公告 Agent 生成草稿' },
        { id: 'n-review', name: '人工审核', type: 'agent', agent_id: 'AG-001', status: 'success', description: '运营人员确认或修改' },
        { id: 'n-send', name: '发布通知', type: 'tool', tool_keys: ['send_email', 'send_sms'], status: 'success', description: '邮件 + 站内信推送' },
        { id: 'n-end', name: '结束', type: 'end', status: 'success' },
      ],
      edges: [
        { from: 'n-start', to: 'n-scan' },
        { from: 'n-scan', to: 'n-dec' },
        { from: 'n-dec', to: 'n-draft', condition: '有变更' },
        { from: 'n-dec', to: 'n-end', condition: '无变更' },
        { from: 'n-draft', to: 'n-review' },
        { from: 'n-review', to: 'n-send' },
        { from: 'n-send', to: 'n-end' },
      ],
      agent_bindings: { 'n-draft': 'AG-001', 'n-review': 'AG-001' },
      tool_chain: { 'n-scan': ['policy_search'], 'n-send': ['send_email', 'send_sms'] },
      history: [
        { id: 'R-241015-01', started_at: minsAgo(120), ended_at: minsAgo(118), status: 'success', output_summary: '检测到 2 条政策变更，已发布对应公告' },
        { id: 'R-241015-02', started_at: minsAgo(60), ended_at: minsAgo(58), status: 'success', output_summary: '无新增政策变更' },
      ],
      updated_at: minsAgo(1),
    },
    {
      id: 'WF-LEAD-REPLY',
      name: '商单自动回复',
      description: '识别商务线索 → 匹配 Agent → 生成回复草稿 → 人工确认发送。',
      enabled: true,
      trigger: '事件：新线索进入「待跟进」状态；手动：商务人员点击「生成回复」',
      nodes: [
        { id: 'n-start', name: '开始', type: 'start', status: 'success' },
        { id: 'n-match', name: '匹配线索', type: 'tool', tool_keys: ['lead_search'], status: 'success', description: '读取线索详情与历史记录' },
        { id: 'n-reply', name: '生成回复草稿', type: 'agent', agent_id: 'AG-002', status: 'success', description: '商单回复 Agent 草拟跟进话术' },
        { id: 'n-confirm', name: '人工确认', type: 'agent', agent_id: 'AG-002', status: 'success', description: '商务人员确认或调整' },
        { id: 'n-send', name: '发送邮件', type: 'tool', tool_keys: ['send_email'], status: 'success', description: '发送给客户' },
        { id: 'n-end', name: '结束', type: 'end', status: 'success' },
      ],
      edges: [
        { from: 'n-start', to: 'n-match' },
        { from: 'n-match', to: 'n-reply' },
        { from: 'n-reply', to: 'n-confirm' },
        { from: 'n-confirm', to: 'n-send' },
        { from: 'n-send', to: 'n-end' },
      ],
      agent_bindings: { 'n-reply': 'AG-002', 'n-confirm': 'AG-002' },
      tool_chain: { 'n-match': ['lead_search'], 'n-send': ['send_email'] },
      history: [
        { id: 'R-241014-03', started_at: minsAgo(180), ended_at: minsAgo(178), status: 'success', output_summary: '为「智慧城市项目」生成跟进邮件，客户已回复' },
        { id: 'R-241015-04', started_at: minsAgo(30), status: 'running', output_summary: '正在为「数字政务平台」生成方案草稿' },
      ],
      updated_at: minsAgo(1),
    },
    {
      id: 'WF-AUTO-REPLY',
      name: '自动分类与去重',
      description: '监听新增反馈 → AI 分类 → 去重组群 → 按优先级派单 → 生成待办。',
      enabled: true,
      trigger: '事件：新反馈提交时实时触发',
      nodes: [
        { id: 'n-start', name: '开始', type: 'start', status: 'success' },
        { id: 'n-ingest', name: '接收反馈', type: 'tool', tool_keys: ['feedback_search'], status: 'success', description: '读取新增反馈内容' },
        { id: 'n-classify', name: 'AI 分类', type: 'agent', agent_id: 'AG-005', status: 'success', description: '自动分类 Agent 打标签' },
        { id: 'n-dedup', name: '去重组群', type: 'agent', agent_id: 'AG-005', status: 'success', description: '相似反馈归并，避免重复处理' },
        { id: 'n-priority', name: '优先级评估', type: 'decision', status: 'success', description: '紧急/高/中/低' },
        { id: 'n-todo', name: '生成待办', type: 'tool', tool_keys: ['create_todo'], status: 'success', description: '创建工单并指派' },
        { id: 'n-end', name: '结束', type: 'end', status: 'success' },
      ],
      edges: [
        { from: 'n-start', to: 'n-ingest' },
        { from: 'n-ingest', to: 'n-classify' },
        { from: 'n-classify', to: 'n-dedup' },
        { from: 'n-dedup', to: 'n-priority' },
        { from: 'n-priority', to: 'n-todo', condition: '紧急/高' },
        { from: 'n-priority', to: 'n-end', condition: '中/低' },
        { from: 'n-todo', to: 'n-end' },
      ],
      agent_bindings: { 'n-classify': 'AG-005', 'n-dedup': 'AG-005' },
      tool_chain: { 'n-ingest': ['feedback_search'], 'n-todo': ['create_todo'] },
      history: [
        { id: 'R-241015-05', started_at: minsAgo(240), ended_at: minsAgo(238), status: 'success', output_summary: '处理 17 条新增反馈，归并为 9 个待办' },
        { id: 'R-241015-06', started_at: minsAgo(90), ended_at: minsAgo(88), status: 'success', output_summary: '处理 3 条紧急反馈，已创建工单' },
      ],
      updated_at: minsAgo(1),
    },
    {
      id: 'WF-SENTIMENT-ALERT',
      name: '舆情监测与应急',
      description: '舆情定时扫描 → 情感异常检测 → 阈值触发 → 生成预警 → 通知负责人。',
      enabled: true,
      trigger: '定时：每 30 分钟扫描一次舆情源；事件：情感值骤降 > 20% 时立即触发',
      nodes: [
        { id: 'n-start', name: '开始', type: 'start', status: 'success' },
        { id: 'n-crawl', name: '舆情扫描', type: 'tool', tool_keys: ['news_search'], status: 'success', description: '爬取社交媒体与新闻' },
        { id: 'n-sentiment', name: '情感分析', type: 'agent', agent_id: 'AG-003', status: 'success', description: '舆情聚类 Agent 分析情感走势' },
        { id: 'n-threshold', name: '阈值判断', type: 'decision', status: 'success', description: '情感值降幅 > 20%' },
        { id: 'n-alert', name: '生成预警', type: 'agent', agent_id: 'AG-003', status: 'success', description: '草拟预警报告' },
        { id: 'n-notify', name: '通知推送', type: 'tool', tool_keys: ['send_email', 'send_sms'], status: 'success', description: '推送给舆情值班组' },
        { id: 'n-end', name: '结束', type: 'end', status: 'success' },
      ],
      edges: [
        { from: 'n-start', to: 'n-crawl' },
        { from: 'n-crawl', to: 'n-sentiment' },
        { from: 'n-sentiment', to: 'n-threshold' },
        { from: 'n-threshold', to: 'n-alert', condition: '触发阈值' },
        { from: 'n-threshold', to: 'n-end', condition: '正常' },
        { from: 'n-alert', to: 'n-notify' },
        { from: 'n-notify', to: 'n-end' },
      ],
      agent_bindings: { 'n-sentiment': 'AG-003', 'n-alert': 'AG-003' },
      tool_chain: { 'n-crawl': ['news_search'], 'n-notify': ['send_email', 'send_sms'] },
      history: [
        { id: 'R-241015-07', started_at: minsAgo(300), ended_at: minsAgo(298), status: 'success', output_summary: '情感值正常，无异常舆情' },
        { id: 'R-241015-08', started_at: minsAgo(45), ended_at: minsAgo(43), status: 'failed', output_summary: '情感分析节点超时', error_message: '模型推理节点 model-infer-01 负载过高，推理超时' },
      ],
      updated_at: minsAgo(1),
    },
    {
      id: 'WF-NEIGHBOR-REQ',
      name: '多源诉求聚合解决',
      description: '汇聚热线/微信/网格化上报 → 去重聚类 → 智能分拨 → 跟踪闭环。',
      enabled: false,
      trigger: '事件：任意渠道收到诉求时实时触发',
      nodes: [
        { id: 'n-start', name: '开始', type: 'start', status: 'idle' },
        { id: 'n-collect', name: '多源汇聚', type: 'tool', tool_keys: ['feedback_search'], status: 'idle', description: '聚合热线、微信、网格化数据' },
        { id: 'n-dedup', name: '去重聚类', type: 'agent', agent_id: 'AG-004', status: 'idle', description: '诉求处置 Agent 识别重复诉求' },
        { id: 'n-assign', name: '智能分拨', type: 'decision', status: 'idle', description: '按属地/类型分派' },
        { id: 'n-track', name: '跟踪闭环', type: 'agent', agent_id: 'AG-004', status: 'idle', description: '跟踪处理进度直至办结' },
        { id: 'n-archive', name: '归档', type: 'tool', tool_keys: ['create_todo'], status: 'idle', description: '标记已办结' },
        { id: 'n-end', name: '结束', type: 'end', status: 'idle' },
      ],
      edges: [
        { from: 'n-start', to: 'n-collect' },
        { from: 'n-collect', to: 'n-dedup' },
        { from: 'n-dedup', to: 'n-assign' },
        { from: 'n-assign', to: 'n-track', condition: '已分拨' },
        { from: 'n-assign', to: 'n-archive', condition: '重复/无效' },
        { from: 'n-track', to: 'n-archive' },
        { from: 'n-archive', to: 'n-end' },
      ],
      agent_bindings: { 'n-dedup': 'AG-004', 'n-track': 'AG-004' },
      tool_chain: { 'n-collect': ['feedback_search'], 'n-archive': ['create_todo'] },
      history: [],
      updated_at: minsAgo(1),
    },
  ]
}
