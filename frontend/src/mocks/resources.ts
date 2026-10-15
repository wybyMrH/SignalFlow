import type { ResourceDetail } from '@/types'

/**
 * 资源管理详情（Mock）：
 * 模拟服务器 / 数据库 / API / 日志 / 告警，供「资源管理」页面展示与检索。
 * 理念：资源不是静态台账，而是与工作流运行、Agent 执行联动的监控层——
 * 工作流异常会在这里呈现为告警，API 端点健康反映在手办闭环的可观测性上。
 */
const minsAgo = (n: number) => new Date(Date.now() - n * 60_000).toISOString()

export function getResourceDetail(): ResourceDetail {
  return {
    updated_at: new Date().toISOString(),
    servers: [
      { id: 'SRV-01', name: 'api-gateway-01', role: 'API 网关', cpu: 42, mem: 55, disk: 46, load: '0.8, 0.6, 0.5', uptime: '32 天', status: 'healthy' },
      { id: 'SRV-02', name: 'app-worker-01', role: '应用服务', cpu: 68, mem: 61, disk: 52, load: '1.6, 1.3, 1.1', uptime: '18 天', status: 'healthy' },
      { id: 'SRV-03', name: 'scheduler-01', role: '任务调度', cpu: 35, mem: 44, disk: 58, load: '0.4, 0.5, 0.4', uptime: '45 天', status: 'healthy' },
      { id: 'SRV-04', name: 'model-infer-01', role: '模型推理', cpu: 82, mem: 74, disk: 63, load: '3.4, 2.9, 2.6', uptime: '12 天', status: 'warning' },
    ],
    databases: [
      { id: 'DB-01', name: 'postgres-main', engine: 'PostgreSQL 16 (pgvector)', status: 'healthy', connections: 23, max_connections: 100, slow_queries: 2, tablespace_pct: 38, last_check: minsAgo(2) },
      { id: 'DB-02', name: 'redis-cache', engine: 'Redis 7', status: 'healthy', connections: 8, max_connections: 64, slow_queries: 0, tablespace_pct: 12, last_check: minsAgo(1) },
      { id: 'DB-03', name: 'milvus-vector', engine: 'Milvus 2.4', status: 'degraded', connections: 5, max_connections: 32, slow_queries: 7, tablespace_pct: 71, last_check: minsAgo(4) },
    ],
    apis: [
      { id: 'API-01', method: 'GET', path: '/api/v1/healthz', status: 'healthy', response_ms: 23, error_rate: 0.0, rps: 12.4 },
      { id: 'API-02', method: 'GET', path: '/api/v1/feedbacks', status: 'healthy', response_ms: 41, error_rate: 0.2, rps: 8.1 },
      { id: 'API-03', method: 'GET', path: '/api/v1/insights/topics', status: 'healthy', response_ms: 56, error_rate: 0.4, rps: 3.2 },
      { id: 'API-04', method: 'POST', path: '/api/v1/ai/classify', status: 'healthy', response_ms: 320, error_rate: 1.1, rps: 2.7 },
      { id: 'API-05', method: 'POST', path: '/api/v1/ai/reply/generate', status: 'healthy', response_ms: 480, error_rate: 1.8, rps: 1.9 },
      { id: 'API-06', method: 'GET', path: '/api/v1/gov/summary', status: 'degraded', response_ms: 612, error_rate: 3.4, rps: 1.2 },
      { id: 'API-07', method: 'GET', path: '/api/v1/business/leads', status: 'healthy', response_ms: 63, error_rate: 0.3, rps: 1.5 },
      { id: 'API-08', method: 'POST', path: '/api/v1/workflows/run', status: 'healthy', response_ms: 240, error_rate: 0.9, rps: 0.8 },
      { id: 'API-09', method: 'GET', path: '/api/v1/resources/health', status: 'healthy', response_ms: 35, error_rate: 0.0, rps: 2.3 },
      { id: 'API-10', method: 'GET', path: '/api/v1/resources/logs', status: 'healthy', response_ms: 52, error_rate: 0.1, rps: 1.7 },
      { id: 'API-11', method: 'GET', path: '/api/v1/interviews', status: 'healthy', response_ms: 47, error_rate: 0.2, rps: 1.1 },
      { id: 'API-12', method: 'GET', path: '/api/v1/agents', status: 'healthy', response_ms: 39, error_rate: 0.0, rps: 1.4 },
      { id: 'API-13', method: 'POST', path: '/api/v1/notices/publish', status: 'degraded', response_ms: 880, error_rate: 4.6, rps: 0.2 },
      { id: 'API-14', method: 'GET', path: '/api/v1/report/export', status: 'down', response_ms: 0, error_rate: 100.0, rps: 0.0 },
    ],
    logs: [
      { id: 'LG-001', time: minsAgo(1), level: 'warn', module: 'milvus-vector', message: '向量检索延迟上升：P95 从 120ms 升至 320ms，建议检查索引重建任务' },
      { id: 'LG-002', time: minsAgo(3), level: 'error', module: 'report-service', message: '导出任务 EXP-2045 失败：PDF 渲染进程内存溢出，已自动重试 2 次' },
      { id: 'LG-003', time: minsAgo(6), level: 'info', module: 'scheduler-01', message: '工作流 WF-SENTIMENT-ALERT 定时触发完成，共处理 12 条新增舆情' },
      { id: 'LG-004', time: minsAgo(9), level: 'info', module: 'app-worker-01', message: 'Agent AG-002 完成商单回复草稿 3 份，进入人工审批队列' },
      { id: 'LG-005', time: minsAgo(14), level: 'info', module: 'api-gateway-01', message: '接口 /api/v1/gov/summary 响应时间超过 600ms，已记录慢请求采样' },
      { id: 'LG-006', time: minsAgo(20), level: 'info', module: 'scheduler-01', message: '数据同步任务 SYNC-042 完成：反馈库新增 10 条，去重合并 3 组' },
      { id: 'LG-007', time: minsAgo(26), level: 'warn', module: 'model-infer-01', message: '推理节点 GPU 显存使用率 88%，未来 1 小时有批量聚类任务，存在排队风险' },
      { id: 'LG-008', time: minsAgo(35), level: 'info', module: 'postgres-main', message: '慢查询收敛：近 1 小时慢 SQL 2 条，均为含向量检索的大范围筛选' },
      { id: 'LG-009', time: minsAgo(48), level: 'error', module: 'report-service', message: '导出任务 EXP-2039 重试超过上限，已转人工处理，工单编号 TK-1180' },
      { id: 'LG-010', time: minsAgo(60), level: 'info', module: 'app-worker-01', message: 'Agent AG-001 完成政策公告草稿《智能客服平台升级通知》，等待发布审批' },
    ],
    alerts: [
      { id: 'AL-001', level: 'error', title: '导出服务连续失败', time: minsAgo(3), target: 'report-service / EXP-2045' },
      { id: 'AL-002', level: 'warn', title: '模型推理节点负载过高', time: minsAgo(26), target: 'model-infer-01' },
      { id: 'AL-003', level: 'warn', title: '向量库检索延迟上升', time: minsAgo(1), target: 'milvus-vector' },
      { id: 'AL-004', level: 'info', title: '政策公告草稿待审批', time: minsAgo(60), target: 'Agent AG-001' },
    ],
  }
}