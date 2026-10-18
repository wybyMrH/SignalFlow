#!/usr/bin/env sh
# 重建 8088 前端（docker nginx）并校验其构建产物与当前 frontend/src 源码一致。
#
# 为什么需要它：
#   8088 与 5199 共用同一套 frontend/src 源码，仅数据源不同：
#     - 5199 = vite dev server（frontend/.env.local: VITE_USE_MOCK=false，直连真实后端）
#     - 8088 = docker nginx 静态构建（构建时 .dockerignore 排除 .env.local，走 mock 数据）
#   两者界面/功能必须完全一致。但 8088 是「构建产物」，改动 frontend/src 后若只刷新
#   5199 而不重建 8088 镜像，8088 仍会停留在旧构建（旧版页面/导航），造成两端口不一致。
#   因此每次改动 frontend/src 后，必须执行本脚本重建 8088。
#
# 用法：
#   ./rebuild-frontend.sh                # 重建并校验
#   ./rebuild-frontend.sh --verify-only  # 仅校验当前 8088 构建是否与源码同步
set -e

cd "$(dirname "$0")"

CONTAINER="signalflow-frontend-1"

if [ "${1:-}" != "--verify-only" ]; then
  echo ">>> 重建 frontend 镜像并重启容器 ..."
  docker compose up -d --build frontend
else
  echo ">>> 跳过构建，仅校验现有 8088 构建产物 ..."
fi

echo ">>> 校验 8088 构建产物是否包含当前源码标记 ..."
fail=0
while IFS='|' read -r marker page; do
  [ -z "$marker" ] && continue
  # 用 sh -c 在容器内执行，避免 Git Bash/MSYS 把容器内路径 /usr/... 误转换为宿主路径
  hit=$(docker exec "$CONTAINER" sh -c 'grep -rl "$1" /usr/share/nginx/html/assets 2>/dev/null' _ "$marker" | head -1 || true)
  if [ -n "$hit" ]; then
    echo "    [OK]   $marker  ($page)  ->  $(basename "$hit")"
  else
    echo "    [MISS] $marker  ($page)  未在构建产物中找到"
    fail=1
  fi
done <<'EOF'
渠道接入|SettingsPage
Agent 角色提示词|SettingsPage
全局模型参数|SettingsPage
AI 气泡主题|SettingsPage
回复与回传|RoadmapPage
主题与痛点|InsightsPage
EOF

if [ "$fail" -eq 0 ]; then
  echo ">>> 8088 构建已与 frontend/src 同步：8088 与 5199 页面一致。"
else
  echo ">>> 警告：8088 构建疑似落后于源码，请执行 ./rebuild-frontend.sh 重建。" >&2
  exit 1
fi