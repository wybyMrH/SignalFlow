/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** API 基础路径，默认 /api/v1 */
  readonly VITE_API_BASE_URL?: string
  /** 是否启用 mock 数据源；默认启用，设 false 走真实后端 */
  readonly VITE_USE_MOCK?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}