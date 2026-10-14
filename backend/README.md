# SignalFlow Backend

客户反馈决策工具 - 后端服务（Python / FastAPI）。

## 技术栈

- FastAPI + Pydantic v2（API 层与数据校验）
- SQLAlchemy 2 + Alembic（关系存储与迁移，PostgreSQL）
- pgvector（向量检索，预留）
- LangGraph（AI 分析工作流编排：去重 -> 聚类 -> 洞察 -> 评估 -> 草稿）
- LiteLLM（统一 LLM / Embedding 网关，支持多 provider 与降级）
- Redis（缓存，预留）
- Docker Compose / GitHub Actions（部署与 CI/CD，见仓库根目录）

## 目录结构

```text
backend/
├── alembic/                 # 数据库迁移（versions/ 为迁移脚本）
├── app/
│   ├── api/v1/              # HTTP 接口层（路由、请求/响应）
│   ├── core/                # 配置、日志、数据库会话
│   ├── integrations/        # 渠道适配器（Fider / 邮件 / 表单等扩展点）
│   ├── llm/                 # LiteLLM 网关封装
│   ├── models/              # SQLAlchemy ORM 模型（领域实体）
│   ├── repositories/        # 数据访问层（仓储）
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── services/            # 业务服务层（编排仓储与工作流）
│   └── workflows/           # LangGraph 工作流（state / graph 节点）
├── tests/                   # pytest 测试
├── pyproject.toml           # 依赖与工具配置（pip install -e ".[dev]"）
├── requirements.txt         # 锁定的运行依赖（容器构建用）
└── .env.example             # 环境变量样例（复制为 .env 后填写）
```

依赖方向：`api -> services -> (repositories | workflows) -> models`，
`llm` / `integrations` 作为基础设施被 services 与 workflows 引用。

## 本地运行

```bash
# 1. 安装依赖（建议使用虚拟环境）
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 2. 配置环境变量
cp .env.example .env             # 按需修改 DATABASE_URL / LLM_*

# 3. 数据库迁移（需先启动 PostgreSQL）
alembic upgrade head

# 4. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：`curl http://localhost:8000/healthz`

## 测试与检查

```bash
pytest                      # 运行测试
ruff check app tests        # 静态检查
mypy app                    # 类型检查
```

## 说明

- 骨架阶段 `WORKFLOW_LLM_ENABLED=False` 时，LangGraph 工作流走旁路，
  不发起真实 LLM 调用，便于离线开发与测试。
- 密钥（LLM_API_KEY 等）一律经环境变量注入，禁止提交到版本库。