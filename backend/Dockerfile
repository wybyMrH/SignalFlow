# SignalFlow 后端镜像
# 多阶段构建：依赖安装（builder） + 精简运行（runtime），减小镜像体积。
# 基础镜像保持与 requires-python >=3.11 兼容，此处选择 3.12-slim。

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY requirements.txt ./
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY --from=builder /install /usr/local

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

EXPOSE 8000

# 启动时先执行数据库迁移，再启动 Uvicorn。
# 数据库就绪由 docker-compose depends_on + healthcheck 保证。
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]