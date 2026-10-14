import axios from 'axios'

/**
 * Axios 实例：统一 baseURL、超时与拦截器。
 * 鉴权 Token 注入 / 401 跳转在接入身份认证（政务版统一身份）时在此扩展。
 */
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  timeout: 30_000,
})

http.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error),
)

http.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
)

export default http