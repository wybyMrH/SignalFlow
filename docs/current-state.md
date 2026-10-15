# 当前状态记录

文档就绪度：已评审范围（reviewed scope：工程骨架 + 前端 mock 数据层与入口 + 业务页面切片实现与浏览器验收 + 配色与全屏排版适配 + Docker 容器化展示验证 + AI 总览面板与反馈管理 AI 化 + AI Mock 后端工作流骨架 + 反馈 UI 与统计卡修复/详情抽屉与气泡助手重构/AI 自动化流程/商务洞察/政务统计扩展 + 运营驾驶舱扩展（总览信息块/客户访谈/Agent 配置/资源管理/工作流配置）与 store 守卫集成修复）

## 评审范围

- 需求或任务：在 E:\code\interview\SignalFlow 搭建 SignalFlow 客户反馈决策工具的工程骨架（已完成）；随后按用户要求进入**前端阶段——用模拟数据把前端从入口按业务需求与功能切片推进，先以文档落盘计划/需求/技术参考，再实现可演示闭环**（本记录当前聚焦前端阶段）。
- 评审日期：2026-10-15
- 证据边界：项目目录文件结构、依赖声明、配置骨架与文档模板；前端阶段新增 `docs/frontend-development-plan.md`（计划与设计规范源）、`docs/adrs/ADR-0002-前端mock先行与轻量设计体系.md`（决策记录）；mock 数据层、API 适配层、stores、入口应用壳与路由；FS-1~FS-7 全部页面切片实现与浏览器验收证据；E-1~E-5 扩展功能（反馈统计卡/详情抽屉与气泡助手重构/AI 自动化/商务洞察/政务统计扩展）实现与浏览器验收证据；O-1~O-6 运营驾驶舱扩展（总览信息块/客户访谈/Agent 配置/资源管理/工作流配置/集成闭环联动）实现与浏览器验收证据。
- 覆盖限制：本记录覆盖骨架验证、前端规划文档、mock 入口打通与 FS-1~FS-7 页面实现、配色与全屏排版适配、Docker 容器化展示验证、AI 总览面板重构、反馈管理 AI 化（AI 回复/自动审批/气泡助手）与 AI Mock 后端工作流骨架，以及 2026-10-15 增补的反馈 UI 与统计卡修复、详情抽屉与气泡助手重构、AI 自动化流程、商务合作信息提炼与政务统计扩展，以及 2026-10-15 二次增补的运营驾驶舱扩展（总览信息块与客户访谈、Agent 配置中心、资源管理、LangGraph 工作流配置、三向闭环联动与 store 守卫修复）；尚未接入真实 LLM 与政务知识库（mock 模式下前端不依赖后端服务，AI 能力由前端 mock 工作流与后端 mock 服务层提供；真实后端 `/gov/overview` 契约亦属后续阶段）。

## 骨架阶段已关闭项（沿用首次评审）

| ID | 需求或契约点 | 文件/模块/边界 | 分类 | 观察行为 | 证据等级 | 影响 | 建议处理 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S-1 | 工程骨架位于指定目录 | `E:\code\interview\SignalFlow` | 已实现 | 目录存在，前后端与配置已生成 | 静态 | 交付前提 | 保持 | 已关闭 |
| S-2 | 区分前后端分层目录 | `backend/`、`frontend/` | 已实现 | 双目录分离，各层分包清晰 | 静态 | 交付前提 | 保持 | 已关闭 |
| S-3 | 引入 LangGraph/LiteLLM | `backend/pyproject.toml`、`backend/app/workflows/`、`backend/app/llm/` | 已实现 | 依赖声明与模块骨架就位 | 静态 | 技术选型落实 | 保持 | 已关闭 |
| S-4 | Docker 部署配置 | `backend/Dockerfile`、`frontend/Dockerfile`、`deploy/docker-compose.yml` | 已实现 | 容器编排骨架就位 | 静态 | 交付前提 | 保持 | 已关闭 |
| S-5 | GitHub Actions CI/CD | `.github/workflows/ci.yml`、`cd.yml` | 已实现 | 构建/测试/镜像工作流骨架就位 | 静态 | 交付前提 | 保持 | 已关闭 |
| S-6 | 框架与技术选型说明文档 | `docs/adrs/ADR-0001-总体技术选型.md`、README | 已实现 | 选型论证与目录说明齐备 | 静态 | 交付前提 | 保持 | 已关闭 |
| S-7 | project-compass 框架 | `AGENTS.md`、`docs/project-spec.md` 等 | 已实现 | 规则书与文档模板已安装 | 静态 | 后续开发依据 | 保持 | 已关闭 |

## 前端阶段当前项

