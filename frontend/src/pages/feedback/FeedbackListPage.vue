<script setup lang="ts">
/**
 * FS-2 反馈管理：信号源下钻页。
 * 顶=筛选条件单行（来源/状态/关键词）；主体=紧凑表格（行高 40px）；
 * 详情=右侧 480px 抽屉（原文 + 归属主题 + 状态流转）。
 * 列表可分页/筛选，状态流转回写 store（mock 驱动）。
 */
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

import Drawer from '@/components/common/Drawer.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SfIcon from '@/components/common/SfIcon.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { fetchAIReplySuggestion } from '@/api/ai'
import { useFeedbackStore } from '@/stores/feedback'
import type { FeedbackSource, FeedbackStatus, FeedbackView } from '@/types'
import { formatDateTime } from '@/utils'
import { sentimentLabels, sentimentTone, sourceLabels, statusLabels, statusTone } from '@/utils/labels'

const route = useRoute()
const store = useFeedbackStore()

const filters = reactive<{ source: FeedbackSource | ''; status: FeedbackStatus | ''; keyword: string }>({
  source: '',
  status: '',
  keyword: '',
})
const drawerOpen = ref(false)
const active = ref<FeedbackView | null>(null)

/** AI 气泡助手状态 */
const aiBubbleOpen = ref(false)
const aiSuggestion = ref('')
const aiSuggestLoading = ref(false)

/** 状态流转动作：当前状态 → 可执行按钮（含 AI 流转） */
const NEXT_STATUS: Array<{ from: FeedbackStatus[]; to: FeedbackStatus; label: string; tone: 'info' | 'success' | 'warning' | 'muted' }> = [
  { from: ['new'], to: 'analyzing', label: '受理', tone: 'info' },
  { from: ['new', 'analyzing'], to: 'ai_reviewing', label: 'AI生成回复', tone: 'info' },
  { from: ['new', 'analyzing'], to: 'resolved', label: '解决', tone: 'success' },
  { from: ['new', 'analyzing'], to: 'replied', label: '回复', tone: 'success' },
  { from: ['ai_reviewing'], to: 'replied', label: '确认发送', tone: 'success' },
  { from: ['ai_replied'], to: 'closed', label: '关闭', tone: 'muted' },
  { from: ['resolved', 'replied'], to: 'closed', label: '关闭', tone: 'muted' },
  { from: ['closed'], to: 'new', label: '重开', tone: 'warning' },
]

const canAct = computed(() => (s: FeedbackStatus) => NEXT_STATUS.filter((n) => n.from.includes(s)))

onMounted(() => {
  const s = route.query.status as string | undefined
  if (s) store.setFilter({ status: s as FeedbackStatus })
  if (route.query.source) {
    const src = String(route.query.source)
    if (src in sourceLabels) store.setFilter({ source: src as FeedbackSource })
  }
  void store.fetchPage()
})

function apply() {
  store.setFilter({ source: filters.source, status: filters.status, keyword: filters.keyword })
  void store.fetchPage()
}

function reset() {
  filters.source = ''
  filters.status = ''
  filters.keyword = ''
  store.setFilter({ source: '', status: '', keyword: '' })
  void store.fetchPage()
}

function openDetail(item: FeedbackView) {
  active.value = item
  drawerOpen.value = true
}

async function transit(next: FeedbackStatus) {
  if (!active.value) return
  await store.setStatus(active.value.id, next)
  active.value = store.items.find((r) => r.id === active.value?.id) ?? active.value
}

function page(delta: number) {
  const next = (store.query.page ?? 1) + delta
  if (next < 1) return
  store.setFilter({ page: next })
  void store.fetchPage()
}

/** AI 生成回复草稿 */
async function aiGenerateReply() {
  if (!active.value) return
  await store.generateReply(active.value.id, active.value.content)
  active.value = store.items.find((r) => r.id === active.value?.id) ?? active.value
}

/** AI 自动审批 */
async function aiAutoApprove() {
  if (!active.value) return
  await store.autoApprove(active.value.id, active.value.content)
  active.value = store.items.find((r) => r.id === active.value?.id) ?? active.value
}

/** 气泡助手：获取回复建议 */
async function askAIForSuggestion() {
  if (!active.value) return
  aiSuggestLoading.value = true
  aiSuggestion.value = ''
  try {
    aiSuggestion.value = await fetchAIReplySuggestion(active.value.content)
  } finally {
    aiSuggestLoading.value = false
  }
}

