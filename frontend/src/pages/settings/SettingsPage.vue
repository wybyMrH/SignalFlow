<script setup lang="ts">
/**
 * FS-7 系统设置：渠道接入 + API 配置 + 服务器配置 + 邮件提醒 + AI 主题 +
 * 全局模型参数 + Agent 角色提示词管理。
 *
 * 设计原则：
 * - 配置项分区展示，每区独立编辑/保存，避免长表单心理负担。
 * - 敏感字段（API Key / 密码）只回显掩码，留空提交表示不修改。
 * - 渠道状态支持一键启停；未连通/未启用的渠道给出可操作的说明。
 * - Agent 提示词在设置页即可快速预览与编辑，无需跳转到 Agent 配置中心。
 */
import { onMounted, ref } from 'vue'

import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SfIcon from '@/components/common/SfIcon.vue'
import Drawer from '@/components/common/Drawer.vue'
import {
  fetchSettingsView,
  updateLLMConfig,
  updateEmailConfig,
  updateAppearanceConfig,
  updateGlobalModelParams,
  updateServerConfig,
  updateNotesConfig,
  toggleChannel,
} from '@/api/settings'
import { updateAgentScenario } from '@/api/agents'
import AIFloatingAssistant from '@/components/ai/AIFloatingAssistant.vue'
import type { SettingsView, AgentPromptConfig } from '@/types'
import { formatDateTime } from '@/utils'

const view = ref<SettingsView | null>(null)
const loading = ref(false)
const saving = ref<Record<string, boolean>>({})
const message = ref('')
const messageTimer = ref<number | null>(null)

function showMsg(text: string) {
  message.value = text
  if (messageTimer.value) window.clearTimeout(messageTimer.value)
  messageTimer.value = window.setTimeout(() => {
    message.value = ''
  }, 3000)
}

onMounted(async () => {
  loading.value = true
  try {
    view.value = await fetchSettingsView()
  } finally {
    loading.value = false
  }
})

// ──────────────────────────────────────────────
// 渠道启停
// ──────────────────────────────────────────────

async function handleToggleChannel(key: string) {
  if (!view.value) return
  saving.value[`channel-${key}`] = true
  try {
    const res = await toggleChannel(key)
    const ch = view.value.channels.find((c) => c.key === key)
    if (ch && res.data) {
      ch.enabled = res.data.enabled
    }
    showMsg(res.message)
  } catch (e: any) {
    showMsg(e?.response?.data?.message || '渠道切换失败')
  } finally {
    saving.value[`channel-${key}`] = false
  }
}

// ──────────────────────────────────────────────
// LLM / API 配置编辑
// ──────────────────────────────────────────────

const llmEdit = ref({
  provider: '',
  model: '',
  api_key: '',
  temperature: 0.2,
  max_tokens: 2048,
  timeout_seconds: 60,
})
const llmEditing = ref(false)

function openLLMEdit() {
  if (!view.value) return
  llmEdit.value = {
    provider: view.value.llm.provider,
    model: view.value.llm.model,
    api_key: '',
    temperature: view.value.llm.temperature,
    max_tokens: view.value.llm.max_tokens,
    timeout_seconds: view.value.llm.timeout_seconds,
  }
  llmEditing.value = true
}

async function saveLLM() {
  if (!view.value) return
  saving.value.llm = true
  try {
    const payload: Record<string, any> = {
      provider: llmEdit.value.provider,
      model: llmEdit.value.model,
      temperature: llmEdit.value.temperature,
      max_tokens: llmEdit.value.max_tokens,
      timeout_seconds: llmEdit.value.timeout_seconds,
    }
    if (llmEdit.value.api_key.trim()) {
      payload.api_key = llmEdit.value.api_key.trim()
    }
    await updateLLMConfig(payload)
    view.value.llm = { ...view.value.llm, ...payload }
    if (llmEdit.value.api_key.trim()) {
      view.value.llm.api_key_mask = '••••••' + llmEdit.value.api_key.slice(-4)
    }
    llmEditing.value = false
    showMsg('LLM 配置已保存')
  } catch (e: any) {
    showMsg(e?.response?.data?.message || '保存失败')
  } finally {
    saving.value.llm = false
  }
}