| ID | 需求或契约点 | 文件/模块/边界 | 分类 | 观察行为 | 证据等级 | 影响 | 建议处理 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F-1 | 前端计划/需求/技术参考以 MD 落盘项目内（非 Word） | `docs/frontend-development-plan.md` | 已实现 | 全流程计划、功能切片、推进秩序、设计规范（色调/密度/布局）、技术参考齐备 | 静态（文件已写入） | 本阶段规范源 | 保持 | 已关闭 |
| F-2 | 前端 mock 先行策略与轻量设计体系决策 | `docs/adrs/ADR-0002-前端mock先行与轻量设计体系.md` | 已实现 | 决策记录按 ADR 模板完成，定义了 mock 切换与自研组件边界 | 静态 | 前端实现依据 | 保持 | 已关闭 |
| F-3 | mock 数据层与入口打通 | `frontend/src/mocks`、`frontend/src/api`、`frontend/src/stores`、`frontend/src/router`、`frontend/src/components/common`、`frontend/src/styles` | 已实现 | mock 数据源（60 条反馈 + 8 洞察主题 + 聚合指标 + 路线图 + 政务 + 设置）；API 适配层按 `VITE_USE_MOCK`（默认 mock）同契约切换；stores 状态层；FS-0 应用壳（72px 图标侧栏 + 52px 顶栏 + Mock 徽标 + 深浅主题）；6 条路由连通；设计 Token 双主题 | 动态（type-check/构建/浏览器验收通过） | 前端切片 FS-0 完成，FS-1+ 前置就绪 | 已用于 FS-1~FS-7 实现 | 已关闭 |
| F-4 | 按业务切片实现页面 | `frontend/src/pages`（dashboard/feedback/insights/roadmap/gov/settings） | 已实现 | FS-1 总览（指标卡/趋势/待处理/信号榜）、FS-2 反馈管理（筛选/分页/详情抽屉/状态流转）、FS-3 洞察（8 主题/四维评分/证据链）、FS-4/5 路线图（看板/任务/草稿审批回传/新建任务）、FS-6 政务适配、FS-7 设置页全部实现 | 动态（浏览器逐页验收通过，见下节） | 全流程可演示 | 完成 Dart 色与排版适配后收口 | 已关闭（验收通过） |
| F-5 | 配色与全屏排版适配（用户反馈） | `frontend/src/styles/main.css` 及页面布局 | 已实现 | 浅色主题：白侧栏（#ffffff）+ 品牌蓝活跃项（#2563eb）、body 背景 #f4f7fb、行高 1.6、内容区 max-width 1480px 居中、顶栏 56px；深色主题保留可切换；响应式断点（Dashboard 1200/640、Insights 1100、Roadmap 1200/700、Gov 1000、Settings 920） | 动态（浏览器近全屏 1854px 走查通过） | 交付观感 | 保持 | 已关闭 |
| F-6 | 前端全流程验证与 Docker 展示 | `frontend` 构建 + `deploy/docker-compose.yml` | 已实现 | `npm run build` 通过；docker compose 启动前端展示容器（默认 mock 模式），http://localhost:8090 可访问；nginx 已用变量化 upstream + Docker DNS resolver 修复 backend 未启动时独立展示 | 动态（容器内走查通过，见下节） | 交付演示 | 保持 | 已关闭 |
| F-7 | 颜色/排版全屏回归与容器内全流程闭环 | 全站 7 页面 + 容器版本 | 已实现 | 近全屏 1846/1854px 视口下 6 主页面无横向溢出；容器内 FS-0→FS-7 全流程走查通过 | 动态（浏览器验收） | 交付演示 | 保持 | 已关闭 |

## AI 功能阶段当前项

