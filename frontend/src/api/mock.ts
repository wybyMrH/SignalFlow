/**
 * Mock / 真实后端切换机制（docs/frontend-development-plan.md §4.2）。
 *
 * 约定：api 层函数签名与后端契约一一对应；内部根据 VITE_USE_MOCK 决定走 mock
 * 还是发起 HTTP 请求。默认 mock（本阶段），后续接后端时在 .env 设
 * `VITE_USE_MOCK=false` 即可切换，页面与 store 代码零改动。
 */
export function useMock(): boolean {
  return import.meta.env.VITE_USE_MOCK !== 'false'
}