// ──────────────────────────────────────────────
// 邮件配置编辑
// ──────────────────────────────────────────────

const emailEdit = ref({
  enabled: false,
  smtp_server: '',
  smtp_port: 587,
  sender: '',
  password: '',
})
const emailEditing = ref(false)

function openEmailEdit() {
  if (!view.value) return
  emailEdit.value = {
    enabled: view.value.email.enabled,
    smtp_server: view.value.email.smtp_server,
    smtp_port: view.value.email.smtp_port,
    sender: view.value.email.sender,
    password: '',
  }
  emailEditing.value = true
}

async function saveEmail() {
  if (!view.value) return
  saving.value.email = true
  try {
    const payload: Record<string, any> = {
      enabled: emailEdit.value.enabled,
      smtp_server: emailEdit.value.smtp_server,
      smtp_port: emailEdit.value.smtp_port,
      sender: emailEdit.value.sender,
    }
    if (emailEdit.value.password.trim()) {
      payload.password = emailEdit.value.password.trim()
    }
    await updateEmailConfig(payload)
    view.value.email = { ...view.value.email, ...payload }
    if (emailEdit.value.password.trim()) {
      view.value.email.password_mask = '••••••'
    }
    emailEditing.value = false
    showMsg('邮件配置已保存')
  } catch (e: any) {
    showMsg(e?.response?.data?.message || '保存失败')
  } finally {
    saving.value.email = false
  }
}

// ──────────────────────────────────────────────
// 外观 / AI 气泡主题
// ──────────────────────────────────────────────

const themeOptions = [
  { value: 'blue', label: '科技蓝（默认）' },
  { value: 'purple', label: '静谧紫' },
  { value: 'green', label: '生机绿' },
  { value: 'orange', label: '温暖橙' },
  { value: 'dark', label: '深色模式' },
]

const themeEditing = ref(false)
const themeEdit = ref('blue')

function openThemeEdit() {
  if (!view.value) return
  themeEdit.value = view.value.appearance.ai_bubble_theme
  themeEditing.value = true
}

async function saveTheme() {
  if (!view.value) return
  saving.value.theme = true
  try {
    await updateAppearanceConfig({ ai_bubble_theme: themeEdit.value })
    view.value.appearance.ai_bubble_theme = themeEdit.value
    themeEditing.value = false
    showMsg('主题已更新')
  } catch (e: any) {
    showMsg(e?.response?.data?.message || '保存失败')
  } finally {
    saving.value.theme = false
  }
}

// ──────────────────────────────────────────────
// 全局模型参数
// ──────────────────────────────────────────────

const globalEdit = ref({ context_window: 4096, tone: 'professional' })
const globalEditing = ref(false)

const toneOptions = [
  { value: 'professional', label: '专业严谨' },
  { value: 'friendly', label: '亲切友好' },
  { value: 'concise', label: '简洁直接' },
  { value: 'empathetic', label: '共情安抚' },
  { value: 'formal', label: '正式书面' },
]

function openGlobalEdit() {
  if (!view.value) return
  globalEdit.value = {
    context_window: view.value.global_model_params.context_window,
    tone: view.value.global_model_params.tone,
  }
  globalEditing.value = true
}

async function saveGlobal() {
  if (!view.value) return
  saving.value.global = true
  try {
    await updateGlobalModelParams({
      context_window: globalEdit.value.context_window,
      tone: globalEdit.value.tone,
    })
    view.value.global_model_params = { ...globalEdit.value }
    globalEditing.value = false
    showMsg('全局模型参数已保存')
  } catch (e: any) {
    showMsg(e?.response?.data?.message || '保存失败')
  } finally {
    saving.value.global = false
  }
}

// ──────────────────────────────────────────────
// 服务器配置编辑（日志级别）
// ──────────────────────────────────────────────

const logLevelOptions = ['DEBUG', 'INFO', 'WARNING', 'ERROR']

const serverEditing = ref(false)
const serverEdit = ref('INFO')

function openServerEdit() {
  if (!view.value) return
  serverEdit.value = view.value.server.log_level || 'INFO'
  serverEditing.value = true
}