function clearActiveDraft() {
  if (!active.value) return
  store.clearDraft(active.value.id)
}
</script>

<template>
  <div class="fb">
    <!-- 筛选单行 -->
    <section class="card filter-bar">
      <select v-model="filters.source" class="sel" aria-label="来源">
        <option value="">全部来源</option>
        <option v-for="(label, key) in sourceLabels" :key="key" :value="key">{{ label }}</option>
      </select>
      <select v-model="filters.status" class="sel" aria-label="状态">
        <option value="">全部状态</option>
        <option v-for="(label, key) in statusLabels" :key="key" :value="key">{{ label }}</option>
      </select>
      <input v-model="filters.keyword" class="kw" type="search" placeholder="搜索关键词" @keyup.enter="apply" />
      <button type="button" class="btn primary" @click="apply">
        <SfIcon name="search" :size="16" /> 查询
      </button>
      <button type="button" class="btn" @click="reset">
        <SfIcon name="refresh" :size="15" /> 重置
      </button>
      <span class="total num">{{ store.total }} 条</span>
    </section>

    <!-- 紧凑表格 -->
    <section class="card table-card">
      <Skeleton v-if="store.loading" :rows="8" />
      <EmptyState v-else-if="store.items.length === 0" text="无匹配反馈" />
      <table v-else class="tbl">
        <thead>
          <tr>
            <th>来源</th>
            <th>反馈内容</th>
            <th>主题</th>
            <th>情感</th>
            <th>状态</th>
            <th>处理人</th>
            <th>时间</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in store.items" :key="item.id" class="row" @click="openDetail(item)">
            <td class="nowrap">{{ sourceLabels[item.source as keyof typeof sourceLabels] ?? item.source }}</td>
            <td class="cell-content">
              <span class="row-title">{{ item.content }}</span>
              <span class="row-id">{{ item.id }}</span>
            </td>
            <td class="nowrap dim">{{ item.topic_title ?? '—' }}</td>
            <td class="nowrap">
              <StatusBadge v-if="item.sentiment" :label="sentimentLabels[item.sentiment]" :tone="sentimentTone[item.sentiment]" />
            </td>
            <td class="nowrap"><StatusBadge :label="statusLabels[item.status]" :tone="statusTone[item.status]" /></td>
            <td class="nowrap dim">{{ item.reviewer ?? '—' }}</td>
            <td class="nowrap dim">{{ formatDateTime(item.created_at) }}</td>
            <td class="nowrap"><SfIcon name="chevron-right" :size="14" class="row-arrow" /></td>
          </tr>
        </tbody>
      </table>
      <!-- 分页 -->
      <div v-if="!store.loading && store.items.length" class="pager">
        <button type="button" class="btn sm" :disabled="(store.query.page ?? 1) <= 1" @click="page(-1)">上一页</button>
        <span class="page-info num">第 {{ store.query.page }} / {{ Math.max(1, Math.ceil(store.total / (store.query.page_size ?? 20))) }} 页</span>
        <button
          type="button"
          class="btn sm"
          :disabled="(store.query.page ?? 1) >= Math.ceil(store.total / (store.query.page_size ?? 20))"
          @click="page(1)"
        >
          下一页
        </button>
      </div>
    </section>

    <!-- 详情抽屉 -->
    <Drawer :open="drawerOpen" :title="active ? `${active.id} 详情` : ''" @close="drawerOpen = false">
      <div v-if="active" class="detail">
        <div class="detail-meta">
          <StatusBadge :label="statusLabels[active.status]" :tone="statusTone[active.status]" />
          <span class="dim">{{ sourceLabels[active.source as keyof typeof sourceLabels] ?? active.source }}</span>
          <span class="dim">{{ formatDateTime(active.created_at) }}</span>
        </div>
        <p class="detail-content">{{ active.content }}</p>
        <dl class="kv">
          <dt>作者</dt>
          <dd>{{ active.author ?? '匿名' }}</dd>
          <dt>归属主题</dt>
          <dd>{{ active.topic_title ?? '未归主题' }}</dd>
          <dt>处理人</dt>
          <dd>{{ active.reviewer ?? '未分配' }}</dd>
        </dl>

        <!-- AI 操作区 -->
        <div v-if="active.status === 'new' || active.status === 'analyzing'" class="ai-section">
          <div class="ai-section-title">
            <SfIcon name="logo" :size="14" />
            AI 辅助处理
          </div>
          <div class="ai-actions">
            <button
              type="button"
              class="btn sm ai-btn"
              :disabled="store.aiDraftLoading === active.id"
              @click="aiGenerateReply"
            >
              <SfIcon name="chat" :size="13" />
              {{ store.aiDraftLoading === active.id ? '生成中...' : 'AI 生成回复' }}
            </button>
            <button
              type="button"
              class="btn sm ai-btn primary"
              :disabled="store.aiApproveLoading === active.id"
              @click="aiAutoApprove"
            >
              <SfIcon name="check" :size="13" />
              {{ store.aiApproveLoading === active.id ? '审批中...' : 'AI 自动审批' }}
            </button>
          </div>
        </div>

        <!-- AI 草稿展示 -->
        <div v-if="store.aiDrafts[active.id]" class="ai-draft-box">
          <div class="ai-draft-header">
            <span class="ai-draft-label"><SfIcon name="logo" :size="12" /> AI 回复草稿</span>
            <button type="button" class="btn sm" @click="clearActiveDraft">清除</button>
          </div>
          <div class="ai-draft-body">{{ store.aiDrafts[active.id] }}</div>
        </div>

        <div class="act">
          <button
            v-for="n in canAct(active.status)"
            :key="n.to"
            type="button"
            class="btn sm"
            :class="n.tone === 'success' ? 'primary' : ''"
            @click="transit(n.to)"
          >
            {{ n.label }}
          </button>
        </div>
      </div>
    </Drawer>

    <!-- AI 气泡助手（悬浮） -->
    <div class="ai-bubble" :class="{ open: aiBubbleOpen }">
      <button type="button" class="ai-bubble-trigger" @click="aiBubbleOpen = !aiBubbleOpen">
        <SfIcon :name="aiBubbleOpen ? 'close' : 'logo'" :size="20" />
      </button>
      <div v-if="aiBubbleOpen" class="ai-bubble-panel">
        <div class="ai-bubble-head">
          <SfIcon name="logo" :size="14" />
          AI 回复助手
        </div>
        <div class="ai-bubble-body">
          <p class="ai-bubble-hint">
            选中反馈详情后，点击「获取建议」即可基于知识库与政策库获得回复建议。
          </p>
          <button
            type="button"
            class="btn primary sm"
            style="width: 100%; margin-top: 8px;"
            :disabled="!active || aiSuggestLoading"
            @click="askAIForSuggestion"
          >
            {{ aiSuggestLoading ? '思考中...' : '获取回复建议' }}
          </button>
          <div v-if="aiSuggestion" class="ai-suggestion">
            <div class="ai-suggestion-label">建议</div>
            {{ aiSuggestion }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fb {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.card {
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  box-shadow: var(--sf-shadow);
}
.filter-bar {
  display: flex;
  align-items: center;
  gap: var(--sf-space-2);
  padding: var(--sf-space-2) var(--sf-space-3);
  flex-wrap: wrap;
}
.sel,
.kw {
  height: 30px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text);
  font-size: var(--sf-font-13);
  padding: 0 var(--sf-space-2);
}
.sel {
  min-width: 108px;
}
.kw {
  min-width: 200px;
  flex: 1;
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 30px;
  padding: 0 var(--sf-space-3);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text);
  font-size: var(--sf-font-13);
  cursor: pointer;
  white-space: nowrap;
}
.btn:hover {
  border-color: var(--sf-primary);
  color: var(--sf-primary);
}
.btn.primary {
  background: var(--sf-primary);
  border-color: var(--sf-primary);
  color: #fff;
}
.btn.primary:hover {
  background: var(--sf-primary-light);
}
.btn.sm {
  height: 26px;
  padding: 0 var(--sf-space-2);
  font-size: var(--sf-font-12);
}
.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.total {
  margin-left: auto;
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.table-card {
  overflow: hidden;
}
.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--sf-font-13);
}
.tbl th {
  height: 36px;
  padding: 0 var(--sf-space-2);
  text-align: left;
  font-size: var(--sf-font-12);
  font-weight: 500;
  color: var(--sf-text-secondary);
  background: var(--sf-bg);
  border-bottom: 1px solid var(--sf-border);
  white-space: nowrap;
}
.tbl td {
  height: 40px;
  padding: 0 var(--sf-space-2);
  border-bottom: 1px solid var(--sf-border);
  vertical-align: middle;
}
.row {
  cursor: pointer;
  transition: background 0.12s ease;
}
.row:hover {
  background: var(--sf-primary-soft);
}
.row:last-child td {
  border-bottom: none;
}
.nowrap {
  white-space: nowrap;
}
.dim {
  color: var(--sf-text-secondary);
  font-size: var(--sf-font-12);
}
.cell-content {
  max-width: 380px;
}
.row-title {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.row-id {
  display: block;
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.row-arrow {
  color: var(--sf-text-faint);
}
.pager {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--sf-space-2);
  padding: var(--sf-space-2) var(--sf-space-3);
  border-top: 1px solid var(--sf-border);
}
.page-info {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
}
.detail {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.detail-meta {
  display: flex;
  align-items: center;
  gap: var(--sf-space-2);
  flex-wrap: wrap;
}
.detail-content {
  margin: 0;
  font-size: var(--sf-font-14);
  line-height: 1.6;
}
.kv {
  margin: 0;
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: var(--sf-space-2) var(--sf-space-3);
  font-size: var(--sf-font-13);
}
.kv dt {
  color: var(--sf-text-faint);
}
.kv dd {
  margin: 0;
}
.act {
  display: flex;
  gap: var(--sf-space-2);
  padding-top: var(--sf-space-2);
  border-top: 1px solid var(--sf-border);
}

/* AI 辅助区 */
.ai-section {
  padding: var(--sf-space-3);
  border-radius: var(--sf-radius-sm);
  background: linear-gradient(135deg, var(--sf-primary-soft) 0%, transparent 100%);
  border: 1px solid var(--sf-primary-border);
}
.ai-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--sf-font-13);
  font-weight: 600;
  color: var(--sf-primary);
  margin-bottom: var(--sf-space-2);
}
.ai-actions {
  display: flex;
  gap: var(--sf-space-2);
  flex-wrap: wrap;
}
.ai-btn {
  border-color: var(--sf-primary-border);
  color: var(--sf-primary);
}
.ai-btn:hover:not(:disabled) {
  background: var(--sf-primary-soft);
}

