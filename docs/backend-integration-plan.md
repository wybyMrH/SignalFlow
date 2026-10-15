# SignalFlow 后端真实接入部署清单

> **目标**：在不破坏前端 mock 全流程演示的前提下，逐步将后端从「骨架+局部 mock」推进到「可独立运行、可被前端无缝切换的真实服务」。
> **核心原则**：高内聚低耦合、公共组件抽象复用、mock 与真实实现共存、先框架后填充、先孤立后关联。

---

## 1. 背景与当前状态

### 1.1 前端现状（v0.1.0）

- **12 个业务页面**全部由前端 mock 数据驱动，可独立演示完整闭环（反馈→洞察→路线→自动化→工作流→商务→访谈→政务→Agent→资源）。
- **API 适配层**（`frontend/src/api/`）已与 mock 契约对齐；切换真实后端时仅需改环境变量 `VITE_USE_MOCK=false`，页面与 store 零改动。
- **Store 守卫模式**已建立：`fetch(force = false)` 防止页面挂载覆盖用户操作，真实后端阶段同样适用。

### 1.2 后端现状（v0.1.0）

| 模块 | 当前深度 | 说明 |
|------|---------|------|
| `app/core/` | 配置/日志/数据库会话骨架 | `config.py` 有 Pydantic Settings，`database.py` 有 `SessionLocal` |
| `app/models/` | `feedback.py` 完整 ORM | 其他 domain 为占位或缺失 |
| `app/schemas/` | `feedback.py` / `ai.py` 部分契约 | AI 契约与前端 mock 对齐，但缺少 gov/interviews/agents/resources/workflows 等 |
| `app/repositories/` | `feedback.py` 基础 CRUD | 其他 domain 缺失 |
| `app/services/` | `feedback.py` 业务层 | 其他 domain 缺失 |
| `app/api/v1/` | `feedback.py` / `ai.py` / `health.py` 等 | `ai.py` 为 mock 实现；`gov` 路由未注册（404） |
| `app/workflows/` | LangGraph 骨架 | 有 state/graph 目录，节点实现为空 |
| `app/llm/` | LiteLLM 网关骨架 | 封装层未填充 |
| `app/integrations/` | 空目录 | 渠道适配器扩展点预留 |
| `alembic/` | 初始化迁移脚本 | 仅有 `env.py` 与版本目录，无实际 migration |

### 1.3 关键差距

1. **Domain 不完整**：gov、interviews、agents、resources、workflows、settings、dashboard、insights、roadmap、automation、business 等 domain 在后端几乎空白。
2. **AI 工作流未落地**：LangGraph 节点为空，LiteLLM 网关未接入真实模型。
3. **API 契约不对齐**：部分前端 mock 接口在后端无对应实现（如 `/gov/overview` 返回 404）。
4. **缺少公共服务**：统一错误处理、分页封装、审计中间件、权限 RBAC 骨架。
5. **渠道适配器未实现**：外部系统（工单/邮件/IM/政务热线）接入为空。

---

## 2. 总体架构蓝图

