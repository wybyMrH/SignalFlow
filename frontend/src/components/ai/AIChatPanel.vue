<script setup lang="ts">
/**
 * AI 对话面板：常驻侧边/可折叠的 AI 助手。
 * 参考 Ant Design X / Page Assist 的 RICH 交互范式：
 * 气泡对话 + 快捷提示词 + 发送器 + 引用来源展示。
 */
import { nextTick, onMounted, ref, watch } from 'vue'

import SfIcon from '@/components/common/SfIcon.vue'
import { useAIStore } from '@/stores/ai'

const ai = useAIStore()
const input = ref('')
const scrollRef = ref<HTMLDivElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)

const quickPrompts = [
  '今天工单情况如何？',
  '最近有什么高频问题？',
  '自动回复怎么配置？',
  '大厅排队怎么解决？',
]

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

async function submit() {
  const q = input.value.trim()
  if (!q || ai.chatLoading) return
  input.value = ''
  await ai.sendMessage(q)
}

function usePrompt(p: string) {
  input.value = p
  inputRef.value?.focus()
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

    <div ref="scrollRef" class="ai-messages">
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

    <div class="ai-prompts">
      <button
        v-for="p in quickPrompts"
        :key="p"
        type="button"
        class="prompt-chip"
        @click="usePrompt(p)"
      >
        {{ p }}
      </button>
    </div>

    <div class="ai-input-bar">
      <input
        ref="inputRef"
        v-model="input"
        type="text"
        class="ai-input"
        placeholder="输入问题，例如「今天工单情况如何」..."
        @keydown.enter="submit"
      />
      <button type="button" class="ai-send" :disabled="!input.trim() || ai.chatLoading" @click="submit">
        <SfIcon name="send" :size="16" />
      </button>
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

.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--sf-space-3);
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
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

.ai-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sf-space-2);
  padding: var(--sf-space-2) var(--sf-space-3);
  border-top: 1px solid var(--sf-border);
}
.prompt-chip {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--sf-border);
  background: var(--sf-bg);
  color: var(--sf-text-secondary);
  font-size: var(--sf-font-12);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.prompt-chip:hover {
  border-color: var(--sf-primary-border);
  color: var(--sf-primary);
  background: var(--sf-primary-soft);
}

.ai-input-bar {
  display: flex;
  gap: var(--sf-space-2);
  padding: var(--sf-space-3);
  border-top: 1px solid var(--sf-border);
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
</style>
