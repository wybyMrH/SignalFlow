# 下一阶段计划

文档就绪度：confirmed（前端 mock 全流程切片 + AI 总览/反馈 AI 化 + AI Mock 后端骨架 + 2026-10-15 反馈 UI 与统计卡/气泡助手重构/AI 自动化/商务洞察/政务统计扩展 + 2026-10-15 二次运营驾驶舱扩展（总览信息块/客户访谈/Agent 配置/资源管理/工作流配置/闭环联动与 store 守卫修复）均已闭环，当前进入「真实 LLM 接入与政务知识库对接、后端政务契约补齐」）

## 上一阶段回执（2026-10-14 前端 mock 全流程切片 + AI 功能）

- **已完成**：FS-0 应用壳 → FS-1 总览 → FS-2 反馈管理 → FS-3 洞察 → FS-4/5 路线图（含草稿审批回传）→ FS-6 政务适配 → FS-7 设置，全部由 mock 数据驱动并逐页浏览器验收；配色已按用户反馈调整为淡色有活力风格（白侧栏 + 品牌蓝 + body #f4f7fb + 行高 1.6 + 内容区 1480px 居中 + 断点适配），近全屏 1854px 视口 6 个主页面均无横向溢出。
- **AI 功能已完成（A-1~A-7）**：AI 总览面板重构（KPI + 数据区 + AI 对话面板 + 工作流状态 + 自动化规则）；反馈管理 AI 化（AI 生成回复草稿/等待人工审批、AI 自动审批统一话术回复并标记、AI 气泡助手、`ai_reviewing`/`ai_replied` 状态）；AI Mock 后端工作流骨架（`backend/app/{schemas,services,api/v1}/ai.py`，7 接口与前端 `api/ai.ts` 契约对齐，`VITE_USE_MOCK=false` 可无缝切换）。
- **验证证据**：`npm run type-check`（修复 SfIcon `message`→`chat`）与 `npm run build`（vue-tsc + vite build，1.35s）通过；Docker Desktop `docker compose up -d --build --no-deps frontend`（FRONTEND_PORT=8090）容器 healthy，最新 dist 部署至 http://localhost:8090；AI 面板/对话/工作流状态/自动化规则/回复生成/自动审批/气泡助手逐项浏览器验收通过。
- **文档**：详见 `docs/current-state.md` F-1~F-7、A-1~A-7 与 E-1~E-5、`docs/adrs/ADR-0002-前端mock先行与轻量设计体系.md`。

## 本轮增补收尾（2026-10-15）

- **已完成（E-1~E-5）**：① 反馈管理页 UI 与统计卡修复——列表行距/密度调整、顶部状态统计卡（待解决/AI 已生成/AI 已自动回复/已解决）、左侧导航条加宽消除换行；② 详情抽屉与气泡助手重构——抽屉展示回复内容、非 AI 审批场景 AI 草稿可编辑；气泡助手按 image(4) 参考重构为完整 AI 助手面板（欢迎页/功能分类快捷入口/历史会话/Agent-Chat 模式切换/免责声明），支持单条意见回复建议与自由聊天；③ AI 自动化流程——自动分类、自动去重合并相似反馈、自动优先级升降级规则配置与执行面板；④ 商务合作信息 AI 提炼——企业线索/行业分布/市场动向/共性需求四面板 + 顶部统计卡，实现产品规划「推销联动」切片；⑤ 政务统计扩展——GovPage 全量重写为 6 顶部统计卡 + 报告元信息 + 7 标签面板（诉求分级/督办事项/区域分布/热点主题/舆情预警/政策告知/审计留痕），舆情四级自绘徽章（StatusBadge 无 orange）；侧边栏按需新增入口并统一样式，SfIcon 补 map/megaphone path。
- **验证证据（2026-10-15）**：`npm run type-check` 通过；`npm run build` 通过（约 3.09s）；Docker compose 四容器（postgres(pgvector)/redis/backend/frontend）重建后全部 healthy，前端 http://localhost:8088（本机 8080 被 edunash-nginx 占用故 .env 设 FRONTEND_PORT=8088，`deploy/.env` 不入库）；后端健康路由经 `curl http://localhost:8000/api/v1/healthz` 确认（裸 /healthz 为过时文档，已同步修正）；容器版 /gov 走查通过（7 标签逐项 eval 核验 + 四级预警徽章 class 绑定正确）；政务页动态验证细节见 `docs/current-state.md` 动态验证证据表。
- **边界确认**：后端 `router.py` 尚未注册 gov 路由（`curl /api/v1/gov/overview` 404）；mock 模式前端不依赖真实接口，真实 `/gov/overview` 契约列入下一阶段。