```text
┌─────────────────────────────────────────────────────────────────────────┐
│  frontend/  (Vue3 + TS + Vite + Pinia)                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │  api/       │  │  stores/    │  │  mocks/     │  ← mock 与真实共存   │
│  │  (axios)    │  │  (pinia)    │  │  (内存态)   │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
│              ↓ VITE_USE_MOCK=false                                     │
└─────────────────────────────────────────────────────────────────────────┘
                              │ /api/v1
┌─────────────────────────────▼───────────────────────────────────────────┐
│  backend/  (FastAPI + SQLAlchemy2 + Alembic)                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  api/v1/           ← HTTP 接口层（契约对齐前端 mock）            │    │
│  │  ├── routers/      ← 按 domain 分包（feedback/insights/...）  │    │
│  │  └── deps.py       ← 依赖注入（DB Session / 当前用户 / 权限）  │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  services/         ← 业务服务层（纯 Python，无 LLM 泄漏）        │    │
│  │  ├── feedback/     ← 按聚合根分包                              │    │
│  │  ├── insights/                                                  │    │
│  │  └── ...                                                        │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  repositories/     ← 数据访问层（SQLAlchemy CRUD + 查询）      │    │
│  │  ├── feedback/                                                  │    │
│  │  └── ...                                                        │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  workflows/        ← LangGraph 有状态编排                     │    │
│  │  ├── state.py        ← 共享状态定义                             │    │
│  │  ├── graph.py        ← 图定义（去重→聚类→洞察→评估→草稿）     │    │
│  │  └── nodes/          ← 节点实现（可独立测试）                   │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  llm/              ← LiteLLM 网关封装                        │    │
│  │  ├── gateway.py      ← 统一调用/限流/降级/多 provider           │    │
│  │  ├── prompts/        ← 提示词模板（按场景分包）                 │    │
│  │  └── models.py       ← 输出 schema 与解析                       │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  integrations/       ← 渠道适配器（外部系统接入）              │    │
│  │  ├── base.py           ← 抽象基类（入站/出站协议）               │    │
│  │  ├── ticket_system/    ← 工单系统适配器                        │    │
│  │  ├── email/            ← 邮件适配器                            │    │
│  │  ├── im/               ← IM（企业微信/钉钉/飞书）              │    │
│  │  └── gov_hotline/      ← 政务热线适配器                       │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  core/               ← 基础设施与公共服务                      │    │
│  │  ├── config.py         ← Pydantic Settings（环境变量统一管理）  │    │
│  │  ├── database.py       ← 连接池/会话管理/事务                   │    │
│  │  ├── security.py       ← JWT / RBAC / 审计中间件                │    │
│  │  ├── exceptions.py     ← 业务异常体系（统一错误码）             │    │
│  │  ├── logging.py        ← 结构化日志（JSON / 链路追踪 ID）       │    │
│  │  └── pagination.py     ← 分页封装（cursor / offset）           │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  models/             ← ORM 模型（SQLAlchemy 2 + pgvector）       │    │
│  │  └── 按 domain 分包，与 repositories 一一对应                  │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  schemas/            ← Pydantic 契约（请求/响应/领域事件）       │    │
│  │  └── 按 domain 分包，与 api/v1 一一对应                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│  ┌───────────────────────────┴──────────────────────────────────────┐  │
│  │  PostgreSQL  +  pgvector  │  Redis（缓存/异步队列/限流计数器）       │  │
│  └───────────────────────────┴──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 阶段规划（从孤立到关联）

### 核心策略

- **阶段 0 先行**：基础设施与公共抽象层必须先于所有业务 domain 完成，否则每个 domain 都会重复造轮子。
- **孤立组件优先**：每个 domain 的 `model → schema → repository → service → api` 五层可以独立开发、独立测试，不依赖其他 domain 的真实实现。
- **mock 共存**：真实后端接口与前端 mock 并行存在，通过 `VITE_USE_MOCK` 切换；后端未就绪的接口前端继续用 mock，已就绪的接口逐步切真实。
- **契约驱动**：每个阶段先写 `schemas/`（Pydantic 契约）和 `api/` 接口签名，再填实现；保证前端可以提前对接。

---

### 阶段 0：基础设施与公共抽象层（所有后续阶段的依赖）

| 模块 | 任务 | 输出 | 验收标准 | 风险与回退 |
|------|------|------|---------|-----------|
| **core.config** | 完善 `Settings`：数据库 URL、Redis URL、JWT 密钥、LLM provider 配置、工作流开关、CORS 白名单 | `app/core/config.py` | 所有配置项有默认值/环境变量映射，启动时校验不通过则立即退出 | 配置缺失导致服务启动失败 |
| **core.database** | 连接池管理、异步会话（`AsyncSession`）、事务装饰器、读写分离预留 | `app/core/database.py` | `get_db()` 依赖注入可用，Alembic 迁移成功执行 | SQLAlchemy 2 async 模式与现有 sync 代码冲突 |
| **core.exceptions** | 定义业务异常体系：`BusinessException` / `NotFoundException` / `ValidationException` / `AIException`；统一错误码枚举 | `app/core/exceptions.py` | 所有业务层抛出的异常被全局异常处理器捕获并返回结构化 JSON | 异常层级设计过深导致调用方困惑 |
| **core.pagination** | 封装 `OffsetPagination` / `CursorPagination`；统一分页响应 schema（`items`/`total`/`next_cursor`） | `app/core/pagination.py` | 所有列表接口使用统一分页参数（`page`/`size` 或 `cursor`/`limit`） | 前端当前 mock 使用不同分页风格，需对齐契约 |
| **core.logging** | 结构化日志（JSON 格式）、请求链路 ID（`X-Request-ID`）、日志脱敏（密钥/手机号/身份证号） | `app/core/logging.py` + middleware | 每条日志带 trace_id，慢请求（>1s）自动 WARN | 日志量过大影响性能，需采样策略 |
| **core.security** | JWT 签发与校验、RBAC 角色定义（admin/operator/viewer）、审计中间件（记录操作人/时间/IP/变更前后） | `app/core/security.py` + deps | mock 阶段可先关闭鉴权（`SKIP_AUTH=true`），框架预留即可 | JWT 密钥轮转策略待设计 |
| **Alembic 迁移** | 初始化首版 migration（create_all），建立 migration 命名规范（`YYYYMMDD_HHMMSS_description.py`） | `alembic/versions/` | `alembic upgrade head` 成功创建全部表 | 模型变更频繁导致 migration 冲突 |
| **Docker 调优** | 后端 Dockerfile 多阶段构建、healthcheck 脚本、非 root 用户运行、依赖缓存层 | `deploy/Dockerfile-backend` | 镜像体积 < 300MB，启动时间 < 5s | 多阶段构建复杂度增加 CI 时间 |

**验收总关**：阶段 0 完成后，后端服务应能独立启动并返回 `{"status":"ok"}`，数据库连接正常， Alembic 迁移可执行，日志带 trace_id。

---

### 阶段 1：孤立数据组件（Domain 实体层，可独立测试）

本阶段的目标是把所有前端 mock 中已定义的「数据形状」翻译为后端的 ORM Model + Pydantic Schema + Repository，不依赖任何业务逻辑或 AI 能力。

**Domain 优先级**（按前端调用频率与数据稳定性排序）：

```
高稳定性、高频调用优先：
  feedback（已有基础，补全字段）
  → settings（系统配置，简单 KV）
  → dashboard（统计聚合，只读）
  → insights（主题/趋势，依赖 feedback 但可 mock 数据源）
