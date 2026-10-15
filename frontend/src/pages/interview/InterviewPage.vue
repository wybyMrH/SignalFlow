<script setup lang="ts">
/**
 * 客户访谈中心：调研 → AI 提炼 → 商务联动。
 * 访谈记录管理 + AI 提炼客户痛点与需求 + 生成商务线索 + 关联反馈。
 * 理念：访谈不只是记录，AI 提炼的合作意向自动汇入商务线索池、痛点自动匹配共性需求，形成闭环。
 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import AIFloatingAssistant from '@/components/ai/AIFloatingAssistant.vue'
import SfIcon from '@/components/common/SfIcon.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useInterviewsStore } from '@/stores/interviews'
import { formatDate, formatDateTime } from '@/utils'
import type { IconName } from '@/components/common/SfIcon.vue'
import type { InterviewStatus } from '@/types'

const router = useRouter()
const store = useInterviewsStore()

const activeFilter = ref<'all' | 'pending' | 'extracted' | 'linked'>('all')
const selectedId = ref<string | null>(null)

const records = computed(() => store.records)
const summary = computed(() => store.summary)
const loading = computed(() => store.loading)
const extractingId = computed(() => store.extractingId)

const statusLabel: Record<InterviewStatus, string> = {
  scheduled: '已预约',
  recorded: '已记录',
  extracted: '已提炼',
  linked: '已联动',
}
const statusTone = (s: InterviewStatus) =>
  (s === 'linked' ? 'success' : s === 'extracted' ? 'info' : s === 'recorded' ? 'warning' : 'neutral') as 'success' | 'info' | 'warning' | 'neutral'

const intentLabel: Record<string, string> = { high: '高', medium: '中', low: '低' }

const filters: Array<{ key: 'all' | 'pending' | 'extracted' | 'linked'; label: string; icon: IconName }> = [
  { key: 'all', label: '全部', icon: 'checklist' },
  { key: 'pending', label: '待提炼', icon: 'clock' },
  { key: 'extracted', label: '已提炼', icon: 'magic' },
  { key: 'linked', label: '已生成线索', icon: 'target' },
]

const filtered = computed(() => {
  switch (activeFilter.value) {
    case 'pending':
      return records.value.filter((r) => r.status === 'scheduled' || r.status === 'recorded')
    case 'extracted':
      return records.value.filter((r) => r.status === 'extracted')
    case 'linked':
      return records.value.filter((r) => r.status === 'linked')
    default:
      return records.value
  }
})

const selected = computed(() => {
  const id = selectedId.value
  if (!id) return filtered.value[0] ?? null
  return records.value.find((r) => r.id === id) ?? filtered.value[0] ?? null
})

onMounted(() => {
  void store.fetchAll()
})

function select(id: string) {
  selectedId.value = id
}

function goBusiness() {
  void router.push('/business')
}

function goFeedback(id: string) {
  void router.push({ path: '/feedback', query: { q: id } })
}
</script>

<template>
  <div class="iv-center">
    <!-- 顶部统计卡 -->
    <div class="stats-row">
      <template v-if="loading || !summary">
        <Skeleton v-for="i in 6" :key="i" :rows="2" class="stat-skel" />
      </template>
      <template v-else>
        <div class="stat-card">
          <div class="stat-label">
            <SfIcon name="mic" :size="14" /> 访谈总记录
          </div>
          <div class="stat-value">{{ summary.total }}</div>
          <div class="stat-hint">累计 {{ Math.round(summary.total_duration_min / 60 * 10) / 10 }} 小时</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">
            <SfIcon name="clock" :size="14" /> 待 AI 提炼
          </div>
          <div class="stat-value" style="color: var(--sf-warning)">{{ summary.pending_extraction }}</div>
          <div class="stat-hint">录音/纪要待理解</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">
            <SfIcon name="magic" :size="14" /> 已提炼
          </div>
          <div class="stat-value">{{ summary.extracted }}</div>
          <div class="stat-hint">痛点与需求已结构化</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">
            <SfIcon name="target" :size="14" /> 合作意向候选
          </div>
          <div class="stat-value" style="color: var(--sf-primary)">{{ summary.lead_candidates }}</div>
          <div class="stat-hint">可生成商务线索</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">
            <SfIcon name="send" :size="14" /> 已生成线索
          </div>
          <div class="stat-value" style="color: var(--sf-success)">{{ summary.generated_leads }}</div>
          <div class="stat-hint">汇入商务洞察线索池</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">
            <SfIcon name="need" :size="14" /> 匹配共性需求
          </div>
          <div class="stat-value">{{ summary.matched_needs_count }}</div>
          <div class="stat-hint">映射产品能力候选</div>
        </div>
      </template>
    </div>

    <!-- 元信息 -->
    <div v-if="summary" class="report-meta">
      <SfIcon name="file" :size="14" />
      AI 仅提炼候选，线索推进与对外动作需人工确认；访谈痛点会自动与商务洞察共性需求联动。
    </div>

    <!-- 主体：左列表 + 右详情 -->
    <div class="iv-main">
      <!-- 左：访谈列表 -->
      <section class="iv-list card">
        <div class="filter-bar">
          <button
            v-for="f in filters"
            :key="f.key"
            type="button"
            class="tab-btn"
            :class="{ active: activeFilter === f.key }"
            @click="activeFilter = f.key"
          >
            <SfIcon :name="f.icon" :size="14" />
            {{ f.label }}
          </button>
        </div>

        <Skeleton v-if="loading" :rows="6" />
        <div v-else class="list-body">
          <button
            v-for="r in filtered"
            :key="r.id"
            type="button"
            class="iv-item"
            :class="{ active: selected?.id === r.id }"
            @click="select(r.id)"
          >
            <div class="iv-item-top">
              <span class="iv-id">{{ r.id }}</span>
              <StatusBadge :label="statusLabel[r.status]" :tone="statusTone(r.status)" />
            </div>
            <div class="iv-company">{{ r.company_name }}</div>
            <div class="iv-sub">{{ r.industry }} · {{ r.contact_name }} {{ r.contact_role }}</div>
            <div class="iv-meta">
              <SfIcon name="mic" :size="11" /> {{ r.source }} · {{ r.duration_min }} min
              <span class="iv-date">{{ formatDate(r.interview_date) }}</span>
            </div>
            <div v-if="r.extraction?.cooperation_intent === 'high' && !r.linked_lead_id" class="iv-candidate">
              高意向候选
            </div>
          </button>
          <p v-if="!filtered.length" class="empty-text">当前筛选下暂无访谈记录</p>
        </div>
      </section>

      <!-- 右：详情 + AI 提炼 -->
      <section v-if="selected" class="iv-detail">
        <div class="card detail-card">
          <div class="detail-head">
            <div>
              <div class="detail-title">
                {{ selected.company_name }}
                <StatusBadge :label="statusLabel[selected.status]" :tone="statusTone(selected.status)" />
              </div>
              <div class="detail-sub">
                {{ selected.industry }} · {{ selected.company_type }} ·
                <span class="chip">{{ selected.source }}</span> · {{ formatDateTime(selected.interview_date) }}
              </div>
            </div>
          </div>

          <!-- 基本信息 -->
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">访谈对象</span>
              <span class="info-value">{{ selected.contact_name }}（{{ selected.contact_role }}）</span>
            </div>
            <div class="info-item">
              <span class="info-label">记录员</span>
              <span class="info-value">{{ selected.recorder }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">时长</span>
              <span class="info-value">{{ selected.duration_min }} 分钟</span>
            </div>
            <div class="info-item">
              <span class="info-label">结构化纪要</span>
              <span class="info-value">{{ selected.summary }}</span>
            </div>
          </div>

          <!-- 关键要点 -->
          <div class="block">
            <div class="block-title">访谈关键要点</div>
            <ul class="point-list">
              <li v-for="(p, i) in selected.key_points" :key="i">{{ p }}</li>
            </ul>
          </div>

          <!-- AI 提炼结果 -->
          <div v-if="selected.extraction" class="block extract-block">
            <div class="block-title">
              <SfIcon name="magic" :size="14" />
              AI 提炼结论
              <span class="extract-time">提炼于 {{ formatDateTime(selected.extraction.extracted_at) }}</span>
            </div>

            <div class="extract-row">
              <span class="extract-label">客户痛点</span>
              <span class="tag-list">
                <span v-for="p in selected.extraction.pain_points" :key="p" class="tag tag-warn">{{ p }}</span>
              </span>
            </div>
            <div class="extract-row">
              <span class="extract-label">需求主张</span>
              <span class="tag-list">
                <span v-for="n in selected.extraction.needs" :key="n" class="tag tag-info">{{ n }}</span>
              </span>
            </div>
            <div class="extract-row">
              <span class="extract-label">合作意向</span>
              <span class="tag tag-intent">{{ intentLabel[selected.extraction.cooperation_intent] }}意向</span>
            </div>
            <div class="extract-row">
              <span class="extract-label">匹配共性需求</span>
              <span class="tag-list">
                <button
                  v-for="m in selected.extraction.matched_needs"
                  :key="m"
                  type="button"
                  class="tag tag-need"
                  title="前往商务洞察查看"
                  @click="goBusiness"
                >
                  {{ m }} <SfIcon name="external" :size="11" />
                </button>
                <span v-if="!selected.extraction.matched_needs.length" class="dim">暂无匹配</span>
              </span>
            </div>

            <div v-if="selected.extraction.lead_candidate" class="lead-note">
              <SfIcon name="target" :size="14" />
              AI 识别到合作信号：{{ selected.extraction.lead_reason }}
            </div>
          </div>

          <!-- 尚未提炼 -->
          <div v-else class="block pending-block">
            <div class="block-title">AI 提炼</div>
            <p class="pending-text">
              {{ selected.status === 'scheduled' ? '访谈尚未开始，预约完成后可进行 AI 提炼。' : '该访谈已完成记录，可执行 AI 提炼，自动识别客户痛点、需求与合作意向，并联动商务洞察。' }}
            </p>
            <button v-if="selected.status !== 'scheduled'" type="button" class="btn primary" :disabled="extractingId === selected.id" @click="store.runExtraction(selected.id)">
              <SfIcon name="magic" :size="14" />
              {{ extractingId === selected.id ? 'AI 提炼中...' : '执行 AI 提炼' }}
            </button>
          </div>

          <!-- 商务联动 -->
          <div class="block action-block">
            <div class="block-title">商务联动</div>
            <div v-if="selected.linked_lead_id" class="linked-line">
              <SfIcon name="check" :size="14" style="color: var(--sf-success)" />
              已生成商务线索
              <span class="lead-id-chip">{{ selected.linked_lead_id }}</span>
              <button type="button" class="link-btn" @click="goBusiness">前往商务洞察查看 <SfIcon name="chevron-right" :size="13" /></button>
            </div>
            <div v-else-if="selected.extraction?.lead_candidate" class="linked-line">
              <button type="button" class="btn primary" @click="store.generateLead(selected.id)">
                <SfIcon name="send" :size="14" />
                生成商务线索并汇入线索池
              </button>
              <span class="dim">生成后可前往商务洞察跟进</span>
            </div>
            <div v-else class="linked-line dim">暂无合作意向信号，暂不生成线索。</div>

            <div v-if="selected.linked_feedback_ids.length" class="linked-feedback">
              <span class="extract-label">关联反馈</span>
              <button
                v-for="fid in selected.linked_feedback_ids"
                :key="fid"
                type="button"
                class="tag tag-link"
                title="前往反馈管理查看原文"
                @click="goFeedback(fid)"
              >
                {{ fid }} <SfIcon name="external" :size="11" />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>

    <AIFloatingAssistant context="interview" />
  </div>
</template>

<style scoped>
.iv-center {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.stats-row {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--sf-space-3);
}
.stat-skel {
  height: 84px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  padding: 12px 16px;
}
.stat-card {
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  box-shadow: var(--sf-shadow);
  padding: var(--sf-space-3) var(--sf-space-4);
}
.stat-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  margin-bottom: 6px;
}
.stat-label :deep(svg) {
  color: var(--sf-primary);
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--sf-text);
  font-variant-numeric: tabular-nums;
}
.stat-hint {
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
  margin-top: 2px;
}
.report-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}

/* 主体双栏 */
.iv-main {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: var(--sf-space-3);
  align-items: start;
}
.card {
  background: var(--sf-surface);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  box-shadow: var(--sf-shadow);
  padding: var(--sf-space-3) var(--sf-space-4);
}
.iv-list {
  padding: var(--sf-space-3);
}
.filter-bar {
  display: flex;
  gap: 6px;
  margin-bottom: var(--sf-space-3);
  flex-wrap: wrap;
}
.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text-secondary);
  font-size: var(--sf-font-12);
  cursor: pointer;
  transition: all 0.15s;
}
.tab-btn:hover {
  border-color: var(--sf-primary-border);
  color: var(--sf-primary);
}
.tab-btn.active {
  border-color: var(--sf-primary);
  color: var(--sf-primary);
  background: var(--sf-primary-soft);
}
.list-body {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
  max-height: calc(100vh - var(--sf-header-h) - 260px);
  overflow-y: auto;
}
.iv-item {
  position: relative;
  text-align: left;
  padding: var(--sf-space-2) var(--sf-space-3);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.iv-item:hover {
  border-color: var(--sf-primary-border);
}
.iv-item.active {
  border-color: var(--sf-primary);
  background: var(--sf-primary-soft);
}
.iv-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 2px;
}
.iv-id {
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-text-faint);
}
.iv-company {
  font-size: var(--sf-font-14);
  font-weight: 600;
  color: var(--sf-text);
}
.iv-sub {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
}
.iv-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
}
.iv-date {
  margin-left: auto;
}
.iv-candidate {
  position: absolute;
  right: var(--sf-space-3);
  bottom: var(--sf-space-2);
  font-size: 11px;
  color: var(--sf-primary);
  background: var(--sf-primary-soft);
  border-radius: 8px;
  padding: 1px 6px;
}
.empty-text {
  color: var(--sf-text-faint);
  font-size: var(--sf-font-13);
  text-align: center;
  padding: var(--sf-space-3) 0;
}