| ID | 需求或契约点 | 文件/模块/边界 | 分类 | 观察行为 | 证据等级 | 影响 | 建议处理 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-1 | AI 原生界面参考调研与设计选型 | `docs/frontend-development-plan.md`（AI 原生界面参考章节） | 已实现 | 研读 Ant Design X（RICH 范式：Bubble/Conversations/Prompts/Sender）、Page Assist（浏览器侧栏常驻聊天）、RuoYi AI（LangChain4j + RAG + 工作流编排）、OpenAI Intelligent UI（动态组合图表/按钮/表单）等开源项目，提取适用于政企 AI 工作台的布局模式与交互范式 | 静态（调研文档落盘） | 设计依据 | 供 A-2~A-4 沿用 | 已关闭 |
| A-2 | AI 总览面板重构（AI Dashboard） | `frontend/src/pages/dashboard/DashboardPage.vue`、`frontend/src/components/ai/AIChatPanel.vue` | 已实现 | 打破传统 KPI 面板排版：顶部 KPI 指标条 + 左侧数据区（趋势图/双栏列表）+ 右侧 AI 助手对话面板 + 底部 AI 工作流状态与自动化规则区；对话面板支持预设工作语句（如「今天工单情况如何」）调用 mock 工作流汇总结果，也支持开放自由聊天 | 动态（浏览器验收 + type-check/build） | 核心 AI 入口 | 保持 | 已关闭 |
| A-3 | AI 工作流状态与自动化规则面板 | `frontend/src/components/ai/AIWorkflowStatus.vue`、`AIAutomationRules.vue`、`frontend/src/stores/ai.ts` | 已实现 | 展示 AI 当前处理中的工作流/信息（按环节进度展示）；自动化区面向政企场景提供自动回复/自动分类/自动升级等预设规则配置开关 | 动态（浏览器验收） | 让 AI「可见可管」 | 保持 | 已关闭 |
| A-4 | 反馈管理 AI 化（AI 生成回复/自动审批/气泡助手） | `frontend/src/pages/feedback/FeedbackListPage.vue`、`frontend/src/stores/feedback.ts`、`frontend/src/mocks/feedbackDb.ts`（F1061-F1064 AI 状态示例） | 已实现 | ① AI 生成回复：点击「AI 生成回复」基于 mock 政策知识库生成回复草稿，等待人工审批；② AI 自动审批：对重复/无用提问自动采用统一话术回复并标记「AI 自动审批」，支持人工一键采用或驳回；③ AI 气泡助手：悬浮气泡组件，点击后向 AI 提问（如「这个问题怎么回复」），根据知识库返回回复建议；④ 状态流转新增 `ai_reviewing`（AI审核中）/`ai_replied`（AI已回复） | 动态（浏览器验收 + 状态标签映射） | 反馈闭环 AI 化 | 保持 | 已关闭 |
| A-5 | AI Mock 数据层与 API 适配 | `frontend/src/mocks/ai.ts`、`frontend/src/api/ai.ts`、`frontend/src/types/index.ts`（AIWorkflowStatus/AIAutomationRule/AIChatMessage） | 已实现 | mock 工作流/规则/对话数据与 `generateAIReply`/`getAIReplySuggestion`/`sendAIChat`/`getAIWelcomeMessage`；API 层 7 接口与后端契约对齐，`VITE_USE_MOCK` 可无缝切换真实后端 | 动态（type-check/build） | mock 先行切换桥梁 | 保持 | 已关闭 |
| A-6 | AI Mock 后端工作流骨架 | `backend/app/schemas/ai.py`、`backend/app/services/ai.py`、`backend/app/api/v1/ai.py`、`backend/app/api/v1/router.py` | 已实现 | 后端 AI 路由契约：GET /api/v1/ai/workflows；GET /api/v1/ai/automation-rules；POST /api/v1/ai/chat；GET /api/v1/ai/chat/welcome；POST /api/v1/ai/reply-draft；POST /api/v1/ai/reply-suggestion；POST /api/v1/ai/auto-approve/{feedback_id}；AIService 提供 mock 实现（工作流/规则/对话/回复生成/建议/自动审批），预留真实 LLM 与知识库替换点 | 静态（契约文件 + 与前端 api/ai.ts 逐接口核对一致） | 后端 AI 接入点 | 下一阶段替换为真实 LiteLLM/知识库实现 | 已关闭 |
| A-7 | AI 功能整体集成验证与容器部署 | `frontend` 构建 + `deploy/docker-compose.yml` | 已实现 | `npm run type-check` 通过（修复 SfIcon `message`→`chat` 类型错误）；`npm run build` 通过（1.35s）；Docker frontend 容器重建 healthy，最新 dist 部署至 http://localhost:8090 | 动态（type-check/build/容器走查） | 交付演示 | 保持 | 已关闭 |

## 扩展功能阶段当前项（2026-10-15 增补）

| ID | 需求或契约点 | 文件/模块/边界 | 分类 | 观察行为 | 证据等级 | 影响 | 建议处理 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E-1 | 反馈管理页 UI 与统计卡修复 | `frontend/src/pages/feedback/FeedbackListPage.vue`、`frontend/src/mocks/feedbackDb.ts`（聚合统计） | 已实现 | 反馈列表行间距与密度调整避免视觉密集；顶部新增状态统计卡（待解决 / AI 已生成 / AI 已自动回复 / 已解决等）；左侧导航条加宽、字号与布局调整消除「洞察与决策」等标签换行 | 动态（浏览器验收 type-check/build） | 可读性/信息密度 | 保持 | 已关闭 |
| E-2 | 详情抽屉与气泡助手重构 | `frontend/src/pages/feedback/FeedbackListPage.vue`、`frontend/src/components/ai/AIAssistantPanel.vue`、`frontend/src/components/ai/AIAnswerBubble.vue` | 已实现 | 详情抽屉补充回复内容展示（含 AI 草稿），非 AI 审批场景下支持人工修改 AI 草稿；右下角气泡助手按 image(4) 参考重构为完整 AI 助手面板：欢迎页 + 功能分类快捷入口 + 历史会话 + Agent/Chat 模式切换 + 免责声明，同时支持单条意见回复建议生成与自由聊天 | 动态（浏览器验收 + type-check/build） | 反馈闭环 AI 化 | 保持 | 已关闭 |
| E-3 | AI 自动化流程（重复工作自动处理） | `frontend/src/pages/automation/AutomationPage.vue`（或等价入口面板）、`frontend/src/stores/`、配置规则数据 | 已实现 | 基于产品规划实现重复性工作场景的 AI 自动化流程：自动分类、自动去重合并相似反馈、自动优先级升降级规则配置与执行面板，融入反馈管理或独立自动化入口，侧边栏提供入口 | 动态（浏览器验收 + type-check/build） | 重复人工提效 | 保持 | 已关闭 |
| E-4 | 商务合作信息 AI 提炼与市场动向报告 | `frontend/src/pages/business/BusinessPage.vue`、`frontend/src/stores/ai.ts`（商务汇总）、`frontend/src/mocks/ai.ts`（fetchBusinessLeads/IndustryShares/MarketSignals/CommonNeeds/InsightSummary）、`frontend/src/types/index.ts` | 已实现 | 从反馈中识别企业合作线索、按行业聚合分布、提炼市场动向信号、归纳跨企业共性需求并生成可视化汇总报告：顶部统计卡（企业合作线索/覆盖行业/市场动向信号/共性需求归纳）+ 企业线索/行业分布/市场动向/共性需求四个面板；线索推进（identified→qualified→pushed）保留人工确认 | 动态（浏览器验收 + type-check/build） | 商务联动新入口 | 保持 | 已关闭 |
| E-5 | 政务统计扩展与侧边栏入口重构 | `frontend/src/pages/gov/GovPage.vue`（全量重写）、`frontend/src/mocks/gov.ts`、`frontend/src/types/index.ts`、`frontend/src/components/common/SfIcon.vue`（新增 map/megaphone path）、`frontend/src/api/gov.ts`（保持单接口） | 已实现 | GovPage 重构为「6 张顶部统计卡（总诉求 48/本周新增 7/待办 12/逾期 3/按期办结率 81%/最高预警-橙色）+ 报告元信息条（统计周期·生成时间·AI 仅提炼声明）+ 7 个标签面板（诉求分级/督办事项/区域分布/热点主题/舆情预警/政策告知/审计留痕）」；舆情四级复用在 StatusBadge tone 白名单之外自绘 `.alert-blue/.alert-yellow/.alert-orange/.alert-red` 徽章；最高预警色 `.level-orange{color:#d97706}` | 动态（浏览器逐标签验收 + type-check/build + Docker 容器走查） | 政务演示闭环 | 保持 | 已关闭 |

