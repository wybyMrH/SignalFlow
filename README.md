# SignalFlow - 客户反馈决策工具

面向客户侧的反馈收集、洞见分析与处置决策平台（支持政务场景私有化部署）。
本仓库为**工程骨架**：技术栈已引入、前后端分层与部署/CI 已就位，业务功能按后续切片迭代实现。

- 产品设计：见前序交付的《SignalFlow-客户反馈决策工具产品规划设计文档》；
  仓库内 `docs/project-spec.md` 为活的规格协议，`docs/adrs/` 为架构决策记录。
- 开发规则：`AGENTS.md`（由 project-compass 安装，人机共同遵守）。

## 总体架构

```text
┌─────────────────────────────────────────────────────────┐
│  frontend/  Vue3 + TS + Vite + Pinia + Vue Router      │
│  （页面 / 状态 / API 客户端分层）                          │
└───────────────┬─────────────────────────────────────────┘
                │  /api（开发期 vite 代理；生产由 Nginx 反代）
┌───────────────▼─────────────────────────────────────────┐
│  backend/  FastAPI + SQLAlchemy2 + Alembic              │
│  api → services → (repositories | workflows(LangGraph)) │
│  llm(LiteLLM 网关) · integrations(渠道适配器)             │
└───────┬──────────────────────────────┬──────────────────┘
        │                              │
┌───────▼───────┐              ┌───────▼───────┐
│ PostgreSQL    │              │ Redis        │
│ + pgvector    │              │ (缓存/异步)    │
└───────────────┘              └───────────────┘
```

## 技术选型

| 层 | 技术 | 说明 |
| --- | --- | --- |
| 后端 | Python 3.11+ / FastAPI / Pydantic v2 | API 与数据校验，分层分包（api/services/repositories/workflows） |
| 存储 | PostgreSQL / SQLAlchemy 2 / Alembic / pgvector | 关系数据 + 向量检索，迁移管理 |
| AI 编排 | LangGraph | 反馈分析工作流：去重 → 聚类 → 洞察 → 评估 → 草稿 |
| LLM 网关 | LiteLLM | 统一多 provider，支持降级与开关（`WORKFLOW_LLM_ENABLED`） |
| 缓存 | Redis | 预留缓存与异步队列 |
| 前端 | Vue 3 + TypeScript + Vite + Pinia + Vue Router + Axios | 与后端目录完全分离（默认候选，见 ADR-0001） |
| 部署 | Docker Compose | postgres(pgvector) + redis + backend + frontend 一键编排 |
| CI/CD | GitHub Actions | push/PR 触发 lint+测试+build，main 构建并推送 ghcr.io 镜像 |

选型论证与备选方案见 `docs/adrs/ADR-0001-总体技术选型.md`。

## 目录结构

```text
SignalFlow/
├── backend/                 # Python 后端
│   ├── app/
│   │   ├── api/v1/          # HTTP 接口层
│   │   ├── core/            # 配置 / 日志 / 数据库会话
│   │   ├── models/          # ORM 模型
│   │   ├── schemas/         # Pydantic 契约
│   │   ├── repositories/    # 数据访问层
│   │   ├── services/        # 业务服务层
│   │   ├── workflows/       # LangGraph 工作流（state/graph 骨架）
│   │   ├── llm/             # LiteLLM 网关封装
│   │   └── integrations/    # 渠道适配器扩展点
│   ├── alembic/             # 数据库迁移
│   └── tests/               # pytest
├── frontend/                # Vue3 前端（api/components/pages/router/stores/types/utils）
├── deploy/                  # Docker Compose 编排与环境变量样例
├── .github/workflows/       # GitHub Actions CI/CD
├── docs/                    # project-compass 文档（spec/adr/计划/台账）
└── AGENTS.md                # 项目开发规则书
```

## 快速开始

```bash
# 后端（本地开发）
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env                                # 填写 DATABASE_URL 等
alembic upgrade head                                # 需先启动 PostgreSQL
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端（本地开发）
cd frontend
npm install
npm run dev                                         # http://localhost:5173，/api 已代理到 8000

# 一键部署（推荐验证用）
cd deploy
cp .env.example .env
docker compose up -d --build                        # 前端 8080 / 后端 8000
```

## CI/CD

- `ci.yml`：push/PR 触发——后端 ruff + mypy + pytest、前端类型检查 + 构建、
  main 分支构建并推送 `ghcr.io/<owner>/signalflow-{backend,frontend}` 镜像。
- `cd.yml`：CI 成功后触发的部署占位（政务内网/云主机接入点已预留）。

## 文档

- 产品与需求：前序交付的设计文档（17 模块五组、政务适配 A-F 组）
- 技术选型：`docs/adrs/ADR-0001-总体技术选型.md`
- 当前状态 / 下一阶段：`docs/current-state.md`、`docs/next-stage-plan.md`