## 运营驾驶舱扩展收尾（2026-10-15 二次增补）

- **已完成（O-1~O-6）**：① 详情抽屉回复可见性与 AI 草稿区调高——所有状态分支均展示回复内容区（已回复完整文本/无回复编辑区/AI 审核中草稿区），文本域 min-height 提升至 160-200px；② 气泡助手全页面级推广——除总览外全部业务页右下角挂载上下文感知气泡助手，预设问题随页面主题定制，总览 AI 助手按气泡助手结构重设计并加总览专属快捷指令；③ 总览面板信息块补充与客户访谈接入——Dashboard 扩展为运营驾驶舱（自动化状态/线索待跟进/政务预警/Agent 与工作流启用/资源健康），新增客户访谈页（IV-001~IV-006、AI 提炼痛点与需求），访谈合作意向自动汇入商务线索池；④ Agent/Skill 配置中心与资源管理入口——AgentConfigPage（5 预置 Agent 卡片/工具权限/工作流绑定/开关/新建）与 ResourceMonitorPage（服务器 3/4、数据库 2/3、API 13/14、告警 5、日志 tab）；⑤ LangGraph 工作流配置入口——5 预置模板（发布公告/商单自动回复/自动分类与去重/舆情监测与应急/多源诉求聚合解决），含节点流程图/触发条件/Agent 绑定/工具链/运行历史/状态开关；⑥ 集成闭环与 store 守卫修复——修复页面 onMounted 无条件 fetch 覆盖用户配置的缺陷（workflows/agents/interviews/ai 4 store 9 个 fetch 方法加 `force=false` 守卫），验证「总览开关→工作流配置页」状态镜像（4/5→5/5 保持）与「访谈→商务线索」联动（IV-002 → BL-007 置顶商务页）。
- **验证证据（2026-10-15 二次）**：`npm run type-check` 通过；`npm run build` 通过（`✓ built in 2.27s`）；浏览器 SPA 内导航整链路验收：整页刷新 `/`（初始线索池/4/5）→ 点总览「启用全部工作流」变 5/5 → SPA 导航 `/workflows`「多源诉求聚合解决」保持已启用 → SPA 导航 `/interview` 选 IV-002 →「生成商务线索并汇入线索池」→ 访谈页显示「已生成商务线索 BL-007」→ SPA 导航 `/business` 验证 BL-007（中科软联/私有化与数据不出域，客户价值 85/置信度 85%）置顶列表。「总览开关→工作流配置页」与「访谈→商务线索」两条跨页面闭环均通过；详细证据见 `docs/current-state.md` O-1~O-6 与动态验证证据表。
- **关键经验**：mock 为前端内存态，`goto` 整页刷新会重置 Pinia store；验收/演示必须用 SPA 内导航（eval 点击侧栏 a 标签）；页面 onMounted 无条件 fetch 会用 mock 初始数据覆盖用户会话内操作，fetch 需带 `force=false` 守卫（ResourceMonitorPage 的条件拉取为正确参照）。

## 选定切片

- 需求与可观察结果：**① 真实 LLM 接入**——用 LiteLLM 统一网关接入可用大模型（本地/云端均可，先 mock-able 配置），替换 `backend/app/services/ai.py` 中 reply 生成与对话总结的 mock 实现为真实调用；**② 政务知识库对接**——建立 mock 本地政策知识库 + RAG 检索链路（向量化 + 检索 + 上下文注入），使 AI 回复/建议基于知识库内容生成并标注来源；**③ 前端演示开关**——`VITE_USE_MOCK=false` 时前端真实调用后端 AI 接口，Docker compose 中 frontend+backend 同时可访问；**④ 后端政务契约补齐**——按 `frontend/src/types/index.ts` 与 `frontend/src/mocks/gov.ts` 定义实现 `backend` 的 `/api/v1/gov/overview`（诉求分级/督办/区域分布/热点主题/舆情预警/政策告知/审计留痕），替换前端 mock 分支。
- 当前行为 → 目标行为：当前 AI 与政务功能完全由前端 mock 与后端 mock 服务驱动；目标为同一套 UI/契约下由真实 LLM + 知识库检索生成回复与总结，政务统计由真实后端接口提供，产品可演示「AI 参与决策」的真实效果。
- 拥有边界、必要组件与排除项：`backend/app/services/ai.py`（真实实现替换）、`backend/app/services/knowledge.py`（知识库检索 mock/RAG 骨架）、`backend/app/workflows/`（LangGraph 工作流编排）、`backend/pyproject.toml`（litellm/向量库依赖）、`backend/app/api/v1/gov.py`（政务契约实现，注册进 `router.py`）；排除真实政务数据库对接（先以本地 mock 政策文档作为知识库源）、真实渠道接入、登录鉴权（仍以演示环境处理）。
- 前置条件与交接契约：前端 `api/ai.ts` 与后端契约保持 A-6 已定义 7 接口不变；输出格式（回复文本/建议/来源标注）与前端 `types/index.ts` 对齐；`VITE_USE_MOCK` 切换文档沿用。
- 为什么这是优先级与合适阶段大小：AI 是产品差异化的核心，真实 LLM + 知识库是「AI 参与面板」与「AI 自动回复」从演示走向可用的关键；边界可独立验证（curl 后端 AI 接口 + 前端真实数据渲染）。