## 运营驾驶舱扩展阶段当前项（2026-10-15 二次增补）

| ID | 需求或契约点 | 文件/模块/边界 | 分类 | 观察行为 | 证据等级 | 影响 | 建议处理 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-1 | 详情抽屉回复可见性与 AI 草稿区调高 | `frontend/src/pages/feedback/FeedbackListPage.vue`、`frontend/src/stores/feedback.ts` | 已实现 | 抽屉无论状态分支（已回复/无回复/AI 审核中）均展示回复内容区：已回复展示完整回复文本与发送人/时间；无回复展示编辑区；AI 草稿文本域 min-height 提升至约 160-200px，按钮区适度下移不拥挤 | 动态（浏览器验收 + type-check/build） | 反馈闭环 AI 化 | 保持 | 已关闭 |
| O-2 | 气泡助手全页面级推广与总览 AI 助手重设计 | `frontend/src/components/ai/AIFloatingAssistant.vue`（新增）、`AIChatPanel.vue`、各业务页面挂载点 | 已实现 | 除总览外全部业务页（反馈/洞察/路线图/政务/自动化/商务/访谈/工作流/Agent/资源）挂载带上下文感知的右下角气泡助手，每页预设问题按页面主题定制（如反馈页「批量生成待办回复」、洞察页「生成本周数据摘要」、政务页「热点诉求摘要」）；总览智能助手面板复用气泡助手结构（欢迎页/快捷入口/历史会话/Agent-Chat 切换/免责声明）+ 总览专属快捷指令（今日概览/异常提醒/自动化状态） | 动态（浏览器逐页验收 + type-check/build） | 全站 AI 入口统一 | 保持 | 已关闭 |
| O-3 | 总览面板信息块补充与客户访谈接入 | `frontend/src/pages/dashboard/DashboardPage.vue`、`frontend/src/pages/interview/InterviewPage.vue`（新增）、`frontend/src/mocks/interviews.ts`、`frontend/src/api/interviews.ts`、`frontend/src/stores/interviews.ts` | 已实现 | 总览 Dashboard 扩展为全局运营驾驶舱：新增自动化任务运行状态、商务线索待跟进数、政务预警待处理数、Agent/工作流启用状态、资源健康概况等卡片；新增侧边栏「客户访谈」入口：IV-001~IV-006 访谈列表（录音/纪要/AI 提炼痛点与需求），访谈中识别合作意向自动汇入商务线索池、痛点自动匹配共性需求 | 动态（浏览器验收 IV-002 联动 + type-check/build） | 全局驾驶舱 + 商务联动 | 保持 | 已关闭 |
| O-4 | Agent/Skill 配置中心与资源管理入口 | `frontend/src/pages/agents/AgentConfigPage.vue`、`frontend/src/pages/resources/ResourceMonitorPage.vue`（新增）、`frontend/src/mocks/{agents,resources}.ts`、`frontend/src/api/{agents,resources}.ts`、`frontend/src/stores/{agents,resources}.ts` | 已实现 | 侧边栏新增「Agent 配置」页：5 个预置 Agent 卡片（政策公告/商单回复/舆情聚类/邻里诉求/反馈自动回复），各含名称/类型/运行次数/场景/工具权限/绑定工作流/成功率/最近运行/配置开关与新建；「资源管理」页：服务器健康 3/4、数据库 2/3、API 13/14、活跃告警 5（最高严重），日志与告警 tab（含 milvus 向量检索延迟 WARN、report-service 导出失败 ERROR） | 动态（浏览器逐 tab 验收 + type-check/build） | 运维可观测 | 保持 | 已关闭 |
| O-5 | LangGraph 工作流配置入口与闭环联动 | `frontend/src/pages/workflows/WorkflowConfigPage.vue`（新增）、`frontend/src/mocks/workflows.ts`、`frontend/src/api/workflows.ts`、`frontend/src/stores/workflows.ts` | 已实现 | 侧边栏新增「工作流配置」页：5 个预置模板（发布公告/商单自动回复/自动分类与去重/舆情监测与应急/多源诉求聚合解决），每卡片含描述/触发条件/LangGraph 节点流程图（开始→…→结束）/Agent 绑定/工具链/运行历史/状态开关；总览「启用全部工作流」开关真实映射工作流启用状态 | 动态（浏览器闭环验证 + type-check/build） | 编排可见可管 | 保持 | 已关闭 |
| O-6 | 集成闭环联动与 store 守卫修复 | `frontend/src/stores/{workflows,agents,interviews}.ts`、`frontend/src/stores/ai.ts`（6 个 fetch 方法） | 已实现 | 修复页面 onMounted 无条件 fetch 覆盖用户配置的缺陷：给 4 个 store 的 9 个 fetch 方法加 `force=false` 守卫（已有数据跳过重取）；「总览开关→工作流配置页」状态镜像闭环（4/5→5/5 并保持）；「访谈→商务线索」联动闭环（IV-002 生成 BL-007 并置顶商务页线索池顶部） | 动态（SPA 内导航整链路验收 + type-check/build） | 会话内状态一致性 | 保持 | 已关闭 |

