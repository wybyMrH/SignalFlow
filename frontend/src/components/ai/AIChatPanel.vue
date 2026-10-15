<script setup lang="ts">
/**
 * AI 总览助手面板（重设计版）。
 * 参照浮动气泡助手（AIFloatingAssistant）结构：欢迎页 + 功能分类快捷入口 + 快捷指令 + 历史会话 + 助手/对话模式切换 + 免责声明。
 * 总览专属快捷指令：今日概览 / 异常提醒 / 自动化任务运行状态 / 客户访谈与合作意向。
 */
import { nextTick, onMounted, ref, watch } from 'vue'

import SfIcon from '@/components/common/SfIcon.vue'
import { useAIStore } from '@/stores/ai'

const ai = useAIStore()
const mode = ref<'home' | 'chat'>('home')
const input = ref('')
const scrollRef = ref<HTMLDivElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)

/** 总览专属功能分类快捷入口 */
const categories = [
  { label: '今日概览', icon: 'chart' },
  { label: '异常提醒', icon: 'alert' },
  { label: '自动化状态', icon: 'magic' },
  { label: '待办反馈', icon: 'checklist' },
  { label: '洞察摘要', icon: 'trend-up' },
  { label: '工作流', icon: 'refresh' },
]

/** 总览专属快捷指令 */
const shortcuts = ['今日概览', '异常提醒', '自动化任务运行状态', '客户访谈与合作意向']

/** 历史会话（本地会话记录） */
const history = ref<Array<{ title: string; messages: Array<{ role: 'user' | 'assistant'; content: string }> }>>([])

function scrollToBottom() {
  nextTick(() => {
    scrollRef.value?.scrollTo({ top: scrollRef.value.scrollHeight, behavior: 'smooth' })
  })
}

watch(() => ai.messages.length, scrollToBottom)

onMounted(() => {
  void ai.initChat()
  scrollToBottom()
})

async function sendMessage() {
  const text = input.value.trim()
  if (!text || ai.chatLoading) return
  mode.value = 'chat'
  input.value = ''
  await ai.sendMessage(text)
  // 记录为历史会话
  const title = text.length > 18 ? `${text.slice(0, 18)}…` : text
  const msgs = ai.messages.slice(-4).map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))
  const existing = history.value.findIndex((h) => h.title === title)
  const entry = { title, messages: msgs }
  if (existing >= 0) history.value[existing] = entry
  else history.value.unshift(entry)
  if (history.value.length > 8) history.value.length = 8
}

function openHistory(idx: number) {
  const h = history.value[idx]
  if (!h) return
  ai.messages = h.messages.map((m, i) => ({
    id: `msg-h-${idx}-${i}`,
    role: m.role,
    content: m.content,
    timestamp: new Date().toISOString(),
  }))
  mode.value = 'chat'
}

function usePrompt(text: string) {
  input.value = text
  void sendMessage()
}
</script>

