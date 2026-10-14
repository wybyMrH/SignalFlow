# SignalFlow 部署（Docker Compose）

一键编排：`postgres(pgvector)` + `redis` + `backend(FastAPI)` + `frontend(Nginx)`。

## 快速开始

```bash
cd deploy
cp .env.example .env        # 按需修改数据库口令、端口与 LLM 密钥
docker compose up -d --build
```

- 前端：http://localhost:8080 （`/api` 由 Nginx 反代到后端）
- 后端健康检查：http://localhost:8000/healthz
- 停止：`docker compose down`（数据卷保留）
- 清空数据：`docker compose down -v`

## 服务说明

| 服务 | 镜像/构建 | 作用 |
| --- | --- | --- |
| postgres | pgvector/pgvector:pg16 | 业务数据 + 向量检索（pgvector） |
| redis | redis:7-alpine | 缓存 / 异步任务（预留） |
| backend | 后端多阶段镜像 | FastAPI API；启动时自动 `alembic upgrade head` |
| frontend | 前端多阶段镜像 | Nginx 托管静态资源并反代 `/api` |

## 政务部署说明

- 本编排支持私有化部署（数据不出域）：镜像与容器全部可运行在政务内网
  或国产化环境，仅需将镜像导入内网镜像仓库。
- 生产环境务必修改 `POSTGRES_PASSWORD` 与 `LLM_API_KEY`，并关闭默认端口暴露。
- 如需对接政务统一身份认证 / 台账系统，在 `backend/app/integrations/`
  增加对应渠道适配器即可，代码层面已预留扩展点。