## 动态验证证据（前端页面切片验收 2026-10-14 首轮 + 2026-10-15 增补）

| 检查项 | 命令/方式 | 结果 |
| --- | --- | --- |
| 前端类型检查 | `npm run type-check` | 通过（修复 Skeleton rows 字符串 prop、StatCard deltaTone union 扩展、filters 显式类型、noUnusedLocals 4 类问题） |
| 反馈筛选 | 状态下拉 + 查询按钮 | 「新增」24 条（F1055 因已回复被正确排除）、「已回复」5 条（F1055 居首） |
| 分页 | 下一页/上一页 | 第 1→2→1 页往返正常，列表与页码正确（setFilter 分页 bug 已修复并回归） |
| 草稿回传闭环 | 路线图 D3001：审批→回传 → 反馈管理 | 回传后 feedbackDb.F1055 = replied（reviewer=智能回传）；SPA 跳转反馈页列表显示「已回复/智能回传」 |
| 信号榜跳转 | 总览页点击信号榜主题 | 跳转 /insights 并选中「大厅等候时间过长」，评分 92、四维卡与证据链（含 F1055）渲染正确 |
| 新建任务 | 路线图「新建任务」抽屉 | 表单（路线图/标题/负责人/优先级）提交后对话框关闭，看板新增任务「验收测试：开窗规则试运行」于 R2001 待办列 |
| FS-6 政务适配 | /gov 浏览器验证 | 诉求分级 A-D（2/11/28/7）、督办事项三级表（1/3/1、8/2）、政策告知（已发布+草稿）渲染正常，「导出报告」点击无报错 |
| FS-7 设置 | /settings 浏览器验证 | 渠道接入表 6 渠道（工单/门户/评价/热线/访谈/商务）状态与同步时间、数据源与权限说明正常 |
| 生产构建 | `npm run build` | 通过（vue-tsc --noEmit + vite build，2.01s，产物 dist/assets 正常） |
| 配色全屏走查 | 独立浏览器 1854×920（近全屏）逐页 | 总览/反馈/洞察/路线图/政务/设置 6 页均无横向溢出；body #f4f7fb、白侧栏、活跃项品牌蓝、内容区 1480px 居中、行高 1.6；深色切换正常 |
| Docker 展示 | `docker compose up -d --no-deps frontend`（FRONTEND_PORT=8090） | 容器启动 http://localhost:8090 可访问，Mock 徽标显示，页面标题正常 |
| 容器内全流程（FS-0→FS-7） | 浏览器打开容器展示实例 | FS-0 应用壳（6 导航/KPI 卡/图表）；FS-1 总览跳转洞察；FS-2 反馈筛选/详情抽屉/状态流转（新增→分析中）；FS-3 洞察证据链+四维评分；FS-4 路线图新建任务回写看板；FS-5 D3001 审批→回传→反馈页 F1055 显示「已回复/智能回传」；FS-6 政务适配 4 卡片；FS-7 设置渠道接入表 |
| AI 整体类型检查 | `npm run type-check` | 通过（修复 SfIcon `name="message"` → `name="chat"` 的 IconName 联合类型错误，回归无新问题） |
| AI 总览面板（A-2） | 浏览器打开 /dashboard | 顶部 KPI 指标条 + 左侧趋势图/双栏列表 + 右侧 AI 助手对话面板渲染正常；面板宽高比例合理、无超大字体/过度留白；AI 工作流状态卡片与自动化规则区位于面板底部，可读可切换 |
| AI 对话（A-2） | AI 助手面板输入「今天工单情况如何」 | 预设语句调用 mock 工作流，返回按渠道聚合的工单汇总（示例：新工单量/趋势/高优先级提示）；自由聊天输入返回 AI 欢迎语与对话气泡，输入框 Sender/发送按钮交互正常 |
| AI 工作流状态（A-3） | /dashboard 底部 AIWorkflowStatus | 展示当前运行中工作流（含环节/进度/状态标记），无空态渲染异常；规则卡片开关可切换，状态反馈即时 |
| AI 生成回复（A-4） | 反馈列表选择一条新反馈 → AI 生成回复 | 生成回复草稿展示于 AI 操作区，来源标注「AI 草稿/依据 mock 知识库」，等待人工审批；再次生成可刷新草稿；清空草稿按钮生效 |
| AI 自动审批（A-4） | 反馈列表执行 AI 自动审批 | 对命中重复/无用规则的单据生成统一话术回复并标记「AI自动审批」标签，状态流转为 `ai_replied`；人工可采用或驳回 |
| AI 气泡助手（A-4） | 点击反馈列表右下角 AI 悬浮气泡 | 气泡展开对话面板，提问后返回基于 mock 知识库的回复建议，可「插入到回复」填充 AI 草稿区 |
| AI 状态流转（A-4） | `frontend/src/mocks/feedbackDb.ts` F1061-F1064 | 4 条 AI 状态示例数据（ai_reviewing/ai_replied）在列表中正确显示「AI审核中」「AI已回复」标签，筛选 AI 状态可命中 |
| AI 后端契约核对（A-6） | 前后端 7 接口逐项比对 | `frontend/src/api/ai.ts` 与 `backend/app/api/v1/ai.py` 的路径、方法、入参、出参完全一致；前端 `http.ts` baseURL `/api/v1` 与后端 router 前缀一致，`VITE_USE_MOCK=false` 可无缝切换 |
| AI 容器部署（A-7） | `docker compose up -d --build --no-deps frontend`（FRONTEND_PORT=8090） | 容器重建 healthy，http://localhost:8090 可访问，最新 dist 已部署，AI 面板与反馈 AI 功能在容器内可操作 |
| 反馈统计卡（E-1） | /feedback 浏览器验证 | 顶部状态统计卡（待解决/AI 已生成/AI 已自动回复/已解决等）与列表数据一致；列表行间距与密度调整后视觉不密集；左侧导航条加宽后「洞察与决策」等标签不再换行 |
| 详情抽屉回复展示与 AI 草稿可改（E-2） | /feedback 打开详情抽屉 | 抽屉内展示已回复内容与 AI 回复草稿；非 AI 审批场景下可编辑 AI 草稿再保存/采用 |
| 气泡助手重构（E-2） | /feedback 右下角 AI 悬浮气泡 | 完整 AI 助手面板：欢迎页 + 功能分类快捷入口 + 历史会话 + Agent/Chat 模式切换 + 免责声明；对单条意见可生成回复建议并插入草稿区，自由聊天正常 |
| AI 自动化（E-3） | 自动化入口浏览器验证 | 自动分类/自动去重合并/自动优先级升降级规则配置与执行面板可操作，规则可开关，执行反馈即时 |
| 商务洞察（E-4） | /business 浏览器验证 | 顶部统计卡（企业合作线索/覆盖行业/市场动向信号/共性需求归纳）+ 企业线索/行业分布/市场动向/共性需求 4 面板渲染正常，行业分布含 pct 与占比展示，市场动向与共性需求来自 mock 企业反馈聚合 |
| 政务统计卡（E-5） | /gov 浏览器验证 | 6 张顶部统计卡数值正确（总诉求 48/本周新增 7/待办 12/逾期 3/按期办结率 81%/最高预警-橙色）+ 报告元信息条（统计周期·生成时间·AI 仅提炼声明） |
| 政务 7 标签逐项（E-5） | /gov 7 个标签逐一 eval 切换 | 诉求分级 A-D 四级 BarRow（2/11/28/7）；督办三级表（1/0、3/1、8/2 逾期）；区域分布 6 区（玄武 25% 电梯加装/住建局+规划局 等）+ pct + 部门 chips；热点主题 4 条（GT-2601 已生成治理任务并显示「治理任务 GT-2601-治理 已进入督办流程」，GT-2602~2604 待生成，含痛点成因 + 原话引用证据，数值与 mock 一致 17/+28、15/+35、11/-8）；舆情预警 4 条（BR-001 蓝/YE-002 黄/OR-003 橙/RD-004 红，徽章 class alert-blue/yellow/orange/red 全部正确绑定，RD-004 已派发住建局应急专班）；政策告知 3 条（N4001/4002/4003，含送达人数/阅读率/渠道新字段）；审计留痕 5 条（A5001~5005） |
| 扩展功能类型检查 | `npm run type-check`（frontend） | 通过（SfIcon 补充 map/megaphone path 后无类型错误） |
| 扩展功能生产构建 | `npm run build`（frontend） | 通过（vue-tsc --noEmit + vite build，约 3.09s，产物 dist/assets 正常） |
| 扩展功能 Docker 集成（position 6） | `docker compose up -d --build`（FRONTEND_PORT=8088，因本机 8080 被 edunash-nginx 占用） | 四容器（postgres(pgvector)/redis/backend/frontend）全部 healthy；后端健康路由经 `curl http://localhost:8000/api/v1/healthz` 返回 `{"status":"ok","service":"signalflow-backend"}`；容器版 http://localhost:8088/gov 走查通过（6 统计卡 + 7 标签 + 四级预警徽章）；前端容器内全流程可操作 |
| 后端健康路由确认（position 6） | `curl http://localhost:8000/healthz` vs `/api/v1/healthz` | 裸 `/healthz` 返回 404；实际健康路由为 `/api/v1/healthz`（`backend/app/api/v1/health.py`），compose 与 deploy/README 中过时注释已同步修正 |
| 后端 gov 契约边界确认（position 6） | `curl http://localhost:8000/api/v1/gov/overview` | 返回 404（backend `router.py` 仅注册 health/feedbacks/insights/ai，未注册 gov 路由）；当前 mock 模式前端不依赖真实接口，真实 `/gov/overview` 契约列入下一阶段 |
| 运营驾驶舱 type-check（O-1~O-6） | `npm run type-check`（frontend） | 通过（vue-tsc --noEmit，新增 agents/interviews/resources/workflows 页面与 store 后无类型错误） |
| 运营驾驶舱生产构建（O-1~O-6） | `npm run build`（frontend） | 通过（vue-tsc --noEmit + vite build，`✓ built in 2.27s`，产物 dist/assets 正常） |
| 详情抽屉回复可见性（O-1） | /feedback 打开多条详情抽屉 | 已回复条目展示完整回复文本与发送人/时间；AI 审核中条目展示 AI 草稿；AI 草稿文本域高度调高（min-height 约 160-200px），按钮区不拥挤 |
| 气泡助手各页（O-2） | 反馈/洞察/路线图/政务/自动化/商务等页右下角 | 每页出现带上下文感知的悬浮气泡助手，预设问题随页面主题变化（反馈页「批量生成待办回复」、洞察页「生成本周数据摘要」、政务页「热点诉求摘要」等） |
| 总览 AI 助手与快捷指令（O-2） | /dashboard 总览面板 | 智能助手面板含欢迎页/快捷入口/历史会话/Agent-Chat 切换/免责声明 + 今日概览/异常提醒/自动化状态快捷指令 |
| 总览信息块（O-3） | /dashboard 浏览器验收 | 自动化任务运行状态、商务线索待跟进数、政务预警待处理数、Agent/工作流启用状态、资源健康概况等卡片渲染正常 |
| 客户访谈页（O-3） | /interview 浏览器验收 | IV-001~IV-006 六条访谈记录（公司/联系人/渠道/时长/日期），含 AI 提炼痛点与需求；IV-002 中科软联高意向候选（数据不出域/私有化部署诉求） |
| Agent 配置页（O-4） | /agents 浏览器验收 | 5 个预置 Agent 卡片（政策公告/商单回复/舆情聚类/邻里诉求/反馈自动回复），各含运行次数/场景/工具权限/绑定工作流/成功率/最近运行/配置开关；新建入口可用 |
| 资源管理页（O-4） | /resources 浏览器验收 eval 逐 tab | 服务器健康 3/4、数据库 2/3、API 13/14、活跃告警 5（最高严重）；日志与告警 tab 内 10 条日志（milvus 向量检索延迟 WARN、report-service 导出失败 ERROR） |
| 工作流配置页（O-5） | /workflows 浏览器验收 | 5 个预置模板（发布公告/商单自动回复/自动分类与去重/舆情监测与应急/多源诉求聚合解决），每卡片含描述/触发条件/节点流程图（开始→…→结束）/Agent 绑定/工具链/运行历史/状态开关 |
| 总览开关→工作流状态镜像（O-6） | 整页刷新 `/` → 点总览「启用全部工作流」→ SPA 点侧栏 `/workflows` | 初始 4/5 → 点击总览开关变 5/5 → SPA 导航工作流页后「多源诉求聚合解决」从「已停用」保持「已启用」，状态镜像一致（store 守卫防覆盖生效） |
| 访谈→商务线索联动（O-6） | 整页刷新 `/` → SPA `/interview` → 选 IV-002 → 「生成商务线索并汇入线索池」→ SPA `/business` | 访谈页显示「已生成商务线索 BL-007」；商务页「企业合作线索」列表顶部置顶出现 BL-007（中科软联/私有化与数据不出域诉求，客户价值 85、置信度 85%、带访谈来源引用，状态-待确认） |

