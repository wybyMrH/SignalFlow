<script setup lang="ts">
/**
 * 可复用的 AI 浮动气泡助手。
 * 参考 FeedbackListPage 气泡助手结构：欢迎页 + 功能分类快捷入口 + 历史会话 + Agent/Chat 模式切换 + 免责声明。
 * 通过 props 传入页面上下文与预设问题，实现各页面差异化快捷指令。
 */
import { ref } from 'vue'

import SfIcon from '@/components/common/SfIcon.vue'
import { useAIStore } from '@/stores/ai'

const props = defineProps<{
  /** 页面上下文标识，决定预设问题与欢迎文案 */
  context:
    | 'feedback'
    | 'insights'
    | 'roadmap'
    | 'gov'
    | 'automation'
    | 'business'
    | 'interview'
    | 'agents'
    | 'resources'
    | 'workflows'
    | 'dashboard'
}>()

const ai = useAIStore()

const open = ref(false)
const mode = ref<'home' | 'chat'>('home')
const input = ref('')
const loading = ref(false)

const contextConfig = {
  feedback: {
    title: '反馈助手',
    welcome: '我可以帮您批量生成回复草稿、按优先级筛选建议或查看 AI 自动审批说明。',
    categories: [
      { label: '批量回复', icon: 'chat' },
      { label: '优先级筛选', icon: 'alert' },
      { label: '自动审批', icon: 'check' },
      { label: '分类统计', icon: 'label' },
      { label: '情感分析', icon: 'sentiment' },
      { label: '去重合并', icon: 'filter' },
    ],
    shortcuts: [
      '批量生成待办回复',
      '按优先级筛选建议',
      'AI 自动审批怎么配置？',
    ],
  },
  insights: {
    title: '洞察助手',
    welcome: '我可以帮您生成本周数据摘要、分析热门主题趋势或查看客户情感分布。',
    categories: [
      { label: '数据摘要', icon: 'chart' },
      { label: '主题趋势', icon: 'trend-up' },
      { label: '情感分布', icon: 'sentiment' },
      { label: '来源分析', icon: 'target' },
      { label: '痛点识别', icon: 'alert' },
      { label: '预测建议', icon: 'magic' },
    ],
    shortcuts: [
      '生成本周数据摘要',
      '热门主题趋势分析',
      '客户情感分布如何？',
    ],
  },
  roadmap: {
    title: '路线助手',
    welcome: '我可以帮您查看任务进度、生成回复草稿或了解回传状态说明。',
    categories: [
      { label: '任务进度', icon: 'checklist' },
      { label: '生成草稿', icon: 'chat' },
      { label: '回传状态', icon: 'refresh' },
      { label: '审批流程', icon: 'shield' },
      { label: '优先级', icon: 'alert' },
      { label: '版本规划', icon: 'clock' },
    ],
    shortcuts: [
      '查看任务进度',
      '生成回复草稿',
      '回传状态说明',
    ],
  },
  gov: {
    title: '政务助手',
    welcome: '我可以帮您查看热点诉求摘要、督办事项提醒或舆情预警分析。',
    categories: [
      { label: '热点诉求', icon: 'chat' },
      { label: '督办事项', icon: 'checklist' },
      { label: '舆情预警', icon: 'alert' },
      { label: '区域分布', icon: 'map' },
      { label: '政策告知', icon: 'shield' },
      { label: '审计留痕', icon: 'file' },
    ],
    shortcuts: [
      '热点诉求摘要',
      '督办事项提醒',
      '舆情预警分析',
    ],
  },
  automation: {
    title: '自动化助手',
    welcome: '我可以帮您查看自动分类结果、去重组群或了解优先级规则说明。',
    categories: [
      { label: '自动分类', icon: 'label' },
      { label: '去重组群', icon: 'filter' },
      { label: '优先级规则', icon: 'alert' },
      { label: '调整记录', icon: 'refresh' },
      { label: '置信度', icon: 'chart' },
      { label: '规则配置', icon: 'settings' },
    ],
    shortcuts: [
      '自动分类结果如何？',
      '去重组群查看',
      '优先级规则说明',
    ],
  },
  business: {
    title: '商务助手',
    welcome: '我可以帮您提供线索跟进建议、行业分布分析或市场动向总结。',
    categories: [
      { label: '线索跟进', icon: 'target' },
      { label: '行业分析', icon: 'industry' },
      { label: '市场动向', icon: 'trend-up' },
      { label: '共性需求', icon: 'need' },
      { label: '企业画像', icon: 'shield' },
      { label: '商机推送', icon: 'send' },
    ],
    shortcuts: [
      '线索跟进建议',
      '行业分布分析',
      '市场动向总结',
    ],
  },
  interview: {
    title: '访谈助手',
    welcome: '我可以帮您从访谈纪要中提炼客户痛点与需求、识别合作意向并联动商务线索。',
    categories: [
      { label: '痛点提炼', icon: 'alert' },
      { label: '需求归纳', icon: 'need' },
      { label: '意向识别', icon: 'target' },
      { label: '线索生成', icon: 'send' },
      { label: '纪要摘要', icon: 'file' },
      { label: '跟进建议', icon: 'chat' },
    ],
    shortcuts: [
      '最近访谈要点摘要',
      '哪些访谈可生成线索？',
      '客户痛点匹配了什么需求？',
    ],
  },
  agents: {
    title: 'Agent 助手',
    welcome: '我可以帮您了解 Agent 能力、推荐可用的工具与工作流绑定，或解释启停影响。',
    categories: [
      { label: '能力清单', icon: 'agent' },
      { label: '工具推荐', icon: 'magic' },
      { label: '工作流绑定', icon: 'workflow' },
      { label: '启停影响', icon: 'alert' },
      { label: '新建 Agent', icon: 'plus' },
      { label: '运行统计', icon: 'chart' },
    ],
    shortcuts: [
      '目前有哪些 Agent？',
      '给商单回复 Agent 推荐工具',
      '禁用 Agent 会有什么影响？',
    ],
  },
  resources: {
    title: '运维助手',
    welcome: '我可以帮您查看资源健康、定位异常告警、检索系统日志或解释状态指标。',
    categories: [
      { label: '健康概览', icon: 'server' },
      { label: '数据库状态', icon: 'database' },
      { label: 'API 状态', icon: 'link' },
      { label: '异常告警', icon: 'alert' },
      { label: '日志检索', icon: 'file' },
      { label: '处置建议', icon: 'chat' },
    ],
    shortcuts: [
      '当前有哪些告警？',
      '检索最近的错误日志',
      '哪些 API 需要关注？',
    ],
  },
  workflows: {
    title: '工作流助手',
    welcome: '我可以帮您理解工作流节点、配置触发条件、绑定 Agent 与工具链，或查看运行历史。',
    categories: [
      { label: '工作流模板', icon: 'workflow' },
      { label: '节点说明', icon: 'magic' },
      { label: '触发条件', icon: 'alert' },
      { label: 'Agent 绑定', icon: 'agent' },
      { label: '工具链', icon: 'chat' },
      { label: '运行历史', icon: 'clock' },
    ],
    shortcuts: [
      '发布公告工作流怎么跑？',
      '如何绑定 Agent 到工作流节点？',
      '查看工作流运行异常',
    ],
  },
  dashboard: {
    title: '总览助手',
    welcome: '我可以帮您查看今日概览、异常提醒或自动化任务运行状态。',
    categories: [
      { label: '今日概览', icon: 'chart' },
      { label: '异常提醒', icon: 'alert' },
      { label: '自动化状态', icon: 'magic' },
      { label: '待办反馈', icon: 'checklist' },
      { label: '洞察摘要', icon: 'trend-up' },
      { label: '工作流', icon: 'refresh' },
    ],
    shortcuts: [
      '今日概览',
      '异常提醒',
      '自动化任务运行状态',
    ],
  },
}

