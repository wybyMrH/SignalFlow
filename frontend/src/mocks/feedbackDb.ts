/**
 * Mock 反馈数据源（政务服务中心演示场景）。
 *
 * 设计约束（docs/frontend-development-plan.md §4.2）：
 * - 数据必须通过 FeedbackView 类型校验，与后端契约保持对齐；
 * - 列表/详情/创建/状态流转均在此"微型后端"内模拟，页面与 store 不感知数据来源；
 * - 聚合指标（总览趋势/渠道分布）由 dashboard.ts 基于本库实时计算，保证口径自洽。
 */

import type { FeedbackCreate, FeedbackListQuery, FeedbackStats, FeedbackView, Paged } from '@/types'

/** 演示租户 */
export const DEMO_TENANT = 'demo-gov'

/**
 * 基于当前时间生成「最近 N 天」内的演示时间戳（UTC 日期键与 dashboard 聚合口径一致）。
 * hour 取值 0-10 对应本地（UTC+8）8-18 点工作时段，保证当天数据落在对应 UTC 日期。
 */
function mockUtc(daysAgo: number, hour: number, minute: number): string {
  const d = new Date()
  d.setUTCDate(d.getUTCDate() - daysAgo)
  d.setUTCHours(hour, minute, 0, 0)
  return d.toISOString()
}

/** source_ref 日期前缀（如 HM-1018-001），与创建时间保持同一天，避免订单号与日期脱节。 */
function mockRefDay(daysAgo: number): string {
  const d = new Date()
  d.setUTCDate(d.getUTCDate() - daysAgo)
  const mm = String(d.getUTCMonth() + 1).padStart(2, '0')
  const dd = String(d.getUTCDate()).padStart(2, '0')
  return `${mm}${dd}`
}

/**
 * 全量反馈明细（64 条演示样本）。
 * 时间动态落在最近三天（今天 / 昨天 / 前天），各渠道、状态、主题、情感均覆盖：
 * - 状态：new / analyzing / ai_reviewing / ai_replied / resolved / replied / closed 全量覆盖；
 * - 渠道：hotline / portal / ticket / interview / review / sales 全量覆盖；
 * - 每条均含 sentiment、priority、topic_id、topic_title（new 状态 reviewer 为 null）；
 * - 内容按真实政务场景编写：排队取号、材料重复提交、预约系统、政策咨询、无障碍、停车指引、APP 操作等。
 */
