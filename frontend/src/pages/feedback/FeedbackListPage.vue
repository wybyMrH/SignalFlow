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
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { fetchAIReplySuggestion, sendAIChatMessage } from '@/api/ai'
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

/** 可编辑的 AI 草稿（id -> draft） */
const editableDrafts = ref<Record<string, string>>({})

/** AI 气泡助手状态 */
const aiBubbleOpen = ref(false)
const aiSuggestion = ref('')
const aiSuggestLoading = ref(false)
/** 气泡助手模式：'home' | 'chat' */
const bubbleMode = ref<'home' | 'chat'>('home')
const bubbleInput = ref('')
const bubbleMessages = ref<Array<{ role: 'user' | 'assistant'; content: string }>>([])
const bubbleLoading = ref(false)
/** 历史会话（本地会话记录：标题 -> 消息列表） */
const bubbleHistory = ref<Array<{ title: string; messages: Array<{ role: 'user' | 'assistant'; content: string }> }>>([
  {
    title: '今天工单情况如何？',
    messages: [
      { role: 'user', content: '今天工单情况如何？' },
      { role: 'assistant', content: '今日新接入工单 64 条，待处理 31 条，其中高优先级 4 条；平均解决时长约 6.2 小时。主要渠道为热线与工单系统。' },
    ],
  },
  {
    title: '大厅排队问题怎么解决？',
    messages: [
      { role: 'user', content: '大厅排队问题怎么解决？' },
      { role: 'assistant', content: '建议推进「动态开窗」优化任务：高峰时段按实时客流开放窗口，并上线微信排队提醒，同时保留老年人人工取号通道。' },
    ],
  },
])

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
  void store.fetchStats()
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
  if (store.aiDrafts[item.id]) {
    editableDrafts.value[item.id] = store.aiDrafts[item.id]
  }
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

/** 保存草稿（仅前端） */
function saveDraft() {
  if (!active.value) return
  const d = editableDrafts.value[active.value.id]
  if (d !== undefined) store.aiDrafts[active.value.id] = d
}

/** 采用并发送：把用户编辑后的草稿作为正式回复发出，并流转状态为已回复 */
async function sendDraft() {
  if (!active.value) return
  saveDraft()
  const id = active.value.id
  const draft = editableDrafts.value[id] ?? store.aiDrafts[id]
  await store.setStatus(id, 'replied', '管理员', draft)
  store.clearDraft(id)
  delete editableDrafts.value[id]
  active.value = store.items.find((r) => r.id === active.value?.id) ?? active.value
}

function clearActiveDraft() {
  if (!active.value) return
  store.clearDraft(active.value.id)
  delete editableDrafts.value[active.value.id]
}

/** 气泡助手：打开会话记录并切换到聊天模式 */
function openBubbleHistory(idx: number) {
  const h = bubbleHistory.value[idx]
  if (!h) return
  bubbleMessages.value = h.messages.map((m) => ({ ...m }))
  bubbleMode.value = 'chat'
}

/** 气泡助手发送消息（接入 AI 对话链路） */
async function sendBubbleMessage() {
  const text = bubbleInput.value.trim()
  if (!text) return
  bubbleMode.value = 'chat'
  bubbleMessages.value.push({ role: 'user', content: text })
  bubbleInput.value = ''
  bubbleLoading.value = true
  try {
    const reply = await sendAIChatMessage(
      text,
      bubbleMessages.value.map((m) => ({
        id: m.content,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        timestamp: new Date().toISOString(),
      })),
    )
    bubbleMessages.value.push({ role: 'assistant', content: reply.content })
    // 记录为历史会话（保留最近 8 条，覆盖同标题会话）
    const title = text.length > 18 ? `${text.slice(0, 18)}…` : text
    const existing = bubbleHistory.value.findIndex((h) => h.title === title)
    const entry = { title, messages: bubbleMessages.value.map((m) => ({ ...m })) }
    if (existing >= 0) bubbleHistory.value[existing] = entry
    else bubbleHistory.value.unshift(entry)
    if (bubbleHistory.value.length > 8) bubbleHistory.value.length = 8
  } finally {
    bubbleLoading.value = false
  }
}

/** 将气泡助手中的建议插入到草稿区 */
function insertSuggestionToDraft() {
  if (!active.value || !aiSuggestion.value) return
  const id = active.value.id
  store.aiDrafts[id] = aiSuggestion.value
  editableDrafts.value[id] = aiSuggestion.value
  aiSuggestion.value = ''
}
</script>