const cfg = contextConfig[props.context]

/** 历史会话（本地会话记录） */
const history = ref<Array<{ title: string; messages: Array<{ role: 'user' | 'assistant'; content: string }> }>>([])

function sendMessage() {
  const text = input.value.trim()
  if (!text || loading.value) return
  mode.value = 'chat'
  ai.messages.push({ id: `msg-u-${Date.now()}`, role: 'user', content: text, timestamp: new Date().toISOString() })
  input.value = ''
  loading.value = true
  ai.sendMessage(text).finally(() => {
    loading.value = false
    // 记录为历史会话
    const title = text.length > 18 ? `${text.slice(0, 18)}…` : text
    const msgs = ai.messages.slice(-4).map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))
    const existing = history.value.findIndex((h) => h.title === title)
    const entry = { title, messages: msgs }
    if (existing >= 0) history.value[existing] = entry
    else history.value.unshift(entry)
    if (history.value.length > 8) history.value.length = 8
  })
}

function openHistory(idx: number) {
  const h = history.value[idx]
  if (!h) return
  // 恢复历史消息到当前对话
  ai.messages = h.messages.map((m, i) => ({
    id: `msg-h-${idx}-${i}`,
    role: m.role,
    content: m.content,
    timestamp: new Date().toISOString(),
  }))
  mode.value = 'chat'
}

