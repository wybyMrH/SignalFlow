import type { InterviewRecord, InterviewSummary, ResourceHealth } from '@/types'

/**
 * 客户访谈与管理中心（mock）：
 * 模拟访谈记录管理 + AI 提炼客户痛点与需求 + 与商务洞察联动。
 * 后续「资源管理」页复用 getResourceHealth 作为健康概况数据源。
 */
const daysAgo = (n: number) => new Date(Date.now() - n * 86400_000).toISOString()

/** 客户访谈记录列表（覆盖 scheduled / recorded / extracted / linked 状态） */
export function getInterviewRecords(): InterviewRecord[] {
  return [
    {
      id: 'IV-001',
      company_name: '云帆数字设计',
      company_type: '私企',
      industry: '企业服务',
      contact_name: '林倩',
      contact_role: 'IT 负责人',
      interview_date: daysAgo(1),
      duration_min: 38,
      source: '视频会议',
      status: 'linked',
      summary: '设计团队 400+ 成员，期望按部门批量开通账号，同时希望管理员能看到成员活跃度以决定续费规模。',
      key_points: [
        '每季度新增约 40 名外包设计师，逐个建号耗时约 3 人天',
        '需要角色分组权限模板，希望按项目隔离数据',
        '对续费定价敏感，正在对比竞品',
      ],
      extraction: {
        pain_points: ['批量建号运维成本高', '希望角色级权限模板'],
        needs: ['批量账号导入', '角色分组授权', '成员活跃度报表'],
        cooperation_intent: 'high',
        matched_needs: ['批量账号与角色管理'],
        lead_candidate: true,
        lead_reason: '明确多次提及批量账号与角色分组能力，与企业版合作意向高',
        extracted_at: daysAgo(0.8),
      },
      linked_feedback_ids: ['F1101'],
      linked_lead_id: 'BL-006',
      recorder: '王雨桐',
    },
    {
      id: 'IV-002',
      company_name: '中科软联',
      company_type: '私企',
      industry: '软件外包',
      contact_name: '陈奕帆',
      contact_role: '交付总监',
      interview_date: daysAgo(2),
      duration_min: 45,
      source: '现场走访',
      status: 'extracted',
      summary: '作为外包承接方，客户要求把反馈系统部署在自有机房，敏感数据不出域，同时希望提供私有化运维文档。',
      key_points: [
        '甲方合同要求数据不出域，需本地化交付',
        '希望提供离线模型更新与运维手册',
        '正在评估 3 家供应商，预计 Q4 决策',
      ],
      extraction: {
        pain_points: ['数据出域合规风险', '私有化运维人力不足'],
        needs: ['本地化部署', '离线模型更新', '运维文档与培训'],
        cooperation_intent: 'high',
        matched_needs: ['私有化与数据不出域部署'],
        lead_candidate: true,
        lead_reason: '合同明确私有化部署诉求且有采购周期，形成高意向线索',
        extracted_at: daysAgo(1.8),
      },
      linked_feedback_ids: ['F1102'],
      recorder: '王雨桐',
    },
    {
      id: 'IV-003',
      company_name: '华东能源集团',
      company_type: '国企',
      industry: '能源化工',
      contact_name: '赵铭',
      contact_role: '信息化处长',
      interview_date: daysAgo(4),
      duration_min: 52,
      source: '视频会议',
      status: 'linked',
      summary: '集团要求与内部 OA、统一认证对接，账号体系对齐集团标准，同时反馈数据要纳入集团审计平台。',
      key_points: [
        '统一认证对接是硬性准入条件',
        '需要审计日志同步到集团平台',
        '集团信息化建设有专项资金',
      ],
      extraction: {
        pain_points: ['账号体系与集团标准不一致'],
        needs: ['SSO 集成', '审计日志对接', '集团级报表'],
        cooperation_intent: 'high',
        matched_needs: ['统一认证与集团账号对接', '审计日志与合规报告'],
        lead_candidate: true,
        lead_reason: '集团专项预算明确，SSO 与审计为刚性需求',
        extracted_at: daysAgo(3.5),
      },
      linked_feedback_ids: ['F1103'],
      linked_lead_id: 'BL-007',
      recorder: '张弛',
    },
    {
      id: 'IV-004',
      company_name: '擎天数据科技',
      company_type: '私企',
      industry: '数据服务',
      contact_name: '沈一鸣',
      contact_role: '产品经理',
      interview_date: daysAgo(3),
      duration_min: 30,
      source: '电话',
      status: 'recorded',
      summary: '想基于反馈数据能力做二次开发，把分析结果嵌入自有 BI 看板，尚未确认具体合作模式。',
      key_points: [
        '倾向 API 对接方式，需评估数据开放范围',
        '预算有限，希望先做 POC 验证',
      ],
      linked_feedback_ids: [],
      recorder: '张弛',
    },
    {
      id: 'IV-005',
      company_name: '联达精密制造',
      company_type: '外企',
      industry: '智能制造',
      contact_name: 'Marco 李',
      contact_role: '信息安全经理',
      interview_date: daysAgo(5),
      duration_min: 41,
      source: '视频会议',
      status: 'scheduled',
      summary: '外资合规要求高，正在调研审计日志与合规报告能力，原定今天访谈已改期到下周二。',
      key_points: [
        '关注 GDPR 数据合规',
        '需要操作留痕与导出报告',
      ],
      linked_feedback_ids: [],
      recorder: '王雨桐',
    },
    {
      id: 'IV-006',
      company_name: '岭南智慧政务研究院',
      company_type: '事业单位',
      industry: '政务服务',
      contact_name: '何靖',
      contact_role: '业务主任',
      interview_date: daysAgo(6),
      duration_min: 47,
      source: '展会',
      status: 'recorded',
      summary: '在数字政府展会上交流，关注舆情监测与群众诉求分级督办，希望结合现有平台做试点。',
      key_points: [
        '关注诉求自动分级与督办闭环',
        '希望演示舆情预警与处置联动',
      ],
      linked_feedback_ids: [],
      recorder: '赵铭',
    },
  ]
}

/** 访谈统计总览 */
export function getInterviewSummary(): InterviewSummary {
  const records = getInterviewRecords()
  const extracted = records.filter((r) => r.status === 'extracted' || r.status === 'linked')
  return {
    total: records.length,
    scheduled: records.filter((r) => r.status === 'scheduled').length,
    recorded: records.filter((r) => r.status === 'recorded').length,
    extracted: extracted.length,
    pending_extraction: records.filter((r) => r.status === 'recorded').length,
    lead_candidates: extracted.filter((r) => r.extraction?.lead_candidate).length,
    generated_leads: records.filter((r) => r.linked_lead_id).length,
    matched_needs_count: new Set(extracted.flatMap((r) => r.extraction?.matched_needs ?? [])).size,
    total_duration_min: records.reduce((sum, r) => sum + r.duration_min, 0),
  }
}

/** 资源健康概况（总览驾驶舱展示，资源管理页复用） */
export function getResourceHealth(): ResourceHealth {
  return {
    ok: true,
    server_count: 4,
    server_healthy: 4,
    db_status: 'healthy',
    db_connections: 23,
    api_healthy: 12,
    api_total: 14,
    error_rate: 0.4,
    alert_count: 1,
    updated_at: new Date().toISOString(),
  }
}