# SignalFlow Frontend

客户反馈决策工具 - Web 前端（Vue 3 + TypeScript）。

## 技术栈

- Vue 3（Composition API + `<script setup>`）
- TypeScript（strict 模式）
- Vite（构建与开发服务器）
- Pinia（状态管理）
- Vue Router（页面路由）
- Axios（HTTP 客户端，经 `/api` 代理访问后端）

## 目录结构

```text
frontend/
├── src/
│   ├── api/            # API 客户端（http 实例 + 领域接口）
│   ├── components/     # 通用组件（common/ 为公共组件）
│   ├── pages/          # 页面级组件（总览 / 反馈 / 洞察 / 设置）
│   ├── router/         # 路由表
│   ├── stores/         # Pinia 状态管理
│   ├── styles/         # 全局样式与设计令牌
│   ├── types/          # 类型定义（与后端 schema 对齐）
│   ├── utils/          # 工具函数
│   ├── App.vue         # 应用外壳（导航 + 内容区）
│   └── main.ts         # 应用入口
├── vite.config.ts      # Vite 配置（含 /api 开发代理与 @ 别名）
├── tsconfig.json       # TypeScript 配置
└── package.json        # 依赖与脚本
```

## 本地运行

```bash
npm install
npm run dev        # 开发服务器 http://localhost:5173
npm run build      # 类型检查 + 生产构建（产物在 dist/）
npm run type-check # 仅类型检查
```

开发期 `vite.config.ts` 已配置 `/api -> http://localhost:8000` 代理，
无需为本地联调配置跨域。

## 约定

- 类型定义集中维护在 `src/types/`，与后端 `app/schemas/` 一一对应；
  后端契约变更时同步更新。
- 鉴权 Token 注入与 401 处理在 `src/api/http.ts` 拦截器中扩展
  （政务版接入统一身份认证时启用）。