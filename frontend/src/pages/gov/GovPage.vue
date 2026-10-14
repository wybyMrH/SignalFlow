<script setup lang="ts">
/**
 * FS-6 政务适配：克制成稳的政务规则面板。
 * 上=诉求分级（A-D 占比）+ 督办事项；下=政策告知 + 审计留痕。
 * 本阶段全部 mock 驱动；导出报告为 UI 占位（后续接导出服务）。
 */
import { onMounted, ref } from 'vue'

import BarRow from '@/components/common/BarRow.vue'
import SfIcon from '@/components/common/SfIcon.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { fetchGovOverview } from '@/api/gov'
import type { GovOverview } from '@/types'

const overview = ref<GovOverview | null>(null)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    overview.value = await fetchGovOverview()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="gov">
    <Skeleton v-if="loading" :rows="8" />
    <template v-else-if="overview">
      <div class="row2">
        <section class="card">
          <div class="head">
            <h2 class="title">诉求分级</h2>
            <span class="sub">A 类即报 · 敏感优先</span>
          </div>
          <div class="bars">
            <BarRow
              v-for="c in overview.classifications"
              :key="c.level"
              :label="`${c.level} ${c.label}`"
              :value="c.count"
              :pct="c.pct"
              :tone="c.tone"
            />
          </div>
        </section>

        <section class="card">
          <div class="head">
            <h2 class="title">督办事项</h2>
            <span class="sub">逾期自动标红</span>
          </div>
          <table class="tbl">
            <thead>
              <tr>
                <th>层级</th>
                <th>事项</th>
                <th>数量</th>
                <th>逾期</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in overview.supervisions" :key="s.level">
                <td class="nowrap">{{ s.level }}</td>
                <td class="nowrap dim">{{ s.label }}</td>
                <td class="num">{{ s.count }}</td>
                <td>
                  <StatusBadge :label="String(s.overdue)" :tone="s.overdue > 0 ? 'danger' : 'success'" />
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>

      <div class="row2">
        <section class="card">
          <div class="head">
            <h2 class="title">政策告知</h2>
            <span class="sub">公告直发渠道</span>
          </div>
          <ul class="notice-list">
            <li v-for="n in overview.notices" :key="n.id" class="notice">
              <div class="n-top">
                <span class="n-title">{{ n.title }}</span>
                <StatusBadge :label="n.status === 'published' ? '已发布' : '草稿'" :tone="n.status === 'published' ? 'success' : 'warning'" />
              </div>
              <p class="n-content">{{ n.content }}</p>
              <span class="n-meta">{{ n.scope }} · 发送 {{ n.sent_count }} 人</span>
            </li>
          </ul>
          <button type="button" class="btn sm ghost">
            <SfIcon name="external" :size="14" /> 导出报告
          </button>
        </section>

        <section class="card">
          <div class="head">
            <h2 class="title">审计留痕</h2>
            <span class="sub">全程可追溯</span>
          </div>
          <table class="tbl">
            <thead>
              <tr>
                <th>操作</th>
                <th>操作人</th>
                <th>对象</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in overview.audits" :key="a.id">
                <td class="nowrap">{{ a.action }}</td>
                <td class="nowrap dim">{{ a.operator }}</td>
                <td class="nowrap dim">{{ a.target }}</td>
                <td class="nowrap dim">{{ a.time }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.gov {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.row2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
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
.bars {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
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
.notice-list {
  list-style: none;
  margin: 0 0 var(--sf-space-2);
  padding: 0;
}
.notice {
  padding: var(--sf-space-2) 0;
  border-bottom: 1px solid var(--sf-border);
}
.notice:last-child {
  border-bottom: none;
}
.n-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
}
.n-title {
  font-size: var(--sf-font-13);
  font-weight: 600;
}
.n-content {
  margin: 3px 0;
  font-size: var(--sf-font-13);
  color: var(--sf-text-secondary);
  line-height: 1.4;
}
.n-meta {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 28px;
  padding: 0 var(--sf-space-2);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text-secondary);
  font-size: var(--sf-font-12);
  cursor: pointer;
}
.btn:hover {
  border-color: var(--sf-primary);
  color: var(--sf-primary);
}
.btn.sm.ghost {
  background: transparent;
}
@media (max-width: 1000px) {
  .row2 {
    grid-template-columns: 1fr;
  }
}
</style>