async function saveServer() {
  if (!view.value) return
  saving.value.server = true
  try {
    await updateServerConfig({ log_level: serverEdit.value })
    view.value.server.log_level = serverEdit.value
    serverEditing.value = false
    showMsg('服务器配置已保存')
  } catch (e: any) {
    showMsg(e?.response?.data?.message || '保存失败')
  } finally {
    saving.value.server = false
  }
}

// ──────────────────────────────────────────────
// 数据源与权限说明编辑
// ──────────────────────────────────────────────

const notesEditing = ref(false)
const notesEdit = ref({ ai_note: '', auth_note: '' })

function openNotesEdit() {
  if (!view.value) return
  notesEdit.value = {
    ai_note: view.value.ai_note || '',
    auth_note: view.value.auth_note || '',
  }
  notesEditing.value = true
}

async function saveNotes() {
  if (!view.value) return
  saving.value.notes = true
  try {
    await updateNotesConfig({
      ai_note: notesEdit.value.ai_note,
      auth_note: notesEdit.value.auth_note,
    })
    view.value.ai_note = notesEdit.value.ai_note
    view.value.auth_note = notesEdit.value.auth_note
    notesEditing.value = false
    showMsg('数据源与权限说明已保存')
  } catch (e: any) {
    showMsg(e?.response?.data?.message || '保存失败')
  } finally {
    saving.value.notes = false
  }
}

// ──────────────────────────────────────────────
// Agent 角色提示词编辑
// ──────────────────────────────────────────────

const promptDrawerOpen = ref(false)
const promptEditAgent = ref<AgentPromptConfig | null>(null)
const promptEditText = ref('')

function openPromptEdit(agent: AgentPromptConfig) {
  promptEditAgent.value = agent
  promptEditText.value = agent.scenario
  promptDrawerOpen.value = true
}

async function savePrompt() {
  if (!view.value || !promptEditAgent.value) return
  const agentId = promptEditAgent.value.id
  saving.value[`prompt-${agentId}`] = true
  try {
    await updateAgentScenario(agentId, promptEditText.value)
    const target = view.value.agent_prompts.find((a) => a.id === agentId)
    if (target) target.scenario = promptEditText.value
    promptDrawerOpen.value = false
    showMsg('Agent 提示词已更新')
  } catch (e: any) {
    showMsg(e?.response?.data?.message || '保存失败')
  } finally {
    saving.value[`prompt-${agentId}`] = false
  }
}
</script>