中频、有外部关联：
  → interviews（访谈记录，关联 feedback / business_leads）
  → agents（Agent 配置，关联 workflows）
  → workflows（工作流模板，关联 agents）
  → resources（资源监控，独立数据源）
低频、政务特化：
  → gov（诉求分级/督办/舆情，独立 domain）
  → business（线索/需求/市场动向，依赖 interviews）
  → roadmap（产品任务，依赖 insights/feedback）
  → automation（规则配置，依赖 feedback）
```

**每个 Domain 的标准五层开发顺序**（高内聚低耦合）：

```
1. schemas/        ← 先定义契约（请求/响应/领域事件），与前端 mock 对齐
2. models/         ← ORM 模型（表结构/索引/外键/向量字段 pgvector）
3. repositories/   ← 基础 CRUD + 领域查询（按业务场景封装，不复用通用 CRUD）
4. （单元测试）     ← 使用 pytest + testcontainers（PostgreSQL）独立测试 repository
5. api/ 接口签名    ← FastAPI router 只写路径/参数/响应模型，handler 先 pass/mock
```

> **设计约束**：
> - `schemas/` 中的 Pydantic 模型必须与前端 `types/index.ts` 一一对应，字段名、类型、可选性保持一致。
> - `models/` 中的 SQLAlchemy 模型使用 `Mapped[]` 注解（SA2 风格），所有表必须有 `created_at`/`updated_at`。
> - `repositories/` 不直接暴露 SQLAlchemy Session 给上层，所有查询封装为领域方法（如 `find_by_status`、`get_priority_distribution`）。
> - 每个 domain 的 repository 独立测试，使用内存 SQLite 或 testcontainers PostgreSQL。

**阶段 1 验收标准**：
- 全部 12 个 domain 的 `schemas/` 和 `models/` 已完成，Alembic migration 可创建全部表。
- `feedback`、`settings`、`dashboard`、`insights` 的 `repositories/` 有完整单元测试并通过。
- 其余 domain 的 `repositories/` 至少完成基础 CRUD。

---

### 阶段 2：业务服务层（Services，依赖 Repository，可独立单元测试）

服务层是**业务规则的容器**，负责编排 repository、计算业务值、触发领域事件。**服务层不得直接调用 LLM**，所有 AI 需求通过 `workflows/` 或 `llm/` 网关间接调用。

| Domain | Service 核心职责 | 输入 | 输出 | 依赖 |
|--------|-----------------|------|------|------|
| **feedback** | 反馈生命周期（创建→去重标记→分类→分配→回复→关闭）、批量操作 | 原始反馈事件 | 反馈详情 + 状态流转 | repository + settings |
| **insights** | 主题聚类结果聚合、痛点评分计算、趋势预警阈值判断 | 聚类结果/时间窗口 | 洞察看板数据 | repository + feedback_repo |
| **dashboard** | KPI 聚合查询（今日新增/待办/逾期/办结率）、数据缓存 | 时间范围 | 统计卡片数据 | repository + Redis 缓存 |
| **interviews** | 访谈记录管理、AI 提炼结果存储、线索生成触发 | 访谈表单/录音元数据 | 访谈详情 + 线索事件 | repository + business_service |
| **agents** | Agent 启停、运行统计、工具权限校验 | Agent 配置变更 | Agent 状态 + 运行日志 | repository + workflows_service |
| **workflows** | 模板管理、节点配置校验、启用状态切换 | 模板 JSON | 工作流详情 + 校验报告 | repository + agents_service |
| **resources** | 健康检查探针、告警规则评估、日志查询 | 探针数据/阈值配置 | 健康状态 + 告警列表 | repository（独立数据源） |
| **gov** | 诉求分级分类、督办规则引擎、舆情预警计算 | 原始诉求/政策文件 | 分级结果 + 督办项 + 预警 | repository + insights_service |
| **business** | 线索生命周期（识别→确认→跟进→转化/放弃）、匹配评分 | 线索事件/访谈关联 | 线索详情 + 匹配报告 | repository + interviews_repo |
| **roadmap** | 产品任务规划、优先级重算、里程碑管理 | 洞察项/任务表单 | 路线图数据 + 任务列表 | repository + insights_repo |
| **automation** | 规则引擎（分类规则/去重策略/优先级调整/自动审批） | 规则配置/反馈事件 | 规则匹配结果 + 操作指令 | repository + feedback_repo |
| **settings** | 系统配置读写、配置变更审计 | KV 配置 | 配置项 + 变更历史 | repository |

**阶段 2 验收标准**：
- `feedback`、`dashboard`、`settings` 的 services 有完整单元测试并通过。
- 所有 service 的公开方法有类型注解和 docstring。
- service 层不直接 import `langgraph` 或 `litellm`，AI 调用统一通过 `llm/gateway.py` 的抽象接口。

---

### 阶段 3：LLM 网关与 AI 工作流（可独立集成测试）

这是**技术风险最高**的阶段，也是前后端差距最大的部分。设计原则是：**LLM 细节不泄漏到 service 层**。

#### 3.1 LiteLLM 网关（`app/llm/`）

| 组件 | 职责 | 抽象接口 | 可复用性 |
|------|------|---------|---------|
| `gateway.py` | 统一调用入口：参数标准化、超时控制、重试（指数退避）、限流（令牌桶） | `call(model, messages, temperature, max_tokens) → LLMResponse` | 全站唯一 LLM 调用点 |
| `registry.py` | 模型注册表：支持 OpenAI / Azure / 文心一言 / 本地部署（Ollama/vLLM） | `register_provider(name, config) / get_model(name)` | 新增模型只需改配置 |
| `fallback.py` | 降级策略：主模型失败 → 次模型 → 本地模型 → 返回错误 | `try_primary → fallback_chain` | 配置驱动，无需改业务代码 |
| `prompts/` | 提示词模板按场景分包：去重/聚类/痛点/评估/回复草稿/政务摘要 | `load_template(scene, variables) → formatted_prompt` | 新增场景只需加模板文件 |
| `models.py` | LLM 输出 schema 定义与解析（JSON mode / function calling） | `parse_json_output(raw) → StructuredOutput` | 统一解析错误处理 |
| `cost_tracker.py` | Token 计数与费用估算，按工作流/按请求维度 | `track(request_id, model, tokens)` | 成本监控与预算告警 |

**验收标准**：
- 网关支持至少 2 个 provider（如 OpenAI + 本地 Ollama）。
- 主模型失败时 3s 内完成降级，降级失败返回可理解的错误信息。
- 提示词模板支持热加载（开发期）或打包加载（生产期）。

#### 3.2 LangGraph 工作流（`app/workflows/`）

工作流是**有状态的 AI 编排**，每个工作流对应前端「工作流配置」中的一个模板。

```text
通用反馈分析工作流（Feedback Analysis Graph）：

