<script setup lang="ts">
/**
 * FS-7 系统设置：渠道接入状态 + 数据源说明（mock 展示）。
 * 本阶段不做真实配置写入，只展示状态与说明，无交互报错。
 */
import { onMounted, ref } from 'vue'

import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { fetchSettingsView } from '@/api/settings'
import type { SettingsView } from '@/types'
import { formatDateTime } from '@/utils'

const view = ref<SettingsView | null>(null)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    view.value = await fetchSettingsView()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="st">
    <Skeleton v-if="loading" :rows="8" />
    <template v-else-if="view">
      <section class="card">
        <div class="head">
          <h2 class="title">渠道接入</h2>
          <span class="sub">Mock 数据源 · 接通状态展示</span>
        </div>
        <table class="tbl">
          <thead>
            <tr>
              <th>渠道</th>
              <th>状态</th>
              <th>今日接入</th>
              <th>最近同步</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in view.channels" :key="c.key">
              <td class="nowrap">{{ c.label }}</td>
              <td class="nowrap">
                <StatusBadge
                  :label="c.connected ? '已接通' : c.enabled ? '未连通' : '未启用'"
                  :tone="c.connected ? 'success' : c.enabled ? 'warning' : 'muted'"
                />
              </td>
              <td class="num">{{ c.incoming }}</td>
              <td class="nowrap dim">{{ c.last_sync ? formatDateTime(c.last_sync) : '—' }}</td>
              <td class="dim">{{ c.note }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="card note">
        <h3 class="title">数据源与权限说明</h3>
        <dl class="kv">
          <dt>数据源</dt>
          <dd>{{ view.mock_mode ? '使用模拟数据（VITE_USE_MOCK 默认开启）' : '使用真实后端接口' }}</dd>
          <dt>AI 洞察</dt>
          <dd>{{ view.ai_note }}</dd>
          <dt>身份认证</dt>
          <dd>{{ view.auth_note }}</dd>
        </dl>
      </section>
    </template>
  </div>
</template>

<style scoped>
.st {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.card {
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  box-shadow: var(--sf-shadow);
  padding: var(--sf-space-3) var(--sf-space-4);
}
.head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: var(--sf-space-2);
}
.title {
  margin: 0;
  font-size: var(--sf-font-14);
  font-weight: 600;
}
.sub {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--sf-font-13);
}
.tbl th {
  height: 32px;
  padding: 0 var(--sf-space-1);
  text-align: left;
  font-size: var(--sf-font-12);
  font-weight: 500;
  color: var(--sf-text-secondary);
  background: var(--sf-bg);
  border-bottom: 1px solid var(--sf-border);
  white-space: nowrap;
}
.tbl td {
  height: 36px;
  padding: 0 var(--sf-space-1);
  border-bottom: 1px solid var(--sf-border);
  vertical-align: middle;
}
.tbl tr:last-child td {
  border-bottom: none;
}
.nowrap {
  white-space: nowrap;
}
.dim {
  color: var(--sf-text-secondary);
  font-size: var(--sf-font-12);
}
.num {
  font-variant-numeric: tabular-nums;
}
.note .title {
  margin-bottom: var(--sf-space-2);
}
.kv {
  margin: 0;
  display: grid;
  grid-template-columns: 72px 1fr;
  gap: var(--sf-space-2) var(--sf-space-3);
  font-size: var(--sf-font-13);
}
.kv dt {
  color: var(--sf-text-faint);
}
.kv dd {
  margin: 0;
  color: var(--sf-text-secondary);
}
</style>