<template>
  <div class="st">
    <!-- 顶部消息条 -->
    <div v-if="message" class="msg-bar">
      <SfIcon name="check" :size="14" />
      <span>{{ message }}</span>
    </div>

    <Skeleton v-if="loading" :rows="12" />

    <template v-else-if="view">
      <!-- 渠道接入 -->
      <section class="card span-2">
        <div class="head">
          <h2 class="title">渠道接入</h2>
          <span class="sub">数据源连通状态与启停控制</span>
        </div>
        <table class="tbl">
          <thead>
            <tr>
              <th>渠道</th>
              <th>状态</th>
              <th>今日接入</th>
              <th>最近同步</th>
              <th>说明</th>
              <th style="width: 72px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in view.channels" :key="c.key">
              <td class="nowrap">{{ c.label }}</td>
              <td class="nowrap">
                <StatusBadge
                  :label="!c.enabled ? '未启用' : c.connected ? '已接通' : '未连通'"
                  :tone="!c.enabled ? 'muted' : c.connected ? 'success' : 'warning'"
                />
              </td>
              <td class="num">{{ c.incoming }}</td>
              <td class="nowrap dim">{{ c.last_sync ? formatDateTime(c.last_sync) : '—' }}</td>
              <td class="dim">{{ c.note }}</td>
              <td>
                <button
                  type="button"
                  class="btn micro"
                  :class="c.enabled ? 'danger-ghost' : 'primary-ghost'"
                  :disabled="saving[`channel-${c.key}`]"
                  @click="handleToggleChannel(c.key)"
                >
                  {{ c.enabled ? '停用' : '启用' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <p class="hint">
          <SfIcon name="info" :size="12" />
          未连通 = 已启用但尚未建立数据同步；未启用 = 渠道已关闭，不再接收新反馈。
        </p>
      </section>

      <!-- API / LLM 配置 -->
      <section class="card">
        <div class="head">
          <h2 class="title">API / LLM 配置</h2>
          <span class="sub">大模型网关连接参数</span>
        </div>
        <dl class="kv">
          <dt>提供商</dt>
          <dd>{{ view.llm.provider }}</dd>
          <dt>模型</dt>
          <dd>{{ view.llm.model }}</dd>
          <dt>API Key</dt>
          <dd>{{ view.llm.api_key_mask || '未配置' }}</dd>
          <dt>温度</dt>
          <dd>{{ view.llm.temperature }}</dd>
          <dt>最大 Token</dt>
          <dd>{{ view.llm.max_tokens }}</dd>
          <dt>超时</dt>
          <dd>{{ view.llm.timeout_seconds }} 秒</dd>
        </dl>
        <div class="actions">
          <button type="button" class="btn ghost" @click="openLLMEdit">
            <SfIcon name="edit" :size="13" /> 编辑
          </button>
        </div>
      </section>

      <!-- 服务器配置 -->
      <section class="card">
        <div class="head">
          <h2 class="title">服务器配置</h2>
          <span class="sub">运行环境与基础参数</span>
        </div>
        <dl class="kv">
          <dt>运行环境</dt>
          <dd>
            <StatusBadge :label="view.server.app_env" tone="info" />
          </dd>
          <dt>监听地址</dt>
          <dd>{{ view.server.app_host }}:{{ view.server.app_port }}</dd>
          <dt>日志级别</dt>
          <dd>{{ view.server.log_level }}</dd>
          <dt>数据模式</dt>
          <dd>
            <StatusBadge
              :label="view.mock_mode ? '模拟数据' : '真实后端'"
              :tone="view.mock_mode ? 'warning' : 'success'"
            />
          </dd>
        </dl>
        <div class="actions">
          <button type="button" class="btn ghost" @click="openServerEdit">
            <SfIcon name="edit" :size="13" /> 编辑
          </button>
        </div>
        <p class="hint">
          <SfIcon name="info" :size="12" />
          运行环境与监听地址为启动级参数（改 .env），日志级别可在页内调整。
        </p>
      </section>

      <!-- 邮件提醒 -->
      <section class="card">
        <div class="head">
          <h2 class="title">邮件提醒</h2>
          <span class="sub">告警与通知推送通道</span>
        </div>
        <dl class="kv">
          <dt>启用状态</dt>
          <dd>
            <StatusBadge
              :label="view.email.enabled ? '已启用' : '未启用'"
              :tone="view.email.enabled ? 'success' : 'muted'"
            />
          </dd>
          <dt>SMTP 服务器</dt>
          <dd>{{ view.email.smtp_server || '—' }}</dd>
          <dt>端口</dt>
          <dd>{{ view.email.smtp_port }}</dd>
          <dt>发件人</dt>
          <dd>{{ view.email.sender || '—' }}</dd>
          <dt>密码</dt>
          <dd>{{ view.email.password_mask || '—' }}</dd>
        </dl>
        <div class="actions">
          <button type="button" class="btn ghost" @click="openEmailEdit">
            <SfIcon name="edit" :size="13" /> 编辑
          </button>
        </div>
      </section>

      <!-- AI 气泡主题 -->
      <section class="card">
        <div class="head">
          <h2 class="title">AI 气泡主题</h2>
          <span class="sub">界面氛围与助手视觉风格</span>
        </div>
        <div class="theme-row">
          <div class="theme-preview" :class="view.appearance.ai_bubble_theme">
            <div class="bubble">你好，我是 SignalFlow AI 助手</div>
          </div>
          <div class="theme-info">
            <div class="theme-name">
              {{ themeOptions.find((t) => t.value === view?.appearance.ai_bubble_theme)?.label || view?.appearance.ai_bubble_theme || '默认' }}
            </div>
            <div class="theme-desc">
              当前主题影响 AI 浮窗、对话气泡与辅助提示的视觉配色。
            </div>
          </div>
        </div>
        <div class="actions">
          <button type="button" class="btn ghost" @click="openThemeEdit">
            <SfIcon name="palette" :size="13" /> 切换主题
          </button>
        </div>
      </section>

      <!-- 全局模型参数 -->
      <section class="card">
        <div class="head">
          <h2 class="title">全局模型参数</h2>
          <span class="sub">上下文窗口与生成语气</span>
        </div>
        <dl class="kv">
          <dt>上下文窗口</dt>
          <dd>{{ view.global_model_params.context_window }}</dd>
          <dt>生成语气</dt>
          <dd>
            {{ toneOptions.find((t) => t.value === view?.global_model_params.tone)?.label || view?.global_model_params.tone || '标准' }}
          </dd>
        </dl>
        <div class="actions">
          <button type="button" class="btn ghost" @click="openGlobalEdit">
            <SfIcon name="edit" :size="13" /> 编辑
          </button>
        </div>
      </section>

      <!-- 数据源与权限说明 -->
      <section class="card note">
        <div class="head">
          <h3 class="title">数据源与权限说明</h3>
          <button type="button" class="btn micro ghost" @click="openNotesEdit">
            <SfIcon name="edit" :size="12" /> 编辑
          </button>
        </div>
        <dl class="kv">
          <dt>数据源</dt>
          <dd>{{ view.mock_mode ? '使用模拟数据（VITE_USE_MOCK 默认开启）' : '使用真实后端接口' }}</dd>
          <dt>AI 洞察</dt>
          <dd>{{ view.ai_note }}</dd>
          <dt>身份认证</dt>
          <dd>{{ view.auth_note }}</dd>
        </dl>
      </section>

      <!-- Agent 角色提示词 -->
      <section class="card span-2">
        <div class="head">
          <h2 class="title">Agent 角色提示词</h2>
          <span class="sub">快速调整各 Agent 的角色定义与场景边界</span>
        </div>
        <div class="agent-prompt-list">
          <div
            v-for="a in view.agent_prompts"
            :key="a.id"
            class="agent-prompt-item"
            :class="{ disabled: !a.enabled }"
          >
            <div class="prompt-head">
              <div class="prompt-name">
                <SfIcon name="agent" :size="14" />
                <span>{{ a.name }}</span>
                <StatusBadge :label="a.category || '—'" tone="info" />
                <StatusBadge v-if="!a.enabled" label="已停用" tone="muted" />
              </div>
              <button type="button" class="btn micro ghost" @click="openPromptEdit(a)">
                <SfIcon name="edit" :size="12" /> 编辑
              </button>
            </div>
            <p class="prompt-text">{{ a.scenario || '未配置提示词' }}</p>
          </div>
        </div>
        <p class="hint">
          <SfIcon name="info" :size="12" />
          提示词修改即时生效，影响该 Agent 在自动分类、回复生成与趋势研判中的行为边界。
        </p>
      </section>
    </template>

    <!-- LLM 编辑抽屉 -->
    <Drawer :open="llmEditing" title="编辑 LLM 配置" @close="llmEditing = false">
      <form class="drawer-form" @submit.prevent="saveLLM">
        <label class="field">
          <span class="field-label">提供商</span>
          <input v-model="llmEdit.provider" type="text" required />
        </label>
        <label class="field">
          <span class="field-label">模型</span>
          <input v-model="llmEdit.model" type="text" required />
        </label>
        <label class="field">
          <span class="field-label">API Key</span>
          <input v-model="llmEdit.api_key" type="password" placeholder="留空表示不修改" />
          <span class="field-hint">当前：{{ view?.llm.api_key_mask || '未配置' }}</span>
        </label>
        <label class="field">
          <span class="field-label">温度 (0-2)</span>
          <input v-model.number="llmEdit.temperature" type="number" step="0.1" min="0" max="2" required />
        </label>
        <label class="field">
          <span class="field-label">最大 Token</span>
          <input v-model.number="llmEdit.max_tokens" type="number" min="256" required />
        </label>
        <label class="field">
          <span class="field-label">超时 (秒)</span>
          <input v-model.number="llmEdit.timeout_seconds" type="number" min="1" required />
        </label>
        <div class="drawer-actions">
          <button type="button" class="btn ghost" @click="llmEditing = false">取消</button>
          <button type="submit" class="btn primary" :disabled="saving.llm">
            {{ saving.llm ? '保存中…' : '保存' }}
          </button>
        </div>
      </form>
    </Drawer>

    <!-- 邮件编辑抽屉 -->
    <Drawer :open="emailEditing" title="编辑邮件配置" @close="emailEditing = false">
      <form class="drawer-form" @submit.prevent="saveEmail">
        <label class="field">
          <span class="field-label">启用邮件提醒</span>
          <label class="switch-row">
            <input v-model="emailEdit.enabled" type="checkbox" />
            <span class="switch-label">{{ emailEdit.enabled ? '已启用' : '已停用' }}</span>
          </label>
        </label>
        <label class="field">
          <span class="field-label">SMTP 服务器</span>
          <input v-model="emailEdit.smtp_server" type="text" placeholder="如：smtp.example.com" />
        </label>
        <label class="field">
          <span class="field-label">端口</span>
          <input v-model.number="emailEdit.smtp_port" type="number" />
        </label>
        <label class="field">
          <span class="field-label">发件人邮箱</span>
          <input v-model="emailEdit.sender" type="email" placeholder="noreply@example.com" />
        </label>
        <label class="field">
          <span class="field-label">密码 / 授权码</span>
          <input v-model="emailEdit.password" type="password" placeholder="留空表示不修改" />
        </label>
        <div class="drawer-actions">
          <button type="button" class="btn ghost" @click="emailEditing = false">取消</button>
          <button type="submit" class="btn primary" :disabled="saving.email">
            {{ saving.email ? '保存中…' : '保存' }}
          </button>
        </div>
      </form>
    </Drawer>

    <!-- 主题切换抽屉 -->
    <Drawer :open="themeEditing" title="切换 AI 气泡主题" @close="themeEditing = false">
      <form class="drawer-form" @submit.prevent="saveTheme">
        <div class="field">
          <span class="field-label">选择主题</span>
          <div class="theme-options">
            <label
              v-for="t in themeOptions"
              :key="t.value"
              class="theme-option"
              :class="{ active: themeEdit === t.value }"
            >
              <input v-model="themeEdit" type="radio" :value="t.value" />
              <span class="theme-dot" :class="t.value" />
              <span class="theme-label">{{ t.label }}</span>
            </label>
          </div>
        </div>
        <div class="drawer-actions">
          <button type="button" class="btn ghost" @click="themeEditing = false">取消</button>
          <button type="submit" class="btn primary" :disabled="saving.theme">
            {{ saving.theme ? '保存中…' : '保存' }}
          </button>
        </div>
      </form>
    </Drawer>

    <!-- 全局参数编辑抽屉 -->
    <Drawer :open="globalEditing" title="编辑全局模型参数" @close="globalEditing = false">
      <form class="drawer-form" @submit.prevent="saveGlobal">
        <label class="field">
          <span class="field-label">上下文窗口</span>
          <input v-model.number="globalEdit.context_window" type="number" min="512" required />
          <span class="field-hint">决定单次请求可携带的最大 Token 数量</span>
        </label>
        <label class="field">
          <span class="field-label">生成语气</span>
          <select v-model="globalEdit.tone">
            <option v-for="t in toneOptions" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
          <span class="field-hint">影响所有 Agent 的回复风格与措辞倾向</span>
        </label>
        <div class="drawer-actions">
          <button type="button" class="btn ghost" @click="globalEditing = false">取消</button>
          <button type="submit" class="btn primary" :disabled="saving.global">
            {{ saving.global ? '保存中…' : '保存' }}
          </button>
        </div>
      </form>
    </Drawer>

    <!-- 服务器配置编辑抽屉 -->
    <Drawer :open="serverEditing" title="编辑服务器配置" @close="serverEditing = false">
      <form class="drawer-form" @submit.prevent="saveServer">
        <label class="field">
          <span class="field-label">日志级别</span>
          <select v-model="serverEdit">
            <option v-for="lv in logLevelOptions" :key="lv" :value="lv">{{ lv }}</option>
          </select>
          <span class="field-hint">运行环境、监听地址为启动级参数（修改 .env 生效），日志级别调整即时写入配置。</span>
        </label>
        <div class="drawer-actions">
          <button type="button" class="btn ghost" @click="serverEditing = false">取消</button>
          <button type="submit" class="btn primary" :disabled="saving.server">
            {{ saving.server ? '保存中…' : '保存' }}
          </button>
        </div>
      </form>
    </Drawer>

    <!-- 数据源与权限说明编辑抽屉 -->
    <Drawer
      :open="notesEditing"
      title="编辑数据源与权限说明"
      @close="notesEditing = false"
    >
      <form class="drawer-form" @submit.prevent="saveNotes">
        <label class="field">
          <span class="field-label">AI 洞察说明</span>
          <textarea v-model="notesEdit.ai_note" rows="3" placeholder="描述当前 AI 洞察能力的实现方式与产出边界..." />
          <span class="field-hint">展示在设置页说明区，向使用者说明洞察能力来源。</span>
        </label>
        <label class="field">
          <span class="field-label">身份认证说明</span>
          <textarea v-model="notesEdit.auth_note" rows="3" placeholder="描述登录与权限接入状态..." />
          <span class="field-hint">展示在设置页说明区，说明统一身份认证接入情况。</span>
        </label>
        <div class="drawer-actions">
          <button type="button" class="btn ghost" @click="notesEditing = false">取消</button>
          <button type="submit" class="btn primary" :disabled="saving.notes">
            {{ saving.notes ? '保存中…' : '保存' }}
          </button>
        </div>
      </form>
    </Drawer>

    <!-- Agent 提示词编辑抽屉 -->
    <Drawer
      :open="promptDrawerOpen"
      :title="`编辑提示词：${promptEditAgent?.name ?? ''}`"
      :width="560"
      @close="promptDrawerOpen = false"
    >
      <form
        v-if="promptEditAgent"
        class="drawer-form"
        @submit.prevent="savePrompt"
      >
        <div class="field">
          <span class="field-label">Agent</span>
          <div class="static-field">{{ promptEditAgent.name }}（{{ promptEditAgent.category }}）</div>
        </div>
        <label class="field">
          <span class="field-label">角色提示词</span>
          <textarea
            v-model="promptEditText"
            rows="8"
            placeholder="定义该 Agent 的角色、职责边界与输出要求..."
            required
          />
          <span class="field-hint">提示词越具体，Agent 输出越稳定。支持多行文本。</span>
        </label>
        <div class="drawer-actions">
          <button type="button" class="btn ghost" @click="promptDrawerOpen = false">取消</button>
          <button
            type="submit"
            class="btn primary"
            :disabled="saving[`prompt-${promptEditAgent.id}`]"
          >
            {{ saving[`prompt-${promptEditAgent.id}`] ? '保存中…' : '保存' }}
          </button>
        </div>
      </form>
    </Drawer>

    <!-- AI 配置助手气泡 -->
    <AIFloatingAssistant context="settings" />
  </div>
</template>

<style scoped>
.st {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sf-space-2);
  align-items: stretch;
}

/* 跨全宽分区 */
.span-2 {
  grid-column: 1 / -1;
}

/* 消息条 */
.msg-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--sf-radius-sm);
  background: var(--sf-success-soft);
  color: var(--sf-success);
  font-size: var(--sf-font-13);
  border: 1px solid var(--sf-success-border);
}