[Start] ──→ [去重节点 DedupNode] ──→ [聚类节点 ClusterNode]
                │                           │
                ▼                           ▼
           相似度>阈值?              主题数/痛点识别
                │                           │
                └──→ 合并反馈 ───────────────┘
                              │
                              ▼
                    [评估节点 EvalNode]
                    (影响面 × 客户价值 × 置信度)
                              │
                              ▼
                    [优先级节点 PriorityNode]
                    (RICE 思想评分卡)
                              │
                              ▼
                    [草稿节点 DraftNode]
                    (回复草稿/产品任务草稿)
                              │
                              ▼
                           [End]
```

| 节点 | 输入 | 输出 | LLM 调用点 | 状态持久化 |
|------|------|------|-----------|-----------|
| `DedupNode` | 原始反馈列表 | 去重后的合并组 + 相似度矩阵 | Embedding（本地模型或 API） | 去重结果写入 `feedback_dedup_groups` |
| `ClusterNode` | 去重后反馈 | 主题列表 + 痛点标签 | 聚类提示词（JSON mode） | 主题/痛点写入 `insights_topics` |
| `EvalNode` | 主题 + 客户信息 | 影响面数值 + 客户价值评分 | 评估提示词 | 评估结果写入 `feedback_evaluations` |
| `PriorityNode` | 评估结果 | 优先级分数 + 排序列表 | 评分规则（可不用 LLM，纯算法） | 优先级写入 `feedback_priorities` |
| `DraftNode` | 高优先级项 | 回复草稿 / 产品任务草稿 | 草稿生成提示词 | 草稿写入 `feedback_drafts` / `roadmap_tasks` |

**验收标准**：
- 每个节点可独立测试（给定输入断言输出结构正确）。
- 完整工作流端到端测试：10 条模拟反馈 → 去重 → 聚类 → 评估 → 优先级 → 草稿，总耗时 < 30s（本地模型）或 < 10s（API 模型）。
- 工作流状态可中断恢复（LangGraph Checkpoint 持久化到 PostgreSQL）。

---

### 阶段 4：API 层与契约对齐（FastAPI Routers）

本阶段的目标是让后端接口与前端 mock 的**数据结构完全一致**，实现「切换环境变量即可工作」。

**开发顺序**（按前端页面依赖顺序）：

```
1. health.py          ← 已有，保持
2. feedback.py        ← 已有基础，补全字段/分页/筛选
3. settings.py        ← 新增，系统配置读写
4. dashboard.py       ← 新增，KPI 聚合（可先用 SQL 聚合，后期加缓存）
5. insights.py        ← 新增，主题/趋势/预警（底层依赖工作流结果）
6. interviews.py      ← 新增，访谈 CRUD + AI 提炼触发接口
7. agents.py          ← 新增，Agent CRUD + 启停 + 统计
8. workflows.py       ← 新增，模板 CRUD + 校验 + 启用
9. resources.py       ← 新增，健康探针 + 告警查询 + 日志查询
10. gov.py           ← 新增，诉求分级 + 督办 + 舆情（独立 domain）
11. business.py       ← 新增，线索 CRUD + 匹配评分 + 市场动向
12. roadmap.py        ← 新增，任务 CRUD + 里程碑 + 审批回传
13. automation.py     ← 新增，规则 CRUD + 测试执行 + 日志
14. ai.py            ← 重构，从 mock 实现改为真实 LLM 调用（gateway + workflows）
```

**契约对齐检查清单**：

每完成一个 router，执行以下验证：
- [ ] 请求/响应 schema 与前端 `types/index.ts` 同名字段类型一致。
- [ ] 列表接口支持统一分页参数（`page`/`size` 或 `cursor`/`limit`）。
- [ ] 错误响应使用统一格式：`{ "code": "ERROR_CODE", "message": "...", "detail": {} }`。
- [ ] 前端 `api/` 模块在不改代码的情况下，将 `VITE_USE_MOCK=false` 能正常请求该接口。
- [ ] 接口有 OpenAPI 文档注释（FastAPI 自动生成）。

**阶段 4 验收标准**：
- 全部 14 个 router 的接口签名已完成，handler 至少返回 mock 数据或真实数据。
- 前端 `npm run type-check` 在 `VITE_USE_MOCK=false` 下无类型错误（需保证后端返回结构与 TS 类型对齐）。
- 使用 Postman / curl 逐个接口调用，返回 200 且数据结构正确。

---

### 阶段 5：渠道适配器与集成（Integrations）

渠道适配器是**外部系统接入**的边界层，负责将外部异构数据转换为内部统一的「反馈事件」。

```text
┌────────────────────────────────────────────────────────────┐
│                    外部系统（异构协议）                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐  │
│  │ 工单系统 │ │ 邮件   │ │ 企业微信 │ │ 政务 12345 热线 │  │
│  │ (REST)  │ │ (IMAP) │ │ (Webhook)│ │ (Kafka/文件)    │  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────────┬────────┘  │
│       │           │           │                │           │
│       ▼           ▼           ▼                ▼           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           integrations/ 渠道适配器层                 │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ base.py     │  │ 协议解析     │  │ 数据规范化   │  │  │
│  │  │ (抽象基类)   │  │ (原始→中间)  │  │ (中间→事件)  │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  │              │                                       │  │
│  │              ▼                                       │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │ 统一反馈事件 (FeedbackEvent)                  │   │  │
│  │  │ 字段: source / channel / raw_content /      │   │  │
│  │  │       customer_id / timestamp / metadata     │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                │
│                           ▼                                │
│                    ┌─────────────┐                         │
│                    │ 消息队列    │ ← 可选（Redis Stream）   │
│                    │ / 直接入库  │                         │
│                    └─────────────┘                         │
└────────────────────────────────────────────────────────────┘
```

| 适配器 | 协议 | 数据拉取方式 | 状态同步方向 |
|--------|------|------------|-------------|
| `ticket_system/` | REST API / Webhook | 轮询 + 回调 | 双向（读取工单 + 回写处理状态） |
| `email/` | IMAP / SMTP | 轮询收件箱 | 单向（读取）+ 回复发送 |
| `im/` | Webhook / Bot API | 被动接收 | 单向（读取）+ 主动推送回复 |
| `app_store/` | 爬虫 / 官方 API | 定时任务 | 单向（读取） |
| `gov_hotline/` | Kafka / 文件交换 / 数据库视图 | 实时流 / 定时同步 | 单向（读取）+ 结果回写 |

**设计约束**：
- 所有适配器继承 `BaseAdapter`，必须实现 `parse(raw) → FeedbackEvent` 和 `normalize(event) → StandardFeedback`。
- 适配器层不直接写数据库，只生产标准化事件；事件由统一的「入站处理器」消费并入库。
- 每个适配器独立测试：用录制的外部系统响应（vcr.py 或本地 fixture）测试解析逻辑。

**阶段 5 验收标准**：
- 至少 1 个适配器（如 `ticket_system/`）完成端到端测试（从外部 API mock → 解析 → 标准化 → 入库）。
- 适配器失败不影响主服务（隔离运行，错误记录在独立日志通道）。

---

### 阶段 6：前后端联调与端到端验收

本阶段的目标是从「后端接口可用」推进到「前后端协同工作、可演示真实数据闭环」。

**联调顺序**（按数据流向，从输入到输出）：

```
联调批次 1（数据入库链路）：
  渠道适配器 → API → Service → Repository → DB
  验证：外部数据能正确入库，前端可查询展示。

