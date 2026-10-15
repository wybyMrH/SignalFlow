import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchResourceDetail } from '@/api/resources'
import type { ResourceDetail } from '@/types'

/**
 * 资源管理 store：服务器/数据库/API/日志/告警。
 * 理念：资源健康与总览驾驶舱复用同一数据源；工作流与 Agent 运行异常
 * 会以告警形式回到这里，形成「执行 → 观测 → 处置」闭环。
 */
export const useResourcesStore = defineStore('resources', () => {
  const detail = ref<ResourceDetail | null>(null)
  const loading = ref(false)
  const lastError = ref<string | null>(null)

  const healthyServers = computed(() => detail.value?.servers.filter((s) => s.status === 'healthy').length ?? 0)
  const healthyApis = computed(() => detail.value?.apis.filter((a) => a.status === 'healthy').length ?? 0)
  const degradedApis = computed(() => detail.value?.apis.filter((a) => a.status === 'degraded').length ?? 0)
  const downApis = computed(() => detail.value?.apis.filter((a) => a.status === 'down').length ?? 0)
  const errorLogs = computed(() => detail.value?.logs.filter((l) => l.level === 'error').length ?? 0)
  const warnLogs = computed(() => detail.value?.logs.filter((l) => l.level === 'warn').length ?? 0)

  async function fetchAll() {
    loading.value = true
    try {
      detail.value = await fetchResourceDetail()
      lastError.value = null
    } catch (e) {
      lastError.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  return {
    detail,
    loading,
    lastError,
    healthyServers,
    healthyApis,
    degradedApis,
    downApis,
    errorLogs,
    warnLogs,
    fetchAll,
  }
})