/* 卡片 */
.card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  box-shadow: var(--sf-shadow);
  padding: var(--sf-space-2) var(--sf-space-3);
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

/* 表格 */
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

/* KV：两对一行，提升信息密度 */
.kv {
  margin: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto minmax(0, 1fr);
  column-gap: var(--sf-space-3);
  row-gap: 5px;
  font-size: var(--sf-font-13);
}
.kv dt {
  color: var(--sf-text-faint);
  white-space: nowrap;
}
.kv dd {
  margin: 0;
  min-width: 0;
  color: var(--sf-text-secondary);
  word-break: break-word;
}

/* 操作按钮区：底部拉伸对齐 */
.actions {
  margin-top: auto;
  padding-top: var(--sf-space-1);
  display: flex;
  gap: 8px;
}

/* 按钮 */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--sf-radius-sm);
  font-size: var(--sf-font-13);
  cursor: pointer;
  border: 1px solid transparent;
  background: transparent;
  color: var(--sf-text);
}
.btn.primary {
  background: var(--sf-primary);
  color: #fff;
  border-color: var(--sf-primary);
}
.btn.ghost {
  border-color: var(--sf-border);
  color: var(--sf-text-secondary);
}
.btn.ghost:hover {
  border-color: var(--sf-primary);
  color: var(--sf-primary);
}
.btn.micro {
  padding: 3px 8px;
  font-size: var(--sf-font-12);
}
.btn.primary-ghost {
  border-color: var(--sf-primary);
  color: var(--sf-primary);
}
.btn.danger-ghost {
  border-color: var(--sf-danger);
  color: var(--sf-danger);
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* hint */
.hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: var(--sf-space-2) 0 0;
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}