联调批次 2（AI 分析链路）：
  DB → Repository → Service → Workflow → LLM Gateway → 结果回写 DB
  验证：AI 工作流能处理真实数据并产生结构化结果。

联调批次 3（决策行动链路）：
  DB → Service → API → 前端展示 → 人工操作 → API → Service → 状态变更 → 回传适配器
  验证：人工审批/配置/回复等操作能正确流转并回传外部系统。

联调批次 4（运营驾驶舱）：
  全部 domain 真实数据聚合 → Dashboard / Insights / Gov / Business / Resources
  验证：总览页所有 KPI 卡片展示真实数据，AI 助手能基于真实数据回答。
```

**验收里程碑**：

| 里程碑 | 标志 | 验收动作 |
|--------|------|---------|
| M1 | 全部接口 200 + 数据结构对齐 | 前端 `VITE_USE_MOCK=false`，逐页浏览无 console 报错 |
| M2 | 反馈能入库 + 可展示 | 通过适配器导入 1 条真实外部数据，前端反馈列表可见 |
| M3 | AI 工作流跑通 + 结果可展示 | 提交 10 条反馈 → 触发工作流 → 前端洞察页展示聚类结果 |
| M4 | 人工操作闭环 | 前端审批一条回复 → 后端状态变更 → 适配器回传 → 外部系统确认收到 |
| M5 | 运营驾驶舱全真实 | 总览页所有卡片数据来自后端真实聚合，AI 助手基于真实数据交互 |

---

## 4. 组件依赖关系与联调时序

```mermaid
graph TD
    subgraph "阶段 0 基础设施"
        A0[core.config] --> A1[core.database]
        A0 --> A2[core.exceptions]
        A0 --> A3[core.logging]
        A0 --> A4[core.pagination]
        A0 --> A5[core.security]
        A1 --> A6[Alembic 迁移]
    end

    subgraph "阶段 1 孤立数据组件"
        A1 --> B1[models + schemas + repositories]
        B1 --> B2[feedback]
        B1 --> B3[settings]
        B1 --> B4[dashboard]
        B1 --> B5[insights]
        B1 --> B6[interviews]
        B1 --> B7[agents]
        B1 --> B8[workflows]
        B1 --> B9[resources]
        B1 --> B10[gov]
        B1 --> B11[business]
        B1 --> B12[roadmap]
        B1 --> B13[automation]
    end

    subgraph "阶段 2 业务服务"
        B2 --> C2[feedback_service]
        B3 --> C3[settings_service]
        B4 --> C4[dashboard_service]
        B5 --> C5[insights_service]
        B6 --> C6[interviews_service]
        B7 --> C7[agents_service]
        B8 --> C8[workflows_service]
        B9 --> C9[resources_service]
        B10 --> C10[gov_service]
        B11 --> C11[business_service]
        B12 --> C12[roadmap_service]
        B13 --> C13[automation_service]
    end

    subgraph "阶段 3 AI 与编排"
        C5 --> D1[llm.gateway]
        C6 --> D1
        C10 --> D1
        D1 --> D2[LangGraph Workflows]
        D2 --> D3[workflow_nodes]
    end

    subgraph "阶段 4 API 层"
        C2 --> E1[api/feedback]
        C3 --> E2[api/settings]
        C4 --> E3[api/dashboard]
        C5 --> E4[api/insights]
        C6 --> E5[api/interviews]
        C7 --> E6[api/agents]
        C8 --> E7[api/workflows]
        C9 --> E8[api/resources]
        C10 --> E9[api/gov]
        C11 --> E10[api/business]
        C12 --> E11[api/roadmap]
        C13 --> E12[api/automation]
        D1 --> E13[api/ai]
        D2 --> E13
    end

    subgraph "阶段 5 集成"
        E1 --> F1[integrations/ticket]
        E1 --> F2[integrations/email]
        E1 --> F3[integrations/im]
        E1 --> F4[integrations/gov_hotline]
    end