<template>
  <div class="fb">
    <!-- 状态统计卡 -->
    <section class="stats-bar">
      <StatCard label="全部反馈" :value="store.stats?.total ?? 0" />
      <StatCard label="待解决" :value="(store.stats?.new ?? 0) + (store.stats?.analyzing ?? 0)" hint="新提交+分析中" />
      <StatCard label="AI审核中" :value="store.stats?.ai_reviewing ?? 0" />
      <StatCard label="AI已回复" :value="store.stats?.ai_replied ?? 0" />
      <StatCard label="已解决" :value="(store.stats?.resolved ?? 0) + (store.stats?.replied ?? 0)" hint="已回复+已解决" />
      <StatCard label="高优先级" :value="store.stats?.high_priority ?? 0" />
    </section>

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

        <!-- 回复内容区：始终可见，按状态展示不同标签与内容 -->
        <div class="reply-section">
          <div class="reply-section-header">
            <SfIcon name="chat" :size="12" />
            <span v-if="active.reply_content">已回复内容</span>
            <span v-else-if="store.aiDrafts[active.id] || editableDrafts[active.id]">AI 回复草稿（审核中）</span>
            <span v-else>回复内容</span>
            <span v-if="active.reviewer || active.replied_at" class="reply-meta">
              <span v-if="active.reviewer">{{ active.reviewer }}</span>
              <span v-if="active.replied_at">{{ formatDateTime(active.replied_at) }}</span>
            </span>
          </div>
          <div v-if="active.reply_content" class="reply-body">{{ active.reply_content }}</div>
          <div v-else-if="store.aiDrafts[active.id] || editableDrafts[active.id]" class="ai-draft-wrap">
            <textarea
              :value="editableDrafts[active.id] ?? store.aiDrafts[active.id]"
              @input="(e: any) => { if (active) editableDrafts[active.id] = e.target.value }"
              class="ai-draft-textarea"
              rows="8"
              placeholder="可在此修改 AI 生成的回复草稿..."
            />
            <div class="ai-draft-footer">
              <button type="button" class="btn sm" @click="clearActiveDraft">清除</button>
              <button type="button" class="btn sm" @click="saveDraft">保存草稿</button>
              <button type="button" class="btn sm primary" @click="sendDraft">采用并发送</button>
            </div>
          </div>
          <div v-else class="reply-body empty">暂无回复</div>
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

    <!-- AI 助手气泡（悬浮） -->
    <div class="ai-bubble" :class="{ open: aiBubbleOpen }">
      <button type="button" class="ai-bubble-trigger" @click="aiBubbleOpen = !aiBubbleOpen">
        <SfIcon :name="aiBubbleOpen ? 'close' : 'logo'" :size="20" />
      </button>
      <div v-if="aiBubbleOpen" class="ai-bubble-panel">
        <div class="ai-bubble-head">
          <SfIcon name="logo" :size="14" />
          <span>SignalFlow AI 助手</span>
          <button type="button" class="btn ghost sm" style="margin-left:auto" @click="aiBubbleOpen = false">
            <SfIcon name="close" :size="14" />
          </button>
        </div>

        <!-- 欢迎页 -->
        <div v-if="bubbleMode === 'home'" class="ai-bubble-body">
          <div class="ai-welcome">
            <div class="ai-welcome-title">您好，欢迎使用 AI 助手</div>
            <p class="ai-welcome-sub">我可以帮您处理反馈、生成回复草稿、查询工单状态或解答政务问题。</p>
          </div>

          <div class="ai-categories">
            <button v-for="c in [
              { label: '政策咨询', icon: 'shield' },
              { label: '办事流程', icon: 'checklist' },
              { label: '投诉举报', icon: 'alert' },
              { label: '民生诉求', icon: 'chat' },
              { label: '服务态度', icon: 'sentiment' },
              { label: '应急事件', icon: 'clock' },
            ]" :key="c.label" type="button" class="ai-category" @click="bubbleInput = c.label; sendBubbleMessage()">
              <SfIcon :name="c.icon as any" :size="16" />
              <span>{{ c.label }}</span>
            </button>
          </div>

          <div class="ai-shortcuts">
            <button type="button" class="ai-shortcut" @click="bubbleInput = '今天工单情况如何？'; sendBubbleMessage()">
              # 今天工单情况如何？
            </button>
            <button v-if="active" type="button" class="ai-shortcut" @click="askAIForSuggestion">
              # 这条反馈怎么回复？
            </button>
            <button type="button" class="ai-shortcut" @click="bubbleInput = '最近有哪些热点诉求？'; sendBubbleMessage()">
              # 最近有哪些热点诉求？
            </button>
          </div>

          <div v-if="aiSuggestion" class="ai-suggestion">
            <div class="ai-suggestion-label">回复建议</div>
            <div>{{ aiSuggestion }}</div>
            <button v-if="active" type="button" class="btn sm primary" style="margin-top:8px;width:100%" @click="insertSuggestionToDraft">
              插入到草稿
            </button>
          </div>

          <div v-if="bubbleHistory.length" class="ai-history">
            <div class="ai-history-label">最近会话</div>
            <button
              v-for="(h, i) in bubbleHistory"
              :key="h.title"
              type="button"
              class="ai-history-item"
              @click="openBubbleHistory(i)"
            >
              <SfIcon name="chat" :size="12" />
              <span class="ai-history-title">{{ h.title }}</span>
              <SfIcon name="chevron-right" :size="12" class="ai-history-arrow" />
            </button>
          </div>
        </div>

        <!-- 聊天页 -->
        <div v-else class="ai-chat-body">
          <div class="ai-messages">
            <div v-for="(m, i) in bubbleMessages" :key="i" class="ai-msg" :class="m.role">
              <div class="ai-msg-bubble">{{ m.content }}</div>
            </div>
            <div v-if="bubbleLoading" class="ai-msg assistant">
              <div class="ai-msg-bubble ai-msg-loading">
                <span class="dot" /><span class="dot" /><span class="dot" />
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="ai-bubble-input-bar">
          <div class="ai-input-wrap">
            <input v-model="bubbleInput" type="text" placeholder="你可以这样问我：今天工单情况如何" @keyup.enter="sendBubbleMessage" />
            <button type="button" class="ai-send-btn" :disabled="bubbleLoading || !bubbleInput.trim()" @click="sendBubbleMessage">
              <SfIcon name="send" :size="16" />
            </button>
          </div>
          <div class="ai-mode-bar">
            <button type="button" class="ai-mode-btn" :class="{ active: bubbleMode === 'home' }" @click="bubbleMode = 'home'">
              <SfIcon name="magic" :size="12" /> 助手
            </button>
            <button type="button" class="ai-mode-btn" :class="{ active: bubbleMode === 'chat' }" @click="bubbleMode = 'chat'">
              <SfIcon name="chat" :size="12" /> 对话
            </button>
          </div>
        </div>

        <div class="ai-disclaimer">
          内容由 AI 生成，仅供参考，您据此所作判断及操作均由您自行承担责任。
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
.stats-bar {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: var(--sf-space-3);
}
@media (max-width: 1100px) {
  .stats-bar {
    grid-template-columns: repeat(3, 1fr);
  }
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
  height: 52px;
  padding: 10px var(--sf-space-2);
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

/* 回复内容区（统一展示：已回复 / AI草稿 / 空回复） */
.reply-section {
  padding: var(--sf-space-3);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-bg);
  border: 1px solid var(--sf-border);
}
.reply-section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-text-secondary);
  margin-bottom: var(--sf-space-2);
  flex-wrap: wrap;
}
.reply-section-header .reply-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  font-weight: 400;
  color: var(--sf-text-faint);
  font-size: var(--sf-font-12);
}
.reply-body {
  font-size: var(--sf-font-13);
  line-height: 1.6;
  color: var(--sf-text);
  white-space: pre-line;
  padding: var(--sf-space-2);
  background: var(--sf-success-soft);
  border-radius: var(--sf-radius-sm);
  border: 1px solid var(--sf-success);
}
.reply-body.empty {
  background: var(--sf-bg);
  border: 1px dashed var(--sf-border);
  color: var(--sf-text-faint);
  text-align: center;
  padding: var(--sf-space-4);
}