/* AI 草稿展示 */
.ai-draft-box {
  padding: var(--sf-space-3);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-bg);
  border: 1px solid var(--sf-border);
}
.ai-draft-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--sf-space-2);
}
.ai-draft-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-primary);
}
.ai-draft-body {
  font-size: var(--sf-font-13);
  line-height: 1.6;
  color: var(--sf-text);
  white-space: pre-line;
}

/* AI 气泡助手 */
.ai-bubble {
  position: fixed;
  right: var(--sf-space-4);
  bottom: var(--sf-space-4);
  z-index: 50;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--sf-space-2);
}
.ai-bubble-trigger {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: var(--sf-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s ease;
}
.ai-bubble-trigger:hover {
  transform: scale(1.05);
}
.ai-bubble-panel {
  width: 320px;
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  box-shadow: var(--sf-shadow);
  overflow: hidden;
}
.ai-bubble-head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: var(--sf-space-3) var(--sf-space-4);
  font-size: var(--sf-font-14);
  font-weight: 600;
  background: linear-gradient(135deg, var(--sf-primary-soft) 0%, transparent 100%);
  border-bottom: 1px solid var(--sf-border);
}
.ai-bubble-body {
  padding: var(--sf-space-3) var(--sf-space-4);
}
.ai-bubble-hint {
  margin: 0;
  font-size: var(--sf-font-13);
  color: var(--sf-text-secondary);
  line-height: 1.5;
}
.ai-suggestion {
  margin-top: var(--sf-space-3);
  padding: var(--sf-space-2) var(--sf-space-3);
  background: var(--sf-primary-soft);
  border: 1px solid var(--sf-primary-border);
  border-radius: var(--sf-radius-sm);
  font-size: var(--sf-font-13);
  line-height: 1.5;
  color: var(--sf-text);
}
.ai-suggestion-label {
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-primary);
  margin-bottom: 4px;
}
</style>