```

**关键依赖规则**：
- **同阶段内可并行**：阶段 1 的 12 个 domain 可并行开发，互不阻塞。
- **跨阶段单向依赖**：阶段 N 只依赖阶段 N-1 的已完成组件，不可反向依赖。
- **AI 层晚于业务层**：LLM 网关和工作流依赖 service 层的输入数据，service 层必须先有真实数据格式。
- **API 层最后收口**：router 是 facade，等 service 稳定后再填充 handler，避免反复修改接口签名。
- **适配器独立于主链路**：适配器只依赖 `FeedbackEvent` 定义和 API 层（用于回传），不依赖具体 service 实现。

---

## 5. 公共抽象层设计（高复用、可扩展）

### 5.1 中间件栈（FastAPI `app.add_middleware` 顺序）

```python
# 请求进入顺序（从上到下，响应则相反）
app.add_middleware(CorrelationIdMiddleware)   # 生成/透传 X-Request-ID
app.add_middleware(LoggingMiddleware)         # 记录请求/响应体（脱敏）
app.add_middleware(TimingMiddleware)          # 记录耗时，>1s 标记慢请求
app.add_middleware(RateLimitMiddleware)       # 基于 Redis 的 IP + 用户限流
app.add_middleware(AuthenticationMiddleware)  # JWT 校验（可 SKIP_AUTH）
app.add_middleware(AuthorizationMiddleware)   # RBAC 校验（可 SKIP_AUTH）
app.add_middleware(AuditMiddleware)           # 记录操作人/时间/变更前后
```

### 5.2 统一错误处理

```python
# app/core/exceptions.py
class BusinessException(Exception):
    code: str          # 机器可读错误码，如 "FEEDBACK_NOT_FOUND"
    message: str       # 人类可读信息
    status_code: int   # HTTP 状态码映射
    detail: dict       # 附加上下文

# app/api/v1/deps.py 中的全局异常处理器
@app.exception_handler(BusinessException)
async def business_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
            "trace_id": request.state.trace_id,
        }
    )
```

### 5.3 分页封装

```python
# app/core/pagination.py
class PageParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

class PageResponse(Generic[T], BaseModel):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

# 使用方式：所有列表接口统一返回 PageResponse
```

### 5.4 可复用 Repository 基类（可选）

```python
# app/repositories/base.py
class BaseRepository(Generic[ModelType, CreateSchema, UpdateSchema]):
    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> ModelType | None: ...
    async def list(self, filters: dict, page: PageParams) -> PageResponse: ...
    async def create(self, obj: CreateSchema) -> ModelType: ...
    async def update(self, id: UUID, obj: UpdateSchema) -> ModelType: ...
    async def delete(self, id: UUID) -> None: ...
