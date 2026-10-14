# 下一阶段计划

文档就绪度：confirmed（上一阶段「前端 mock 全流程切片」已闭环，当前进入「仓库就绪 + 后端最小闭环」）

## 上一阶段回执（2026-10-14 前端 mock 全流程切片）

- **已完成**：FS-0 应用壳 → FS-1 总览 → FS-2 反馈管理 → FS-3 洞察 → FS-4/5 路线图（含草稿审批回传）→ FS-6 政务适配 → FS-7 设置，全部由 mock 数据驱动并逐页浏览器验收；配色已按用户反馈调整为淡色有活力风格（白侧栏 + 品牌蓝 + body #f4f7fb + 行高 1.6 + 内容区 1480px 居中 + 断点适配），近全屏 1854px 视口 6 个主页面均无横向溢出。
- **验证证据**：`npm run type-check` 与 `npm run build`（vue-tsc + vite build）通过；Docker Desktop `docker compose up -d --no-deps frontend`（FRONTEND_PORT=8090）容器 healthy，http://localhost:8090 可访问；容器内 FS-0→FS-7 全流程走查通过（草稿回传使用 SPA 内导航，mock 内存态不回退）。
- **文档**：详见 `docs/current-state.md` F-1~F-7 与 `docs/adrs/ADR-0002-前端mock先行与轻量设计体系.md`。

## 选定切片

- 需求与可观察结果：**① 项目仓库就绪**——初始化 Git、加入 `.gitignore` 忽略规则、一次性初始提交，并按用户授权推送至私有 GitHub 仓库（不开源）；**② 后端最小闭环**——在现有后端骨架内实现反馈接收与持久化 API（POST /api/v1/feedback、GET /api/v1/feedback 分页/筛选），为前端 `VITE_USE_MOCK=false` 切换提供真实契约。
- 当前行为 → 目标行为：前端可独立演示（mock 驱动，不依赖后端）；目标为反馈数据可经真实 API 写入与读取，前后端契约与 mock 适配层一致，Docker compose 中 frontend+backend 同时可访问。
- 拥有边界、必要组件与排除项：`backend/app/api/`（反馈 CRUD + 内存/文件持久化）、`backend/app/schemas/`（Pydantic 契约）、`deploy/docker-compose.yml`（backend 服务编排）；排除真实 LLM 洞察、真实渠道接入、登录鉴权与数据库选型（先用轻量持久化，数据库迁移留待后续切片）。
- 前置条件与交接契约：`frontend/src/types` 与后端 schema 字段对齐（feedback item、status 枚举等）；API 适配层保持 `VITE_USE_MOCK` 切换不受影响；`docs/frontend-development-plan.md` §3.3 验收口径沿用。
- 为什么这是优先级与合适阶段大小：仓库就绪是后续一切提交与协作的前提；后端最小闭环是「真实数据切换」的必要前置，边界可独立验证（curl + 浏览器双通道）。

## 验收与证据

- 正常路径：`git status` 干净、`.gitignore` 生效（排除 dist/node_modules/.env 等）→ 推送私有仓库成功且远程可见；后端启动后 `curl -X POST /api/v1/feedback` 写入 1 条 → `GET /api/v1/feedback?status=new` 可读到；前端 `VITE_USE_MOCK=false` 且 backend 可用时，反馈页列表渲染真实返回数据。
- 相关失败或取消：凭证缺失/网络不可达时停止并报告，不伪造推送成功；后端未启动时前端仍可回退 mock 演示，不白屏。
- 重复、重试、重启、权限或恢复检查：后端重启后已写入数据仍在（轻量持久化）或按设计清空（内存态需明示）；推送前检查远程仓库存在性与权限。
- 非专业人士可检查的证据：GitHub 私有仓库页面、curl 请求/响应样例、前端真实数据渲染截图。
- 证据等级与限制：curl/浏览器真实可见；持久化方案若为内存态则在文档明示限制。

### 生成内容评估

本切片无 LLM 生成内容；若后续 LangGraph 洞察接入产生生成文本，再启用模型评审流程。

## 依赖与决策

- 需要的用户决策：GitHub 仓库名与可见性已按用户指示（私有、不开源）执行；若远程仓库不存在，报告并请用户确认创建方式（gh 创建 / 用户手动创建后提供 URL）。
- 技术调研或 ADR 前置：无新增前置；后端持久化选型（内存 vs 文件 vs SQLite）若需要可新增 ADR-0003 记录。
- 安全、数据或迁移风险：`.gitignore` 必须覆盖 `.env`、密钥、dist、依赖目录与本地截图；mock 数据不包含真实客户信息；推送前复查无敏感文件入仓。

## 完成与回退

- 交付物与可观察结果：Git 仓库已初始化并推送私有仓库（远程可访问）；后端最小闭环 API 可 curl 验证；前端真实数据切换说明更新到 `docs/current-state.md`。
- 判定切片完成的准则：Git 推送成功且 `git log` 可见初始提交；curl POST/GET 均返回 200 且数据一致；前端真实数据渲染验收通过。
- 需替换或刷新的当前快照与回退界限：完成时更新 `docs/current-state.md`；回退界限为还原后端 API 新增模块与 Git 提交（不删除已完成前端切片）。
- 验证后需检查清理的一次性测试/运行产物：本地临时 curl 数据、dist 构建产物（按 `.gitignore` 策略）、docker 运行日志。

## 后续候选（仅候选，非承诺）

- 真实数据端到端切换：反馈/洞察接口全量接通，前端删除/标签化 mock 分支。
- 洞察与 LangGraph 接入：以真实工作流产物替换 mock 主题/优先级数据。
- 政务深化切片：FS-6 与后端政务功能组（诉求分级/督办/政策告知/审计）对接。
- 反馈分类模型与渠道接入：工单/门户/评价等真实渠道数据入库。