export const feedbackDb: FeedbackView[] = [
  // ── 前天（offset=2）──
  { id: 'F1001', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(2)}-001`, content: '上午九点在一楼大厅排队取号，等了四十分钟才轮到，叫号屏还跳过了好几个号，老人站着干着急。', author: '王梅', status: 'closed', sentiment: 'negative', priority: 5, topic_id: 't2', topic_title: '大厅等候时间过长', reviewer: '张莉', created_at: mockUtc(2, 1, 12), updated_at: mockUtc(1, 5, 40) },
  { id: 'F1002', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '从东门进来绕了两圈才找到停车场入口，路上没有任何指示牌，办完事出来又找不到车了。', author: '李强', status: 'resolved', sentiment: 'neutral', priority: 2, topic_id: 't7', topic_title: '停车与指引不清晰', reviewer: '陈曦', created_at: mockUtc(2, 3, 5), updated_at: mockUtc(2, 8, 20) },
  { id: 'F1003', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(2)}-012`, content: '办房屋租赁备案要求提交身份证、房产证、合同原件和复印件，材料上周刚交过一模一样的，这次又要，建议打通材料复用。', author: '刘芳', status: 'analyzing', sentiment: 'negative', priority: 4, topic_id: 't1', topic_title: '办事材料重复提交', reviewer: '赵磊', created_at: mockUtc(2, 6, 22), updated_at: mockUtc(2, 8, 10) },
  { id: 'F1004', tenant_id: DEMO_TENANT, source: 'interview', source_ref: null, content: '访谈中多位老人反映：自助取号机字太小、不会操作，也没有志愿者协助，希望能保留人工通道。', author: '周阿姨', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't6', topic_title: '老年与无障碍服务不足', reviewer: null, created_at: mockUtc(2, 8, 45), updated_at: mockUtc(2, 8, 45) },
  { id: 'F1005', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(2)}-009`, content: '预约系统昨天下单成功，今早到现场却说没查到记录，值班人员电话也打不通，白跑一趟。', author: '吴晓东', status: 'resolved', sentiment: 'negative', priority: 4, topic_id: 't3', topic_title: '线上预约系统不稳定', reviewer: '孙浩', created_at: mockUtc(2, 0, 30), updated_at: mockUtc(1, 3, 12) },
  { id: 'F1006', tenant_id: DEMO_TENANT, source: 'review', source_ref: `PJ-${mockRefDay(2)}-021`, content: '综合窗口办社保转移中午排了一个多小时，柜台只开两个，其他窗口空着没人。', author: '郑爽', status: 'analyzing', sentiment: 'negative', priority: 4, topic_id: 't2', topic_title: '大厅等候时间过长', reviewer: '张莉', created_at: mockUtc(2, 5, 20), updated_at: mockUtc(2, 7, 0) },
  { id: 'F1007', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '网站上留了咨询企业年金的问题，三天没人回，400 电话也说不清楚，只能再跑一趟。', author: '钱进', status: 'replied', sentiment: 'neutral', priority: 3, topic_id: 't4', topic_title: '政策咨询响应偏慢', reviewer: '何静', created_at: mockUtc(2, 7, 1), updated_at: mockUtc(1, 8, 30) },
  { id: 'F1008', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(2)}-018`, content: '我的客户 APP 报错提示 token 过期，重装了三次还是闪退，iPhone 15 最新系统。', author: '冯嘉', status: 'closed', sentiment: 'negative', priority: 4, topic_id: 't8', topic_title: '移动端 APP 操作不便', reviewer: '孙浩', created_at: mockUtc(2, 9, 48), updated_at: mockUtc(1, 2, 22) },
  { id: 'F1009', tenant_id: DEMO_TENANT, source: 'review', source_ref: `PJ-${mockRefDay(2)}-005`, content: '今天窗口的小伙子态度很好，把医保报销需要的材料一条条列给我，办得很顺利，点赞。', author: '孙秀英', status: 'resolved', sentiment: 'positive', priority: 1, topic_id: 't5', topic_title: '窗口服务体验不一', reviewer: null, created_at: mockUtc(2, 2, 15), updated_at: mockUtc(2, 2, 15) },
  { id: 'F1010', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(2)}-013`, content: '办营业执照变更，窗口说缺场地证明，可我在网上传过了，线下打印件又不认，重复交材料。', author: '许峰', status: 'analyzing', sentiment: 'negative', priority: 4, topic_id: 't1', topic_title: '办事材料重复提交', reviewer: '赵磊', created_at: mockUtc(2, 3, 35), updated_at: mockUtc(2, 6, 40) },
  { id: 'F1011', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '线上预约提交后页面一直转圈，刷新后发现约的时段被改了，差点错过办理日期。', author: '何俊', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't3', topic_title: '线上预约系统不稳定', reviewer: null, created_at: mockUtc(2, 6, 8), updated_at: mockUtc(2, 6, 8) },
  { id: 'F1012', tenant_id: DEMO_TENANT, source: 'sales', source_ref: null, content: '客户现场走访反馈：停车引导确实混乱，商务洽谈客户第一次来基本都要打电话问路。', author: '罗成', status: 'closed', sentiment: 'neutral', priority: 2, topic_id: 't7', topic_title: '停车与指引不清晰', reviewer: '陈曦', created_at: mockUtc(2, 8, 52), updated_at: mockUtc(1, 4, 1) },
  { id: 'F1014', tenant_id: DEMO_TENANT, source: 'interview', source_ref: null, content: '访谈记录：老年人大厅办理业务平均比年轻人多花 20 分钟，主要卡在填表和手机操作环节。', author: '周阿姨', status: 'resolved', sentiment: 'neutral', priority: 3, topic_id: 't6', topic_title: '老年与无障碍服务不足', reviewer: '何静', created_at: mockUtc(2, 5, 40), updated_at: mockUtc(1, 2, 15) },
  { id: 'F1015', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(2)}-022`, content: '咨询生育津贴申领条件，热线转了三个人，等了两天没人回电话，政策解读口径不一。', author: '孟凡', status: 'new', sentiment: 'negative', priority: 3, topic_id: 't4', topic_title: '政策咨询响应偏慢', reviewer: null, created_at: mockUtc(2, 7, 19), updated_at: mockUtc(2, 7, 19) },
  { id: 'F1016', tenant_id: DEMO_TENANT, source: 'review', source_ref: `PJ-${mockRefDay(2)}-014`, content: '新版 APP 预约入口藏在二级菜单里，字号小，操作流程比旧版多了三步。', author: '秦朗', status: 'analyzing', sentiment: 'negative', priority: 3, topic_id: 't8', topic_title: '移动端 APP 操作不便', reviewer: '孙浩', created_at: mockUtc(2, 9, 3), updated_at: mockUtc(1, 2, 20) },
  { id: 'F1017', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '同一套材料在三个窗口各交一遍，前台说系统没打通，建议部门间共享材料库。', author: '宋佳', status: 'resolved', sentiment: 'negative', priority: 4, topic_id: 't1', topic_title: '办事材料重复提交', reviewer: '赵磊', created_at: mockUtc(2, 3, 41), updated_at: mockUtc(1, 8, 5) },
  { id: 'F1018', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(2)}-016`, content: '窗口工作人员解答耐心，但不同窗口对同一问题说法不一样，建议统一培训口径。', author: '唐丽', status: 'replied', sentiment: 'neutral', priority: 2, topic_id: 't5', topic_title: '窗口服务体验不一', reviewer: '陈曦', created_at: mockUtc(2, 5, 55), updated_at: mockUtc(1, 4, 33) },
  { id: 'F1019', tenant_id: DEMO_TENANT, source: 'review', source_ref: `PJ-${mockRefDay(2)}-009`, content: '预约页选择时段后提示库存不足，反复重试三次才成功，体验很差。', author: '魏然', status: 'new', sentiment: 'negative', priority: 3, topic_id: 't3', topic_title: '线上预约系统不稳定', reviewer: null, created_at: mockUtc(2, 7, 37), updated_at: mockUtc(2, 7, 37) },
  { id: 'F1020', tenant_id: DEMO_TENANT, source: 'sales', source_ref: null, content: '重点企业走访：企业对绿色通道服务满意，希望把定制化办理推广到更多事项。', author: '罗成', status: 'resolved', sentiment: 'positive', priority: 1, topic_id: 't2', topic_title: '大厅等候时间过长', reviewer: null, created_at: mockUtc(2, 9, 28), updated_at: mockUtc(2, 9, 28) },
  { id: 'F1021', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(2)}-011`, content: '东门停车场夜间照明不足，地面车位线磨损看不清，容易刮蹭。', author: '段鹏', status: 'closed', sentiment: 'neutral', priority: 2, topic_id: 't7', topic_title: '停车与指引不清晰', reviewer: '陈曦', created_at: mockUtc(2, 8, 50), updated_at: mockUtc(1, 2, 0) },
  { id: 'F1022', tenant_id: DEMO_TENANT, source: 'review', source_ref: `PJ-${mockRefDay(2)}-017`, content: '公积金政策页写的和窗口执行的不一致，被工作人员要求按新口径补材料。', author: '林芳', status: 'analyzing', sentiment: 'negative', priority: 3, topic_id: 't4', topic_title: '政策咨询响应偏慢', reviewer: '何静', created_at: mockUtc(2, 3, 44), updated_at: mockUtc(1, 2, 50) },
  // ── 昨天（offset=1，周六）──
  { id: 'F1013', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(1)}-007`, content: '社保窗口周末排长队，取号系统显示前面还有 68 人，实际等候接近两小时。', author: '黄敏', status: 'closed', sentiment: 'negative', priority: 5, topic_id: 't2', topic_title: '大厅等候时间过长', reviewer: '张莉', created_at: mockUtc(1, 6, 26), updated_at: mockUtc(1, 8, 32) },
  { id: 'F1023', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '残疾人通道入口常年锁着，轮椅用户只能绕到正门，建议在门户上标注无障碍路线。', author: '龚平', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't6', topic_title: '老年与无障碍服务不足', reviewer: null, created_at: mockUtc(1, 5, 16), updated_at: mockUtc(1, 5, 16) },
  { id: 'F1024', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(1)}-027`, content: '灵活就业参保材料清单线上线下不一致，线下要求的多一份委托书，来回折腾。', author: '曹阳', status: 'analyzing', sentiment: 'negative', priority: 4, topic_id: 't1', topic_title: '办事材料重复提交', reviewer: '赵磊', created_at: mockUtc(1, 8, 2), updated_at: mockUtc(1, 8, 30) },
  { id: 'F1025', tenant_id: DEMO_TENANT, source: 'interview', source_ref: null, content: '回访：三成受访者对大厅等待时长不满，高峰时段取号后无排队进度提醒。', author: '访谈组', status: 'new', sentiment: 'negative', priority: 5, topic_id: 't2', topic_title: '大厅等候时间过长', reviewer: null, created_at: mockUtc(1, 1, 30), updated_at: mockUtc(1, 1, 30) },
  { id: 'F1026', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: 'APP 人脸识别在强光下无法通过，每次办理都要试四五次，建议增加手动验证。', author: '叶青', status: 'resolved', sentiment: 'negative', priority: 3, topic_id: 't8', topic_title: '移动端 APP 操作不便', reviewer: '孙浩', created_at: mockUtc(1, 3, 22), updated_at: mockUtc(0, 6, 44) },
  { id: 'F1027', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(1)}-003`, content: '综合窗口叫号顺序偶尔和取号时间不一致，短号后到却先办，引发排队不满。', author: '韩雪', status: 'replied', sentiment: 'neutral', priority: 3, topic_id: 't5', topic_title: '窗口服务体验不一', reviewer: '陈曦', created_at: mockUtc(1, 6, 9), updated_at: mockUtc(0, 1, 25) },
  { id: 'F1028', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(1)}-019`, content: '预约后系统未发短信提醒，到大厅才发现预约被取消，说是系统默认超时释放。', author: '顾全', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't3', topic_title: '线上预约系统不稳定', reviewer: null, created_at: mockUtc(1, 7, 58), updated_at: mockUtc(1, 7, 58) },
  { id: 'F1029', tenant_id: DEMO_TENANT, source: 'review', source_ref: `PJ-${mockRefDay(1)}-006`, content: '办理不动产登记，材料清单上十项材料有六项是重复提交过，历史数据应该能复用。', author: '邵峰', status: 'analyzing', sentiment: 'negative', priority: 4, topic_id: 't1', topic_title: '办事材料重复提交', reviewer: '赵磊', created_at: mockUtc(1, 2, 5), updated_at: mockUtc(1, 4, 30) },
  { id: 'F1030', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(1)}-015`, content: '咨询异地就医备案，提交后 5 个工作日才回复，期间病人都已经出院了。', author: '于华', status: 'resolved', sentiment: 'neutral', priority: 3, topic_id: 't4', topic_title: '政策咨询响应偏慢', reviewer: '何静', created_at: mockUtc(1, 5, 28), updated_at: mockUtc(0, 2, 12) },
  { id: 'F1031', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '高峰期取号后显示等待 120 分钟，实际等了 150 分钟，等候屏更新时间不实时。', author: '章悦', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't2', topic_title: '大厅等候时间过长', reviewer: null, created_at: mockUtc(1, 7, 35), updated_at: mockUtc(1, 7, 35) },
  { id: 'F1032', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(1)}-024`, content: '帮八十岁母亲办高龄补贴，窗口要求用手机操作，老人没有智能手机，需要代办服务。', author: '薛燕', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't6', topic_title: '老年与无障碍服务不足', reviewer: null, created_at: mockUtc(1, 9, 20), updated_at: mockUtc(1, 9, 20) },
  { id: 'F1033', tenant_id: DEMO_TENANT, source: 'interview', source_ref: null, content: '用户访谈：年轻人普遍能接受线上办理，但觉得 APP 步骤繁琐，常用功能要翻三层。', author: '访谈组', status: 'analyzing', sentiment: 'negative', priority: 3, topic_id: 't8', topic_title: '移动端 APP 操作不便', reviewer: '孙浩', created_at: mockUtc(1, 1, 48), updated_at: mockUtc(1, 3, 15) },
  { id: 'F1034', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '预约改签功能不可用，只能取消重约，高峰时段基本抢不到号。', author: '钟磊', status: 'closed', sentiment: 'neutral', priority: 3, topic_id: 't3', topic_title: '线上预约系统不稳定', reviewer: '孙浩', created_at: mockUtc(1, 3, 14), updated_at: mockUtc(1, 6, 0) },
  { id: 'F1035', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(1)}-020`, content: '今天遇到的热线客服非常专业，主动帮忙预约了复诊号，还提醒我带齐材料。', author: '程雪', status: 'resolved', sentiment: 'positive', priority: 1, topic_id: 't5', topic_title: '窗口服务体验不一', reviewer: null, created_at: mockUtc(1, 6, 2), updated_at: mockUtc(1, 6, 2) },
  { id: 'F1036', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(1)}-004`, content: '个体户年报材料与税务部门要求不一致，两部门互不认账，要求纸质件重新提交。', author: '贾宁', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't1', topic_title: '办事材料重复提交', reviewer: null, created_at: mockUtc(1, 8, 33), updated_at: mockUtc(1, 8, 33) },
  { id: 'F1037', tenant_id: DEMO_TENANT, source: 'review', source_ref: `PJ-${mockRefDay(1)}-012`, content: '周末大厅爆满，叫号系统卡顿，等了一个小时发现号被叫过没人应。', author: '戴琳', status: 'analyzing', sentiment: 'negative', priority: 5, topic_id: 't2', topic_title: '大厅等候时间过长', reviewer: '张莉', created_at: mockUtc(1, 1, 55), updated_at: mockUtc(1, 3, 5) },
  { id: 'F1038', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '北门停车场没有电子余位屏，高峰期在门口排队等位，建议接入系统实时显示。', author: '石磊', status: 'resolved', sentiment: 'neutral', priority: 2, topic_id: 't7', topic_title: '停车与指引不清晰', reviewer: '陈曦', created_at: mockUtc(1, 4, 16), updated_at: mockUtc(1, 7, 30) },
  { id: 'F1039', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(1)}-026`, content: '咨询创业补贴政策，热线只给了网址让自行查看，没有直接解答，感受敷衍。', author: '彭飞', status: 'new', sentiment: 'negative', priority: 3, topic_id: 't4', topic_title: '政策咨询响应偏慢', reviewer: null, created_at: mockUtc(1, 6, 41), updated_at: mockUtc(1, 6, 41) },
  { id: 'F1040', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(1)}-009`, content: '无障碍电梯在检修期未提前公示，轮椅用户到了现场才知道，白跑一趟。', author: '谭芳', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't6', topic_title: '老年与无障碍服务不足', reviewer: null, created_at: mockUtc(1, 8, 58), updated_at: mockUtc(1, 8, 58) },
  { id: 'F1041', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(1)}-017`, content: '预约时段被系统自动重排，致电热线确认又说以现场为准，两个口径不一致。', author: '熊伟', status: 'analyzing', sentiment: 'negative', priority: 4, topic_id: 't3', topic_title: '线上预约系统不稳定', reviewer: '孙浩', created_at: mockUtc(1, 2, 37), updated_at: mockUtc(1, 4, 45) },
  { id: 'F1042', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '材料清单页显示云盘上传成功，窗口却说系统里没有，要求重新上传打印。', author: '姜伟', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't1', topic_title: '办事材料重复提交', reviewer: null, created_at: mockUtc(1, 5, 21), updated_at: mockUtc(1, 5, 21) },
  { id: 'F1043', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(1)}-013`, content: '周六上午医保窗口只开一个，排队时长破纪录，建议按预约量动态开窗。', author: '苏娟', status: 'resolved', sentiment: 'negative', priority: 4, topic_id: 't2', topic_title: '大厅等候时间过长', reviewer: '张莉', created_at: mockUtc(1, 7, 44), updated_at: mockUtc(0, 2, 28) },
  { id: 'F1044', tenant_id: DEMO_TENANT, source: 'review', source_ref: `PJ-${mockRefDay(1)}-008`, content: '窗口回复标准不一，同一问题两个窗口给了两种答案，希望统一服务话术。', author: '黎敏', status: 'replied', sentiment: 'neutral', priority: 2, topic_id: 't5', topic_title: '窗口服务体验不一', reviewer: '陈曦', created_at: mockUtc(1, 9, 9), updated_at: mockUtc(0, 1, 20) },
  // ── 今天（offset=0）──
  { id: 'F1045', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: 'APP 版本更新后消息通知全部失效，办事进度只能到大厅看，毫无线上体验。', author: '范宁', status: 'new', sentiment: 'negative', priority: 3, topic_id: 't8', topic_title: '移动端 APP 操作不便', reviewer: null, created_at: mockUtc(0, 1, 12), updated_at: mockUtc(0, 1, 12) },
  { id: 'F1046', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(0)}-021`, content: '热线咨询公租房申请，答复说等公示，但公示时间地点都没有告知，信息不透明。', author: '任杰', status: 'new', sentiment: 'negative', priority: 3, topic_id: 't4', topic_title: '政策咨询响应偏慢', reviewer: null, created_at: mockUtc(0, 3, 26), updated_at: mockUtc(0, 3, 26) },
  { id: 'F1047', tenant_id: DEMO_TENANT, source: 'review', source_ref: `PJ-${mockRefDay(0)}-011`, content: '房产过户材料线上线下两份清单，线上说免提交的线下仍要纸质，体验割裂。', author: '尹莉', status: 'analyzing', sentiment: 'negative', priority: 4, topic_id: 't1', topic_title: '办事材料重复提交', reviewer: '赵磊', created_at: mockUtc(0, 6, 50), updated_at: mockUtc(0, 8, 35) },
  { id: 'F1048', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(0)}-016`, content: '教育部门与民政部门材料不通用，办理同一家庭业务要分别提交两套证明。', author: '洪波', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't2', topic_title: '大厅等候时间过长', reviewer: null, created_at: mockUtc(0, 9, 37), updated_at: mockUtc(0, 9, 37) },
  { id: 'F1049', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(0)}-018`, content: '线上预约系统凌晨维护后数据回滚，白天的预约记录全部丢失，窗口不认补打的凭证。', author: '牛丽', status: 'new', sentiment: 'negative', priority: 5, topic_id: 't3', topic_title: '线上预约系统不稳定', reviewer: null, created_at: mockUtc(0, 1, 8), updated_at: mockUtc(0, 1, 8) },
  { id: 'F1050', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(0)}-008`, content: '窗口 AB 岗交接不清，上午受理的单子下午另一个窗口不认，要求重新排队。', author: '夏雨', status: 'new', sentiment: 'negative', priority: 3, topic_id: 't5', topic_title: '窗口服务体验不一', reviewer: null, created_at: mockUtc(0, 3, 3), updated_at: mockUtc(0, 3, 3) },
  { id: 'F1051', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '线上提交的电子签章线下不认可，要求重新盖章签字，数字化等于没做。', author: '董洁', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't1', topic_title: '办事材料重复提交', reviewer: null, created_at: mockUtc(0, 7, 32), updated_at: mockUtc(0, 7, 32) },
  { id: 'F1052', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(0)}-023`, content: '早上八点四十到大厅，取号机前已经排了 30 人，开门前没有分流引导。', author: '白帆', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't2', topic_title: '大厅等候时间过长', reviewer: null, created_at: mockUtc(0, 0, 55), updated_at: mockUtc(0, 0, 55) },
  { id: 'F1053', tenant_id: DEMO_TENANT, source: 'review', source_ref: `PJ-${mockRefDay(0)}-007`, content: '昨日门户政策问答回复已读未回，今天热线又问了一遍，答复内容还不一致。', author: '万琳', status: 'new', sentiment: 'negative', priority: 3, topic_id: 't4', topic_title: '政策咨询响应偏慢', reviewer: null, created_at: mockUtc(0, 2, 44), updated_at: mockUtc(0, 2, 44) },
  { id: 'F1054', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '官方网站无障碍模式开关找不到，读屏软件无法朗读办理须知，视障用户无法使用。', author: '欧阳', status: 'new', sentiment: 'neutral', priority: 4, topic_id: 't6', topic_title: '老年与无障碍服务不足', reviewer: null, created_at: mockUtc(0, 6, 17), updated_at: mockUtc(0, 6, 17) },
  { id: 'F1055', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(0)}-003`, content: '今天大厅叫号系统故障，工作人员手工登记排队，秩序混乱，等了近一小时。', author: '余凯', status: 'new', sentiment: 'negative', priority: 5, topic_id: 't2', topic_title: '大厅等候时间过长', reviewer: null, created_at: mockUtc(0, 1, 20), updated_at: mockUtc(0, 1, 20) },
  { id: 'F1056', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(0)}-002`, content: 'APP 适老化模式开启后字号仍偏小，按钮点击区域不足，建议优化大字号布局。', author: '马玉', status: 'new', sentiment: 'negative', priority: 3, topic_id: 't8', topic_title: '移动端 APP 操作不便', reviewer: null, created_at: mockUtc(0, 2, 6), updated_at: mockUtc(0, 2, 6) },
  { id: 'F1057', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '线上提交电子材料成功后窗口仍要求纸质件，材料复用机制需要真正落地。', author: '龙飞', status: 'analyzing', sentiment: 'negative', priority: 4, topic_id: 't1', topic_title: '办事材料重复提交', reviewer: '赵磊', created_at: mockUtc(0, 3, 35), updated_at: mockUtc(0, 4, 0) },
  { id: 'F1058', tenant_id: DEMO_TENANT, source: 'review', source_ref: `PJ-${mockRefDay(0)}-004`, content: '改签功能依然报错，试了三次都没成功，只能到窗口重新取号办理。', author: '方婷', status: 'new', sentiment: 'negative', priority: 4, topic_id: 't3', topic_title: '线上预约系统不稳定', reviewer: null, created_at: mockUtc(0, 5, 52), updated_at: mockUtc(0, 5, 52) },
  { id: 'F1059', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(0)}-010`, content: '上午反映的叫号跳号问题，下午热线回电确认已修复，处理效率值得肯定。', author: '王梅', status: 'resolved', sentiment: 'positive', priority: 2, topic_id: 't5', topic_title: '窗口服务体验不一', reviewer: '陈曦', created_at: mockUtc(0, 1, 12), updated_at: mockUtc(0, 7, 20) },
  { id: 'F1060', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(0)}-005`, content: '咨询材料补正问题，窗口当天答复并给出清单，问题已解决。', author: '陆超', status: 'resolved', sentiment: 'positive', priority: 2, topic_id: 't1', topic_title: '办事材料重复提交', reviewer: '赵磊', created_at: mockUtc(0, 2, 40), updated_at: mockUtc(0, 6, 5) },
  // AI 状态示例数据
  { id: 'F1061', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '请问社保转移需要哪些材料？我已经在原参保地开了凭证，接下来怎么操作？', author: '郑明', status: 'ai_reviewing', sentiment: 'neutral', priority: 2, topic_id: 't4', topic_title: '政策咨询响应偏慢', reviewer: 'AI助手', created_at: mockUtc(0, 8, 0), updated_at: mockUtc(0, 8, 5) },
  { id: 'F1062', tenant_id: DEMO_TENANT, source: 'hotline', source_ref: `HM-${mockRefDay(0)}-030`, content: '大厅排队时间太长了，每次都等一个多小时，能不能多开几个窗口？', author: '林晓', status: 'ai_replied', sentiment: 'negative', priority: 4, topic_id: 't2', topic_title: '大厅等候时间过长', reviewer: 'AI自动审批', created_at: mockUtc(0, 2, 0), updated_at: mockUtc(0, 8, 10) },
  { id: 'F1063', tenant_id: DEMO_TENANT, source: 'portal', source_ref: null, content: '我想咨询一下生育津贴的申领条件，需要连续缴费多久？', author: '周婷', status: 'ai_reviewing', sentiment: 'neutral', priority: 2, topic_id: 't4', topic_title: '政策咨询响应偏慢', reviewer: 'AI助手', created_at: mockUtc(0, 7, 30), updated_at: mockUtc(0, 8, 15) },
  { id: 'F1064', tenant_id: DEMO_TENANT, source: 'ticket', source_ref: `GD-${mockRefDay(0)}-020`, content: 'APP 闪退问题怎么处理？已经更新了最新版本还是不行。', author: '吴刚', status: 'ai_replied', sentiment: 'negative', priority: 3, topic_id: 't8', topic_title: '移动端 APP 操作不便', reviewer: 'AI自动审批', created_at: mockUtc(0, 3, 20), updated_at: mockUtc(0, 8, 20) },
]

/** 文案截取：用于主题证据链摘要 */
export function excerpt(text: string, max = 56): string {
  const t = text.replace(/\s+/g, ' ').trim()
  return t.length > max ? `${t.slice(0, max)}…` : t
}

/** 模拟网络延迟，保证骨架/加载态可见 */
export function mockDelay<T>(data: T, ms = 220): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(structuredClone(data)), ms))
}

/** 根据主题生成演示性回复文案（历史回复展示用） */
export function buildMockReply(topicTitle?: string | null): string {
  const title = topicTitle ?? '相关事项'
  return `您好，您反映的“${title}”问题我们已收悉并核实处理，给您带来不便深表歉意。后续我们将持续优化服务流程与体验，感谢您的理解与支持。如有疑问可拨打服务热线详询。`
}

/**
 * 初始化历史回复：为已回复 / 已解决 / 已关闭 / AI 已回复 状态记录补充演示回复内容，
 * 保证详情抽屉“已回复内容”可展示；不覆盖手写的 reply_content。
 */
function ensureReplies() {
  const done: FeedbackView['status'][] = ['replied', 'resolved', 'closed', 'ai_replied']
  for (const f of feedbackDb) {
    if (done.includes(f.status) && !f.reply_content) {
      f.reply_content = buildMockReply(f.topic_title)
      f.replied_at = f.updated_at
    }
  }
}
ensureReplies()

/** 列表查询：过滤 + 关键字 + 分页（与后端 GET /feedbacks 契约一致） */
export function listFeedbacks(query: FeedbackListQuery = {}): Paged<FeedbackView> {
  const { source, status, keyword, topic_id, page = 1, page_size = 20 } = query
  let rows = feedbackDb
  if (source) rows = rows.filter((r) => r.source === source)
  if (status) rows = rows.filter((r) => r.status === status)
  if (topic_id) rows = rows.filter((r) => r.topic_id === topic_id)
  if (keyword) {
    const kw = keyword.trim().toLowerCase()
    rows = rows.filter(
      (r) =>
        r.content.toLowerCase().includes(kw) ||
        (r.author ?? '').toLowerCase().includes(kw) ||
        (r.topic_title ?? '').toLowerCase().includes(kw),
    )
  }
  // 排序：创建时间倒序
  rows = [...rows].sort((a, b) => b.created_at.localeCompare(a.created_at))
  const total = rows.length
  const start = (page - 1) * page_size
  return { items: rows.slice(start, start + page_size), total, page, page_size }
}

/** 详情查询 */
export function getFeedback(id: string): FeedbackView | undefined {
  return feedbackDb.find((r) => r.id === id)
}

/** 创建反馈（写入内存库头部） */
export function createFeedback(payload: FeedbackCreate): FeedbackView {
  const now = new Date().toISOString()
  const row: FeedbackView = {
    id: `F${Date.now().toString().slice(-6)}`,
    tenant_id: DEMO_TENANT,
    source: payload.source as FeedbackView['source'],
    source_ref: payload.source_ref ?? null,
    content: payload.content,
    author: payload.author ?? '匿名用户',
    status: 'new',
    sentiment: 'negative',
    topic_id: null,
    topic_title: null,
    priority: 0,
    reviewer: null,
    created_at: now,
    updated_at: now,
  }
  feedbackDb.unshift(row)
  return row
}

/** 状态流转（回写 updated_at；resolved/replied 时记录处理人；达成终态自动补回复文案） */
export function updateFeedbackStatus(
  id: string,
  status: FeedbackView['status'],
  reviewer?: string,
  replyContent?: string | null,
): FeedbackView | undefined {
  const row = feedbackDb.find((r) => r.id === id)
  if (!row) return undefined
  row.status = status
  row.updated_at = new Date().toISOString()
  if (reviewer) row.reviewer = reviewer
  const done: FeedbackView['status'][] = ['replied', 'resolved', 'closed', 'ai_replied']
  if (done.includes(status) && !row.reply_content) {
    row.reply_content = replyContent && replyContent.trim() ? replyContent.trim() : buildMockReply(row.topic_title)
    row.replied_at = row.updated_at
  }
  return row
}

/** 反馈状态统计 */
export function getFeedbackStats(): FeedbackStats {
  const s: FeedbackStats = {
    total: feedbackDb.length,
    new: 0,
    analyzing: 0,
    ai_reviewing: 0,
    ai_replied: 0,
    resolved: 0,
    replied: 0,
    closed: 0,
    high_priority: 0,
  }
  for (const f of feedbackDb) {
    if (f.status === 'new') s.new++
    else if (f.status === 'analyzing') s.analyzing++
    else if (f.status === 'ai_reviewing') s.ai_reviewing++
    else if (f.status === 'ai_replied') s.ai_replied++
    else if (f.status === 'resolved') s.resolved++
    else if (f.status === 'replied') s.replied++
    else if (f.status === 'closed') s.closed++
    if ((f.priority ?? 0) >= 4) s.high_priority++
  }
  return s
}