```

> **设计决策**：基类只封装最通用的 CRUD，复杂查询必须在各 domain 的 repository 中显式实现，避免「万能基类」导致的高耦合。

### 5.5 审计日志模型

```python
# app/models/audit.py
class AuditLog(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    actor_id: Mapped[str]          # 操作人
    action: Mapped[str]            # CREATE / UPDATE / DELETE / EXECUTE
    resource_type: Mapped[str]      # feedback / workflow / agent ...
    resource_id: Mapped[str]
    before: Mapped[dict | None]     # 变更前快照（JSONB）
    after: Mapped[dict | None]      # 变更后快照（JSONB）
    ip_address: Mapped[str | None]
    user_agent: Mapped[str | None]
    created_at: Mapped[datetime]
```

---

## 6. 风险矩阵与回退策略

| 风险 | 可能性 | 影响 | 缓解措施 | 回退方案 |
|------|--------|------|---------|---------|
| **LLM 调用超时/失败** | 高 | 高 | 网关实现降级链 + 本地模型兜底 + 断路器 | 返回 mock 结果 + 标记「AI 服务不可用」 |
| **Embedding 模型性能不足** | 中 | 中 | 支持本地轻量模型（sentence-transformers）+ 批量处理 | 降级为关键词匹配去重 |
| **数据库 migration 冲突** | 中 | 中 | 每个阶段单独 migration，禁止在已部署环境改旧 migration | 使用 `alembic downgrade` + 修复后重新升级 |
| **前端契约变更** | 低 | 中 | schemas 层先行定义，前端后端共同评审 | 在 api 层做字段兼容映射 |
| **PostgreSQL pgvector 性能瓶颈** | 低 | 高 | 向量维度控制（≤1536），索引策略（IVFFlat/HNSW），分表 | 向量检索降级为 BM25 全文检索 |
| **Redis 单点故障** | 低 | 中 | 集群模式预留，当前阶段单实例 + 哨兵 | 缓存失效 → 直接查库（性能降级） |
| **安全漏洞（JWT/注入）** | 中 | 高 | 使用 FastAPI 原生校验 + SQLAlchemy ORM（防注入）+ 参数化查询 | 启用 `SKIP_AUTH=false` 强制鉴权 |
| **Docker 镜像膨胀** | 中 | 低 | 多阶段构建，只安装生产依赖，使用 slim 基础镜像 | 接受稍大镜像，优先功能完整 |
| **开发期 schema 频繁变更** | 高 | 低 | 阶段 1 结束前冻结 schemas，后续只增不减 | 使用 Pydantic `Field(alias=...)` 兼容旧字段 |

---

## 7. Mock 与真实实现共存策略

### 7.1 前端侧

```typescript
// frontend/src/api/mock.ts
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'

// 所有 api 模块统一从 mock 适配层导出
export const feedbackApi = USE_MOCK ? mockFeedbackApi : realFeedbackApi
```

- **开发期**：`VITE_USE_MOCK=true`，前端独立开发不依赖后端。
- **联调期**：`VITE_USE_MOCK=false`，真实后端就绪的接口走真实，未就绪的接口前端临时用 mock（可细化到接口级别）。
- **生产期**：`VITE_USE_MOCK=false`，全部走真实后端。

### 7.2 后端侧

- **服务层 mock 回退**：LLM 网关实现「断路器」模式，当外部模型不可用时，返回预设的 mock 结构化结果（与前端期望的数据格式一致），保证服务不崩溃。
- **工作流 mock 模式**：`WORKFLOW_LLM_ENABLED=false` 时，工作流节点跳过 LLM 调用，返回基于规则的模拟结果（如随机聚类 / 固定评分），用于测试工作流拓扑本身。

---

## 8. 开发规范与接口契约

### 8.1 代码规范

- **Ruff**：格式化 + lint（`E`, `F`, `I`, `B`, `UP`），行宽 100。
- **MyPy**：严格模式（`strict = true`），所有函数/方法必须有类型注解。
- **pytest**：asyncio 模式，所有 repository / service / workflow 节点必须有单元测试。
- **测试覆盖率**：service 层 ≥ 80%，repository 层 ≥ 70%，api 层 ≥ 60%（通过集成测试覆盖）。

### 8.2 接口契约规范

- **URL 风格**：全部小写 + 连字符，如 `/api/v1/business-leads`。
- **HTTP 方法**：GET（查询）/ POST（创建）/ PUT（全量更新）/ PATCH（部分更新）/ DELETE（删除）。
- **状态码**：200（成功）/ 201（创建）/ 400（参数错误）/ 401（未认证）/ 403（无权限）/ 404（资源不存在）/ 409（冲突）/ 422（校验失败）/ 500（服务端错误）。
- **响应 envelope**：
  ```json
  {
    "code": "SUCCESS",
    "message": "操作成功",
    "data": { ... },
    "trace_id": "abc-123"
  }
  ```
  错误时：
  ```json
  {
    "code": "FEEDBACK_NOT_FOUND",
    "message": "反馈不存在",
    "detail": { "feedback_id": "xxx" },
    "trace_id": "abc-123"
  }
  ```

### 8.3 Git 分支策略

```
main        ← 稳定分支，只有阶段验收通过的代码可合并
  │
  ├── feature/backend-phase0-core    ← 阶段 0 开发
  ├── feature/backend-phase1-feedback-schema
  ├── feature/backend-phase1-settings-schema
  ├── ...
  ├── feature/backend-phase3-llm-gateway
  ├── feature/backend-phase4-gov-router
  └── feature/backend-phase5-ticket-adapter
```

- 每个阶段/每个 domain 独立分支，完成后 PR 到 `main`。
- PR 必须过 CI（ruff + mypy + pytest + type-check/build）。
- 禁止 force push `main`。

---

## 9. 里程碑时间线（估算）

> 以下估算基于 1 名全栈开发 + 1 名后端开发 + 0.5 名 AI 工程师的资源配置，每周 5 个工作日。

| 阶段 | 工期 | 前置依赖 | 关键交付物 | 验收动作 |
|------|------|---------|-----------|---------|
| 阶段 0 | 1 周 | 无 | `core/` 完整 + Alembic 首版迁移 + Docker 调优 | 后端独立启动，healthz 200，migration 成功 |
| 阶段 1 | 2 周 | 阶段 0 | 12 domain 的 `schemas/` + `models/` + `repositories/` | 全部表可创建，repository 单元测试通过 |
| 阶段 2 | 2 周 | 阶段 1 | 12 domain 的 `services/` | service 单元测试通过，覆盖率 ≥ 80% |
| 阶段 3 | 2 周 | 阶段 2 | LLM 网关 + 5 节点工作流 | 工作流端到端测试 < 30s，降级可用 |
| 阶段 4 | 2 周 | 阶段 2 + 阶段 3 | 14 个 router 完整实现 | 前端 `VITE_USE_MOCK=false` 逐页浏览无报错 |
| 阶段 5 | 1 周 | 阶段 4 | 1 个适配器端到端 | 外部数据 mock → 入库 → 前端展示 |
| 阶段 6 | 1 周 | 阶段 4 + 阶段 5 | 全链路联调报告 | M1~M5 里程碑全部通过 |
| **合计** | **11 周** | — | — | — |

---

## 10. 文档索引与更新策略

| 文档 | 更新时机 | 维护责任人 |
|------|---------|-----------|
| `backend-integration-plan.md` | 每阶段开始前评审，阶段中重大调整时更新 | 技术负责人 |
| `docs/current-state.md` | 每阶段验收后追加证据 | 开发负责人 |
| `docs/next-stage-plan.md` | 每阶段完成后更新下一阶段的细化任务 | 技术负责人 |
| `docs/adrs/` | 技术决策变更时追加新 ADR | 架构师 |
| `AGENTS.md` | 项目规则变更时更新 | 技术负责人 |

---

## 附录 A：前端 Mock ↔ 后端 API 契约映射表（关键接口）

| 前端页面 | 前端 Mock 函数 | 期望后端 Router | 当前状态 | 优先级 |
|---------|---------------|----------------|---------|--------|
| 总览 | `dashboardApi.getOverview()` | `GET /api/v1/dashboard/overview` | 前端 mock 已就绪，后端空白 | P0 |
| 反馈列表 | `feedbackApi.list()` | `GET /api/v1/feedbacks` | 后端已有基础，需补全分页/筛选 | P0 |
| 反馈详情 | `feedbackApi.getById(id)` | `GET /api/v1/feedbacks/{id}` | 后端已有基础 | P0 |
| 洞察主题 | `insightsApi.getTopics()` | `GET /api/v1/insights/topics` | 前端 mock 已就绪，后端空白 | P0 |
| 政务总览 | `govApi.getOverview()` | `GET /api/v1/gov/overview` | **404**，前后端均为空白 | P0 |
| 访谈列表 | `interviewsApi.list()` | `GET /api/v1/interviews` | 前端 mock 已就绪，后端空白 | P1 |
| 生成线索 | `interviewsApi.generateLead(id)` | `POST /api/v1/interviews/{id}/generate-lead` | 前端 mock 已就绪，后端空白 | P1 |
| Agent 列表 | `agentsApi.list()` | `GET /api/v1/agents` | 前端 mock 已就绪，后端空白 | P1 |
| 工作流列表 | `workflowsApi.list()` | `GET /api/v1/workflows` | 前端 mock 已就绪，后端空白 | P1 |
| 资源健康 | `resourcesApi.getHealth()` | `GET /api/v1/resources/health` | 前端 mock 已就绪，后端空白 | P2 |
| AI 规则 | `aiApi.getRules()` | `GET /api/v1/ai/rules` | 后端 mock 实现，需替换为真实 | P1 |
| AI 生成回复 | `aiApi.generateReply(id)` | `POST /api/v1/ai/generate-reply` | 后端 mock 实现，需替换为真实 | P1 |

---

## 附录 B：已确认的环境变量清单

```bash
# 数据库
DATABASE_URL=postgresql+psycopg://user:pass@postgres:5432/signalflow

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM 网关
LLM_PROVIDER=openai          # openai / azure / ollama / vllm
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4o
LLM_FALLBACK_MODEL=gpt-3.5-turbo
WORKFLOW_LLM_ENABLED=true    # false 时返回 mock 结果

# 工作流
WORKFLOW_MAX_CONCURRENT=5
WORKFLOW_TIMEOUT_SECONDS=30

# 安全
SKIP_AUTH=true               # 开发期关闭鉴权，生产期设为 false
CORS_ORIGINS=http://localhost:5173,http://localhost:8088

# 日志
LOG_LEVEL=INFO               # DEBUG / INFO / WARNING / ERROR
LOG_FORMAT=json              # json / text
```

---

*文档版本：v0.1.0*  
*最后更新：2026-10-15*  
*下一评审点：阶段 0 完成后（预计 1 周）*