### 重要结论：草稿回传「未回写」疑点澄清

- 现象：此前验收发现 D3001 回传后反馈页 F1055 仍显示「新增」，疑似回写未生效。
- 根因：**并非代码缺陷**。mock 数据为前端模块内存态，`page.goto` 整页导航会让浏览器重新加载模块、内存数据复位为初始值；此前「回传→跳转反馈页」使用了整页导航，导致回写结果被重置。
- 验证：同一页面会话内回传后用 SPA 链接（点击侧栏导航）跳转反馈页，F1055 正确显示「已回复/智能回传」；且「新增」列表从 25 条变为 24 条，证明回写真实发生在内存库。
- 影响：代码链路（store → api → mock 写操作）正确无需修改；验收与演示时应使用 SPA 内导航而非整页刷新；接入真实后端后状态持久化，无此限制。已在 `docs/frontend-development-plan.md` 验收注意事项补充。

## 通俗语言发现

1. **用户或系统需要什么**：前端以模拟数据跑通全流程闭环，页面紧凑、信息密度合理、突出"反馈→洞察→决策→行动"的产品理念；总览面板需要由 AI 参与——既有传统数据展示，也有 AI 对话（预设工作语句 + 自由聊天）、AI 处理中信息/工作流状态展示与自动化规则配置；反馈管理需要引入 AI 回复生成、自动审批与气泡助手；2026-10-15 进一步要求：反馈页行距与统计卡、气泡助手按参考图重构、详情抽屉展示回复且 AI 草稿可改、按优先级分阶段开发（UI 走查 → 气泡助手 → AI 自动化 → 商务洞察 → 政务扩展）；随后要求把总览扩展为全局运营驾驶舱（自动化/线索/预警/Agent/工作流/资源健康）、新增客户访谈与商务联动、建立 Agent/Skill 配置中心与资源管理入口、提供 LangGraph 工作流配置入口并保证各功能闭环联动。
2. **现在发生了什么**：前端全流程计划、功能切片与设计规范已落盘（MD），ADR-0002 已记录 mock 先行决策；mock 数据层、API 适配、stores、FS-0 应用壳与 FS-1~FS-7 全部页面已实现；AI 总览面板重构（对话栏/工作流状态/自动化规则）、反馈管理 AI 化（AI 生成回复/自动审批/气泡助手/AI 状态流转）、AI Mock 后端工作流骨架（7 接口契约与前端对齐）已完成；2026-10-15 增补完成反馈统计卡与行距/导航修复、详情抽屉回复展示与 AI 草稿可改、气泡助手完整面板重构（欢迎页/快捷入口/历史会话/模式切换/免责声明）、AI 自动化流程（分类/去重合并/优先级规则）、商务洞察（线索/行业/动向/共性需求四面板）与政务统计扩展（6 统计卡 + 7 标签 + 四级预警）；2026-10-15 二次增补完成运营驾驶舱扩展（详情抽屉回复可见性与 AI 草稿区调高、气泡助手全页面推广与总览 AI 助手重设计、总览信息块与客户访谈接入、Agent 配置中心与资源管理入口、LangGraph 工作流配置入口与三向闭环联动）并修复 mock 阶段 store 覆盖缺陷（4 store 9 个 fetch 方法加 force 守卫）；`npm run type-check` + `npm run build` 通过，Docker compose 四容器 healthy（前端 8088）。
3. **应该发生什么**：全部新增功能由 mock 数据驱动，前端可独立演示（不依赖真实后端）；验收与演示必须使用 SPA 内导航而非整页刷新（整页刷新会重置 mock 内存态）；真实后端 gov 契约（`/gov/overview`）与真实 LLM 接入、政务知识库对接属于下一阶段（见 `docs/next-stage-plan.md`）。
4. **为什么差异重要**：统计卡让「待办/逾期/办结率」一眼可见；气泡助手与抽屉改造使 AI 草稿可人工干预，符合政企「AI 辅助 + 人工兜底」原则；AI 自动化与商务/政务扩展覆盖产品规划的推销联动与政务场景，增强演示完整性；运营驾驶舱把自动化、线索、预警、Agent/工作流/资源健康统一到总览，配合工作流配置与访谈→线索联动形成「配置→执行→回显」闭环，演示叙事更完整；store 守卫修复保证会话内用户操作不被页面挂载重取覆盖，是 mock 阶段状态一致性的关键；mock 适配层保证后续接真实 LLM/知识库零改动。
5. **证据与受影响边界**：FS-1~FS-7 与 E-1~E-5 及 O-1~O-6 全部页面交互闭环均有浏览器证据；type-check/build/容器部署（8088）通过；mock 阶段已知限制：整页刷新会重置 Pinia store 内存态，验收/演示须用 SPA 内导航；后端 AI 服务当前为 mock 实现，真实 LLM、政务知识库与后端 `/gov/overview` 合约未实施。
6. **建议的下一步（不声称已完成）**：进入下一阶段——真实 LLM 接入（LiteLLM 统一网关 + LangGraph 工作流）、政务知识库对接（RAG 检索）与后端政务接口契约补齐，替换 mock 服务实现；本阶段成果已提交并推送至私有 GitHub 仓库。