## 验收与证据

- 正常路径：后端容器启动后 `curl -X POST /api/v1/ai/chat` 与 `curl -X POST /api/v1/ai/reply-draft` 返回真实生成内容（含知识库来源标注，若检索命中）；`GET /api/v1/ai/workflows` 返回真实执行状态；前端 `VITE_USE_MOCK=false` 且 backend 可用时，AI 对话与 AI 回复草稿渲染真实返回；知识库检索在无命中时给出明确「未检索到相关依据」降级文案。
- 相关失败或取消：无可用 LLM 密钥/服务时停止并报告，不伪造生成结果；后端未启动时前端仍可回退 mock 演示，不白屏。
- 重复、重试、重启、权限或恢复检查：LLM 调用失败重试策略（LiteLLM 重试/降级到 mock）；知识库索引重建后可再次检索；推送前检查远程仓库存在性与权限。
- 非专业人士可检查的证据：curl 请求/响应样例（含真实生成文本）、前端 AI 对话与回复草稿真实渲染截图、知识库来源标注截图。
- 证据等级与限制：curl/浏览器真实可见；生成内容质量依赖所选 LLM 能力，需人工抽查。

### 生成内容评估

本切片将产生 LLM 生成文本（回复草稿/对话总结/建议），需启用模型评审流程：抽查生成内容与知识库依据的一致性、政企话术合规性、来源标注准确性；发现幻觉或越权内容时回退为 mock 或人工审批兜底（AI 自动审批仍保留人工可驳回入口）。

## 依赖与决策

- 需要的用户决策：LLM 供应来源（本地模型 / 云端 API / 暂用公开演示 key）与知识库源文档（是否提供真实政策文件，或继续使用 mock 政策文档）。
- 技术调研或 ADR 前置：新增 ADR-0003 记录真实 LLM 接入与知识库选型（LiteLLM 网关 + 向量检索方案）；如引入新依赖需先验证可安装。
- 安全、数据或迁移风险：LLM 与知识库内容涉及政务数据，只使用用户授权/公开文档；API key 写入环境变量（`.env`，不入库）；生成内容保留人工审批环节；推送前复查无敏感文件入仓。

## 完成与回退

- 交付物与可观察结果：后端 AI 服务真实实现可 curl 验证；知识库检索链路可用并返回来源；前端 `VITE_USE_MOCK=false` 真实调用渲染通过；文档更新到 `docs/current-state.md`。
- 判定切片完成的准则：curl 两个以上 AI 接口返回真实生成内容；知识库命中/未命中两分支验证通过；前端真实数据渲染验收通过。
- 需替换或刷新的当前快照与回退界限：完成时更新 `docs/current-state.md` 与 `docs/next-stage-plan.md`；回退界限为还原 `backend/app/services/ai.py` 至 mock 实现（前端与契约保持不动）。
- 验证后需检查清理的一次性测试/运行产物：本地临时 curl 数据、dist 构建产物（按 `.gitignore` 策略）、docker 运行日志。

## 后续候选（仅候选，非承诺）

- 真实政务数据端到端对接：工单/门户/评价等真实渠道数据入库，知识库替换为真实政策库。
- 反馈分类模型与渠道接入：以真实数据训练/微调分类，替换 mock 主题/优先级数据。
- 商务洞察后端契约：按 `mocks/business.ts` 实现后端商务汇总接口（当前仅前端 mock）。
- 登录鉴权与多租户：演示环境收口为可交付内部试用版本。