<template>
  <div class="ai-panel">
    <div class="ai-header">
      <div class="ai-title">
        <div class="ai-avatar">
          <SfIcon name="logo" :size="16" />
        </div>
        <div>
          <div class="ai-name">AI 智能助手</div>
          <div class="ai-status">
            <span class="ai-dot" />
            在线 · 基于本地知识库
          </div>
        </div>
      </div>
    </div>

    <!-- 欢迎页（助手首页） -->
    <div v-if="mode === 'home'" class="ai-home">
      <div class="ai-welcome">
        <div class="ai-welcome-title">您好，欢迎使用总览助手</div>
        <p class="ai-welcome-sub">我可以帮您查看今日概览、异常提醒或自动化任务运行状态，汇总全局运营情况。</p>
      </div>

      <div class="ai-categories">
        <button
          v-for="c in categories"
          :key="c.label"
          type="button"
          class="ai-category"
          @click="usePrompt(c.label)"
        >
          <SfIcon :name="c.icon as any" :size="16" />
          <span>{{ c.label }}</span>
        </button>
      </div>

      <div class="ai-shortcuts">
        <button v-for="s in shortcuts" :key="s" type="button" class="ai-shortcut" @click="usePrompt(s)">
          # {{ s }}
        </button>
      </div>

      <div v-if="history.length" class="ai-history">
        <div class="ai-history-label">最近会话</div>
        <button
          v-for="(h, i) in history"
          :key="h.title"
          type="button"
          class="ai-history-item"
          @click="openHistory(i)"
        >
          <SfIcon name="chat" :size="12" />
          <span class="ai-history-title">{{ h.title }}</span>
          <SfIcon name="chevron-right" :size="12" class="ai-history-arrow" />
        </button>
      </div>
    </div>

    <!-- 对话页 -->
    <div v-else ref="scrollRef" class="ai-messages">
      <div
        v-for="msg in ai.messages"
        :key="msg.id"
        class="msg"
        :class="msg.role === 'user' ? 'msg-user' : 'msg-assistant'"
      >
        <div class="msg-bubble">
          <div class="msg-content">{{ msg.content }}</div>
          <div v-if="msg.sources?.length" class="msg-sources">
            <SfIcon name="link" :size="10" />
            来源：{{ msg.sources.join('、') }}
          </div>
        </div>
        <div class="msg-meta">{{ new Date(msg.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}</div>
      </div>

      <div v-if="ai.chatLoading" class="msg msg-assistant">
        <div class="msg-bubble typing">
          <span class="typing-dot" />
          <span class="typing-dot" />
          <span class="typing-dot" />
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="ai-input-bar">
      <input
        ref="inputRef"
        v-model="input"
        type="text"
        class="ai-input"
        placeholder="输入问题，例如「今日概览」..."
        @keydown.enter="sendMessage"
      />
      <button type="button" class="ai-send" :disabled="!input.trim() || ai.chatLoading" @click="sendMessage">
        <SfIcon name="send" :size="16" />
      </button>
    </div>

    <!-- 助手 / 对话模式切换 -->
    <div class="ai-mode-bar">
      <button type="button" class="ai-mode-btn" :class="{ active: mode === 'home' }" @click="mode = 'home'">
        <SfIcon name="magic" :size="12" /> 助手
      </button>
      <button type="button" class="ai-mode-btn" :class="{ active: mode === 'chat' }" @click="mode = 'chat'">
        <SfIcon name="chat" :size="12" /> 对话
      </button>
    </div>

    <div class="ai-disclaimer">
      内容由 AI 生成，仅供参考，您据此所作判断及操作均由您自行承担责任。
    </div>
  </div>
</template>

<style scoped>
.ai-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  overflow: hidden;
}
.ai-header {
  padding: var(--sf-space-3) var(--sf-space-4);
  border-bottom: 1px solid var(--sf-border);
  background: linear-gradient(135deg, var(--sf-primary-soft) 0%, transparent 100%);
  flex-shrink: 0;
}
.ai-title {
  display: flex;
  align-items: center;
  gap: var(--sf-space-3);
}
.ai-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--sf-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ai-name {
  font-size: var(--sf-font-14);
  font-weight: 600;
  color: var(--sf-text);
}
.ai-status {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
  display: flex;
  align-items: center;
  gap: 4px;
}
.ai-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--sf-success);
  display: inline-block;
}

/* 欢迎页 */
.ai-home {
  flex: 1;
  overflow-y: auto;
  padding: var(--sf-space-3) var(--sf-space-4);
  display: flex;
  flex-direction: column;
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

/* 对话页 */
.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--sf-space-3);
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
  min-height: 120px;
}
.msg {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.msg-user {
  align-items: flex-end;
}
.msg-assistant {
  align-items: flex-start;
}
.msg-bubble {
  max-width: 92%;
  padding: 10px 14px;
  border-radius: var(--sf-radius);
  font-size: var(--sf-font-13);
  line-height: 1.55;
  white-space: pre-line;
}
.msg-user .msg-bubble {
  background: var(--sf-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.msg-assistant .msg-bubble {
  background: var(--sf-bg);
  color: var(--sf-text);
  border: 1px solid var(--sf-border);
  border-bottom-left-radius: 4px;
}
.msg-content {
  word-break: break-word;
}
.msg-sources {
  margin-top: 6px;
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
  display: flex;
  align-items: center;
  gap: 4px;
}
.msg-meta {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
}
.typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 14px;
}
.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--sf-text-faint);
  animation: typing 1.2s infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

/* 输入区 */
.ai-input-bar {
  display: flex;
  gap: var(--sf-space-2);
  padding: var(--sf-space-2) var(--sf-space-3);
  border-top: 1px solid var(--sf-border);
  flex-shrink: 0;
}
.ai-input {
  flex: 1;
  padding: 8px 12px;
  border-radius: var(--sf-radius-sm);
  border: 1px solid var(--sf-border);
  background: var(--sf-bg);
  color: var(--sf-text);
  font-size: var(--sf-font-13);
  outline: none;
}
.ai-input:focus {
  border-color: var(--sf-primary);
}
.ai-send {
  width: 36px;
  height: 36px;
  border-radius: var(--sf-radius-sm);
  border: none;
  background: var(--sf-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: opacity 0.15s;
}
.ai-send:hover:not(:disabled) { opacity: 0.85; }
.ai-send:disabled { opacity: 0.4; cursor: not-allowed; }

/* 模式切换 */
.ai-mode-bar {
  display: flex;
  gap: var(--sf-space-2);
  padding: 0 var(--sf-space-3) var(--sf-space-2);
  flex-shrink: 0;
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
  flex-shrink: 0;
}
</style>