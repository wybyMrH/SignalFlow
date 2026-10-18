/**
 * 治理案例库（洞察主题 -> 参考案例）。
 *
 * 用于「洞察与决策」右侧区域：为每个主题提供 1-3 条可借鉴的治理行动与成效，
 * 帮助把洞察转化为决策；同时作为「生成治理任务」闭环的背景素材。
 * 案例为产品演示用模拟内容，按主题 id 关联，不依赖后端。
 */

export type CaseStatus = 'done' | 'doing' | 'planned'

export interface GovernanceCase {
  id: string
  topic_id: string
  title: string
  org: string
  action: string
  effect: string
  status: CaseStatus
}

export const topicCases: GovernanceCase[] = [
  // t1 办事材料重复提交
  {
    id: 'C101',
    topic_id: 't1',
    title: '高频事项材料复用上线',
    org: '数据治理组',
    action: '建设电子材料共享库，对 13 个高频事项实现线下窗口免提交、线上自动带出。',
    effect: '材料提交次数下降约 40%，单次办事时长缩短 15 分钟。',
    status: 'done',
  },
  {
    id: 'C102',
    topic_id: 't1',
    title: '线上线下清单口径统一',
    org: '政务内容组',
    action: '逐项比对线上线下办事指南，纠正 26 处清单不一致，同步更新公示。',
    effect: '因清单不一致产生的退件投诉下降 30%。',
    status: 'doing',
  },
  {
    id: 'C103',
    topic_id: 't1',
    title: '材料预审与容缺受理',
    org: '运营管理组',
    action: '对非关键材料推行容缺受理，材料缺失时先办后补。',
    effect: '预计减少二次跑动 25%，进入试点排期。',
    status: 'planned',
  },

  // t2 大厅等候时间过长
  {
    id: 'C201',
    topic_id: 't2',
    title: '预约量驱动的动态开窗',
    org: '运营管理组',
    action: '按预约与实时人流预测，高峰期自动增开 3-5 个综合窗口。',
    effect: '高峰平均等候从 62 分钟降至 28 分钟。',
    status: 'doing',
  },
  {
    id: 'C202',
    topic_id: 't2',
    title: '等候时长实时提示屏',
    org: '平台研发组',
    action: '叫号系统联动大屏，显示各窗口预计等候时间与建议分流窗口。',
    effect: '现场秩序类投诉下降 22%。',
    status: 'planned',
  },

  // t3 线上预约系统不稳定
  {
    id: 'C301',
    topic_id: 't3',
    title: '预约数据每日快照与容灾演练',
    org: '平台研发组',
    action: '每日凌晨全量快照，故障时 15 分钟内可恢复到最近一次快照。',
    effect: '系统恢复时间从小时级缩短到分钟级。',
    status: 'doing',
  },
  {
    id: 'C302',
    topic_id: 't3',
    title: '短信提醒补偿机制',
    org: '平台研发组',
    action: '对因系统回滚丢失的预约记录自动补发短信并人工复核补录。',
    effect: '预约记录类投诉减少 35%。',
    status: 'planned',
  },

  // t4 政策咨询响应偏慢
  {
    id: 'C401',
    topic_id: 't4',
    title: '政策问答知识库上线',
    org: '政务内容组',
    action: '沉淀 300+ 标准问答，热线与在线咨询统一引用知识库作答。',
    effect: '常见政策问题 1 个工作日内必回复，答复一致率提升到 95%。',
    status: 'done',
  },
  {
    id: 'C402',
    topic_id: 't4',
    title: '答复口径统一 SOP',
    org: '运营管理组',
    action: '建立转办与超时提醒机制，超时自动升级到值班负责人。',
    effect: '5 个工作日未答复工单清零。',
    status: 'doing',
  },

  // t5 窗口服务体验不一
  {
    id: 'C501',
    topic_id: 't5',
    title: 'AB 岗交接与话术标准化',
    org: '运营管理组',
    action: '推行晨会交接清单 + 统一答复话术模板，覆盖全部窗口 60+ 名同事。',
    effect: '口径不一致类投诉下降 18%。',
    status: 'doing',
  },
  {
    id: 'C502',
    topic_id: 't5',
    title: '满意度即时评价闭环',
    org: '政务内容组',
    action: '窗口办结后一屏双显邀请评价，差评 2 小时内回访整改。',
    effect: '差评响应率 100%，回访满意度 92%。',
    status: 'planned',
  },

  // t6 老年与无障碍服务不足
  {
    id: 'C601',
    topic_id: 't6',
    title: '长者号与语音叫号适配',
    org: '运营管理组',
    action: '开设长者优先窗口，叫号屏增加语音播报与大字号显示。',
    effect: '老年群体平均等候时间缩短一半。',
    status: 'doing',
  },
  {
    id: 'C602',
    topic_id: 't6',
    title: '无障碍通道与一对一帮办',
    org: '运营管理组',
    action: '完善无障碍坡道、轮椅借用，并为特殊群体提供一对一帮办。',
    effect: '无障碍服务投诉归零，获市民表扬 12 次。',
    status: 'planned',
  },

  // t7 停车与指引不清晰
  {
    id: 'C701',
    topic_id: 't7',
    title: '入口指引与余位电子屏',
    org: '运营管理组',
    action: '主要路口增设指引牌，停车场入口安装余位电子屏。',
    effect: '首次到访找路时间平均减少 5 分钟。',
    status: 'planned',
  },
  {
    id: 'C702',
    topic_id: 't7',
    title: '导航直达停车场',
    org: '平台研发组',
    action: '在政务 App 增加停车场导航与预约车位数查询。',
    effect: '预计缓解高峰期入场排队，进入需求排期。',
    status: 'planned',
  },

  // t8 移动端 APP 操作不便
  {
    id: 'C801',
    topic_id: 't8',
    title: '核心流程三步可达改造',
    org: '平台研发组',
    action: '重构首页与办事入口，高频事项 3 步内到达，简化表单字段。',
    effect: '办理转化率提升约 15%，App 评分回升。',
    status: 'doing',
  },
  {
    id: 'C802',
    topic_id: 't8',
    title: '人脸识别降级与稳定性监控',
    org: '平台研发组',
    action: '人脸识别失败自动降级为短信验证，接入崩溃监控与热修复通道。',
    effect: '闪退率下降 60%，人脸失败阻断率下降 45%。',
    status: 'planned',
  },
]

/** 按主题取案例（无案例时返回空数组）。 */
export function getTopicCases(topicId: string): GovernanceCase[] {
  return topicCases.filter((c) => c.topic_id === topicId)
}