/* AI 草稿编辑区 */
.ai-draft-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
}
.ai-draft-textarea {
  width: 100%;
  min-height: 180px;
  padding: var(--sf-space-2);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text);
  font-size: var(--sf-font-13);
  line-height: 1.6;
  resize: vertical;
  font-family: inherit;
}
.ai-draft-footer {
  display: flex;
  gap: var(--sf-space-2);
  padding-top: var(--sf-space-2);
  border-top: 1px solid var(--sf-border);
  margin-top: var(--sf-space-1);
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
  width: 380px;
  max-height: 560px;
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  box-shadow: 0 8px 30px rgba(15, 23, 42, 0.12);
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  flex-shrink: 0;
}
.ai-bubble-body {
  padding: var(--sf-space-3) var(--sf-space-4);
  overflow-y: auto;
  flex: 1;
}
.ai-welcome {
  text-align: center;
  margin-bottom: var(--sf-space-3);
}
.ai-welcome-title {
  font-size: var(--sf-font-16);
  font-weight: 600;
  color: var(--sf-text);
  margin-bottom: 6px;
}
.ai-welcome-sub {
  margin: 0;
  font-size: var(--sf-font-13);
  color: var(--sf-text-secondary);
  line-height: 1.5;
}
.ai-categories {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sf-space-2);
  margin-bottom: var(--sf-space-3);
}
.ai-category {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: var(--sf-space-2) var(--sf-space-1);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text);
  font-size: var(--sf-font-12);
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}
.ai-category:hover {
  border-color: var(--sf-primary-border);
  background: var(--sf-primary-soft);
}
.ai-history {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: var(--sf-space-2);
  border-top: 1px solid var(--sf-border);
  padding-top: var(--sf-space-2);
}
.ai-history-label {
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-text-secondary);
  margin-bottom: 4px;
}
.ai-history-item {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 6px var(--sf-space-2);
  border: none;
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text-secondary);
  font-size: var(--sf-font-12);
  cursor: pointer;
  text-align: left;
  transition: background 0.15s ease, color 0.15s ease;
}
.ai-history-item:hover {
  background: var(--sf-primary-soft);
  color: var(--sf-primary);
}
.ai-history-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ai-history-arrow {
  color: var(--sf-text-faint);
}
.ai-shortcuts {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: var(--sf-space-3);
}
.ai-shortcut {
  text-align: left;
  padding: 6px var(--sf-space-2);
  border: none;
  border-radius: var(--sf-radius-sm);
  background: var(--sf-bg);
  color: var(--sf-primary);
  font-size: var(--sf-font-13);
  cursor: pointer;
  transition: background 0.15s ease;
}
.ai-shortcut:hover {
  background: var(--sf-primary-soft);
}
.ai-chat-body {
  padding: var(--sf-space-2) var(--sf-space-3);
  overflow-y: auto;
  flex: 1;
  min-height: 120px;
}
.ai-messages {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
}
.ai-msg {
  display: flex;
}
.ai-msg.user {
  justify-content: flex-end;
}
.ai-msg-bubble {
  max-width: 85%;
  padding: var(--sf-space-2) var(--sf-space-3);
  border-radius: var(--sf-radius-sm);
  font-size: var(--sf-font-13);
  line-height: 1.5;
  background: var(--sf-bg);
  color: var(--sf-text);
}
.ai-msg.user .ai-msg-bubble {
  background: var(--sf-primary);
  color: #fff;
}
.ai-msg-loading .dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--sf-text-faint);
  margin: 0 2px;
  animation: ai-dot 1.2s infinite ease-in-out both;
}
.ai-msg-loading .dot:nth-child(1) { animation-delay: 0s; }
.ai-msg-loading .dot:nth-child(2) { animation-delay: 0.2s; }
.ai-msg-loading .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes ai-dot {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
.ai-bubble-input-bar {
  padding: var(--sf-space-2) var(--sf-space-3);
  border-top: 1px solid var(--sf-border);
  flex-shrink: 0;
}
.ai-input-wrap {
  display: flex;
  gap: var(--sf-space-1);
  align-items: center;
}
.ai-input-wrap input {
  flex: 1;
  height: 36px;
  padding: 0 var(--sf-space-2);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text);
  font-size: var(--sf-font-13);
}
.ai-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--sf-radius-sm);
  background: var(--sf-primary);
  color: #fff;
  cursor: pointer;
}
.ai-send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.ai-mode-bar {
  display: flex;
  gap: var(--sf-space-2);
  margin-top: var(--sf-space-1);
}
.ai-mode-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border: 1px solid var(--sf-border);
  border-radius: 10px;
  background: var(--sf-surface);
  color: var(--sf-text-secondary);
  font-size: var(--sf-font-12);
  cursor: pointer;
}
.ai-mode-btn.active {
  border-color: var(--sf-primary);
  color: var(--sf-primary);
  background: var(--sf-primary-soft);
}
.ai-disclaimer {
  padding: 6px var(--sf-space-3);
  font-size: 11px;
  color: var(--sf-text-faint);
  text-align: center;
  border-top: 1px solid var(--sf-border);
  background: var(--sf-bg);
  line-height: 1.4;
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