## 评审覆盖与关闭标准

- 已评审文件/模块与深度：工程骨架目录与配置（首轮）+ 前端规划文档、ADR-0002 的内容完整性与流程符合度 + mock 数据层/API 适配/stores/应用壳/路由 + FS-1~FS-7 全部页面实现的浏览器可见验收 + AI 总览面板/反馈管理 AI 化/后端 AI mock 契约（A-1~A-7）的浏览器验收与 type-check/build/容器部署验证 + E-1~E-5 扩展功能（反馈 UI 与统计卡/详情抽屉与气泡助手/AI 自动化/商务洞察/政务统计扩展）的浏览器验收与 type-check/build/Docker 集成验证 + O-1~O-6 运营驾驶舱扩展（详情抽屉回复可见性/气泡助手全页面/总览信息块与客户访谈/Agent 配置/资源管理/工作流配置/集成闭环与 store 守卫）的浏览器验收与 type-check/build 验证。
- 未检查的文件或边界：真实 LLM 接入与政务知识库对接（下一阶段）、后端 AI mock 服务在真实 FastAPI 运行时的手工 curl 验证（后端依赖未安装，契约以静态核对为准）、后端 `/gov/overview` 真实接口（未注册，属下一阶段契约补齐）。
- 关闭前端规划项所需证据：切片实现完成后的浏览器可见验收（`docs/frontend-development-plan.md` §3.3）；文档本身的"已落盘"证据为文件存在与内容核对。
- 最后检查版本或日期：2026-10-15。

## 删除或合并候选

当前无删除/合并候选；规划文档与 ADR 为流程要求的新增产物，未发现重复内容。