/* 主题预览 */
.theme-row {
  display: flex;
  align-items: center;
  gap: var(--sf-space-3);
  padding: var(--sf-space-2);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-bg);
}
.theme-preview {
  flex-shrink: 0;
  padding: 10px 14px;
  border-radius: var(--sf-radius-sm);
}
.theme-preview .bubble {
  padding: 8px 12px;
  border-radius: 12px;
  font-size: var(--sf-font-13);
  color: #fff;
}
.theme-preview.blue .bubble { background: var(--sf-primary); }
.theme-preview.purple .bubble { background: #7c3aed; }
.theme-preview.green .bubble { background: #059669; }
.theme-preview.orange .bubble { background: #ea580c; }
.theme-preview.dark .bubble { background: #334155; }

.theme-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.theme-name {
  font-size: var(--sf-font-13);
  font-weight: 600;
  color: var(--sf-text);
}
.theme-desc {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
}

/* 主题选项 */
.theme-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.theme-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--sf-radius-sm);
  border: 1px solid var(--sf-border);
  cursor: pointer;
  transition: border-color 0.15s ease;
}
.theme-option.active {
  border-color: var(--sf-primary);
  background: var(--sf-primary-soft);
}
.theme-option input {
  display: none;
}
.theme-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  flex-shrink: 0;
}
.theme-dot.blue { background: var(--sf-primary); }
.theme-dot.purple { background: #7c3aed; }
.theme-dot.green { background: #059669; }
.theme-dot.orange { background: #ea580c; }
.theme-dot.dark { background: #334155; }
.theme-label {
  font-size: var(--sf-font-13);
  color: var(--sf-text);
}

/* Agent 提示词列表 */
.agent-prompt-list {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
}
.agent-prompt-item {
  padding: 10px 12px;
  border-radius: var(--sf-radius-sm);
  border: 1px solid var(--sf-border);
  background: var(--sf-bg);
}
.agent-prompt-item.disabled {
  opacity: 0.55;
}
.prompt-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.prompt-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--sf-font-13);
  font-weight: 600;
  color: var(--sf-text);
}
.prompt-text {
  margin: 0;
  font-size: var(--sf-font-12);
  line-height: 1.5;
  color: var(--sf-text-secondary);
  white-space: pre-wrap;
}

/* 抽屉表单 */
.drawer-form {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field-label {
  font-size: var(--sf-font-12);
  font-weight: 500;
  color: var(--sf-text-secondary);
}
.field-hint {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.drawer-form input,
.drawer-form select,
.drawer-form textarea {
  padding: 8px 10px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  font-size: var(--sf-font-13);
  background: var(--sf-surface);
  color: var(--sf-text);
}
.drawer-form input:focus,
.drawer-form select:focus,
.drawer-form textarea:focus {
  outline: none;
  border-color: var(--sf-primary);
}
.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: var(--sf-space-2);
}

/* 开关行 */
.switch-row {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.switch-label {
  font-size: var(--sf-font-13);
  color: var(--sf-text);
}

/* 静态字段 */
.static-field {
  padding: 8px 10px;
  border-radius: var(--sf-radius-sm);
  background: var(--sf-bg);
  font-size: var(--sf-font-13);
  color: var(--sf-text);
}

/* 说明卡片：标题间距由 .head 控制 */
.note .title {
  margin-bottom: 0;
}

/* 响应式：窄屏折叠为单列 */
@media (max-width: 1100px) {
  .st {
    grid-template-columns: 1fr;
  }
}
</style>