/* 详情 */
.iv-detail {
  min-width: 0;
}
.detail-card {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.detail-head {
  display: flex;
  align-items: flex-start;
  gap: var(--sf-space-2);
}
.detail-title {
  display: flex;
  align-items: center;
  gap: var(--sf-space-2);
  font-size: var(--sf-font-16);
  font-weight: 700;
  color: var(--sf-text);
}
.detail-sub {
  margin-top: 4px;
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.chip {
  font-size: 11px;
  border: 1px solid var(--sf-border);
  border-radius: 8px;
  padding: 1px 6px;
  color: var(--sf-text-secondary);
}
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sf-space-2) var(--sf-space-3);
  background: var(--sf-bg);
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  padding: var(--sf-space-2) var(--sf-space-3);
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.info-item:nth-child(4) {
  grid-column: 1 / -1;
}
.info-label {
  font-size: var(--sf-font-11);
  color: var(--sf-text-faint);
}
.info-value {
  font-size: var(--sf-font-13);
  color: var(--sf-text);
  line-height: 1.5;
}
.block {
  border-top: 1px solid var(--sf-border);
  padding-top: var(--sf-space-3);
}
.block-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--sf-font-13);
  font-weight: 600;
  color: var(--sf-text);
  margin-bottom: var(--sf-space-2);
}
.point-list {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.point-list li {
  font-size: var(--sf-font-13);
  line-height: 1.5;
  color: var(--sf-text-secondary);
}
.extract-block {
  background: linear-gradient(135deg, var(--sf-primary-soft) 0%, transparent 60%);
  border: 1px solid var(--sf-primary-border);
  border-radius: var(--sf-radius-sm);
  padding: var(--sf-space-3);
}
.extract-time {
  margin-left: auto;
  font-size: 11px;
  font-weight: 400;
  color: var(--sf-text-faint);
}
.extract-row {
  display: flex;
  align-items: flex-start;
  gap: var(--sf-space-2);
  margin-bottom: var(--sf-space-2);
}
.extract-label {
  flex-shrink: 0;
  width: 76px;
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  padding-top: 3px;
}
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--sf-font-12);
  border-radius: 10px;
  padding: 2px 8px;
  border: 1px solid transparent;
}
.tag-warn {
  background: rgba(245, 158, 11, 0.12);
  color: #b45309;
}
.tag-info {
  background: var(--sf-primary-soft);
  color: var(--sf-primary);
  border-color: var(--sf-primary-border);
}
.tag-intent {
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
}
.tag-need {
  background: var(--sf-surface);
  color: var(--sf-primary);
  border-color: var(--sf-primary-border);
  cursor: pointer;
}
.tag-need:hover {
  background: var(--sf-primary-soft);
}
.tag-link {
  background: var(--sf-bg);
  color: var(--sf-text-secondary);
  border-color: var(--sf-border);
  cursor: pointer;
}
.tag-link:hover {
  color: var(--sf-primary);
  border-color: var(--sf-primary-border);
}
.lead-note {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: var(--sf-space-2);
  padding: var(--sf-space-2) var(--sf-space-3);
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: var(--sf-radius-sm);
  font-size: var(--sf-font-13);
  color: #065f46;
  line-height: 1.5;
}
.pending-block .pending-text {
  margin: 0 0 var(--sf-space-2);
  font-size: var(--sf-font-13);
  color: var(--sf-text-secondary);
  line-height: 1.5;
}
.link-btn {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  border: none;
  background: none;
  color: var(--sf-primary);
  font-size: var(--sf-font-12);
  cursor: pointer;
  padding: 2px 4px;
}
.link-btn:hover {
  text-decoration: underline;
}
.action-block {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
}
.linked-line {
  display: flex;
  align-items: center;
  gap: var(--sf-space-2);
  flex-wrap: wrap;
  font-size: var(--sf-font-13);
  color: var(--sf-text);
}
.lead-id-chip {
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-success);
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 8px;
  padding: 1px 6px;
}
.linked-feedback {
  display: flex;
  align-items: center;
  gap: var(--sf-space-2);
  flex-wrap: wrap;
  font-size: var(--sf-font-12);
}
.dim {
  color: var(--sf-text-faint);
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: var(--sf-radius-sm);
  cursor: pointer;
  font-size: var(--sf-font-13);
  transition: opacity 0.15s;
}
.btn.primary {
  background: var(--sf-primary);
  color: #fff;
  border: none;
  padding: 7px 14px;
}
.btn.primary:hover {
  opacity: 0.9;
}
.btn.primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .iv-main {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .stats-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>