function useCategory(label: string) {
  input.value = label
  sendMessage()
}

function useShortcut(text: string) {
  input.value = text
  sendMessage()
}
</script>

<template>
  <div class="ai-float" :class="{ open }">
    <button type="button" class="ai-float-trigger" @click="open = !open">
      <SfIcon :name="open ? 'close' : 'logo'" :size="20" />
    </button>
    <div v-if="open" class="ai-float-panel">
      <div class="ai-float-head">
        <SfIcon name="logo" :size="14" />
        <span>SignalFlow {{ cfg.title }}</span>
        <button type="button" class="btn ghost sm" style="margin-left:auto" @click="open = false">
          <SfIcon name="close" :size="14" />
        </button>
      </div>

      <!-- 欢迎页 -->
      <div v-if="mode === 'home'" class="ai-float-body">
        <div class="ai-welcome">
          <div class="ai-welcome-title">您好，欢迎使用 {{ cfg.title }}</div>
          <p class="ai-welcome-sub">{{ cfg.welcome }}</p>
        </div>

        <div class="ai-categories">
          <button
            v-for="c in cfg.categories"
            :key="c.label"
            type="button"
            class="ai-category"
            @click="useCategory(c.label)"
          >
            <SfIcon :name="c.icon as any" :size="16" />
            <span>{{ c.label }}</span>
          </button>
        </div>

        <div class="ai-shortcuts">
          <button v-for="s in cfg.shortcuts" :key="s" type="button" class="ai-shortcut" @click="useShortcut(s)">
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

      <!-- 聊天页 -->
      <div v-else class="ai-chat-body">
        <div class="ai-messages">
          <div v-for="(m, i) in ai.messages" :key="i" class="ai-msg" :class="m.role">
            <div class="ai-msg-bubble">
              <div class="msg-content">{{ m.content }}</div>
              <div v-if="m.sources?.length" class="msg-sources">
                <SfIcon name="link" :size="10" />
                来源：{{ m.sources.join('、') }}
              </div>
            </div>
            <div class="msg-meta">{{ new Date(m.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}</div>
          </div>
          <div v-if="loading || ai.chatLoading" class="ai-msg assistant">
            <div class="ai-msg-bubble ai-msg-loading">
              <span class="dot" /><span class="dot" /><span class="dot" />
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="ai-float-input-bar">
        <div class="ai-input-wrap">
          <input v-model="input" type="text" placeholder="你可以这样问我..." @keyup.enter="sendMessage" />
          <button type="button" class="ai-send-btn" :disabled="loading || ai.chatLoading || !input.trim()" @click="sendMessage">
            <SfIcon name="send" :size="16" />
          </button>
        </div>
        <div class="ai-mode-bar">
          <button type="button" class="ai-mode-btn" :class="{ active: mode === 'home' }" @click="mode = 'home'">
            <SfIcon name="magic" :size="12" /> 助手
          </button>
          <button type="button" class="ai-mode-btn" :class="{ active: mode === 'chat' }" @click="mode = 'chat'">
            <SfIcon name="chat" :size="12" /> 对话
          </button>
        </div>
      </div>

      <div class="ai-disclaimer">
        内容由 AI 生成，仅供参考，您据此所作判断及操作均由您自行承担责任。
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-float {
  position: fixed;
  right: var(--sf-space-4);
  bottom: var(--sf-space-4);
  z-index: 50;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--sf-space-2);
}
.ai-float-trigger {
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
.ai-float-trigger:hover {
  transform: scale(1.05);
}
.ai-float-panel {
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
.ai-float-head {
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
.ai-float-body {
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

/* 聊天页 */
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
  flex-direction: column;
  gap: 2px;
}
.ai-msg.user {
  align-items: flex-end;
}
.ai-msg.assistant {
  align-items: flex-start;
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
  border-bottom-right-radius: 4px;
}
.ai-msg.assistant .ai-msg-bubble {
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

/* 输入区 */
.ai-float-input-bar {
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

/* 按钮 */
.btn.ghost {
  background: transparent;
  border: none;
  color: var(--sf-text-faint);
  cursor: pointer;
}
.btn.ghost:hover {
  color: var(--sf-text);
}
.btn.sm {
  height: 26px;
  padding: 0 var(--sf-space-2);
  font-size: var(--sf-font-12);
}
</style>
