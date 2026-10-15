import { ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchInterviewRecords, fetchInterviewSummary, runInterviewExtraction } from '@/api/interviews'
import { useAIStore } from './ai'
import type { InterviewRecord, InterviewSummary } from '@/types'

/**
 * 客户访谈 store：访谈记录管理 + AI 提炼 + 商务洞察联动。
 * 理念：访谈不只是记录，AI 提炼的痛点与需求可自动匹配共性需求、
 * 识别合作意向生成商务线索，形成「调研 → 提炼 → 线索 → 跟进」闭环。
 */
export const useInterviewsStore = defineStore('interviews', () => {
  const records = ref<InterviewRecord[]>([])
  const summary = ref<InterviewSummary | null>(null)
  const loading = ref(false)
  const extractingId = ref<string | null>(null)

  async function fetchAll(force = false) {
    if (!force && records.value.length) {
      return
    }
    loading.value = true
    try {
      const [r, s] = await Promise.all([fetchInterviewRecords(), fetchInterviewSummary()])
      records.value = r
      summary.value = s
    } finally {
      loading.value = false
    }
  }

  /** 对指定访谈执行 AI 提炼（模拟录音/纪要理解） */
  async function runExtraction(id: string) {
    extractingId.value = id
    try {
      const ex = await runInterviewExtraction(id)
      const rec = records.value.find((r) => r.id === id)
      if (rec) {
        rec.extraction = ex
        rec.status = 'extracted'
        rec.summary = `访谈已由 AI 提炼：${ex.pain_points.join('、')}；${ex.needs.join('、')}。`
        refreshSummary()
      }
    } finally {
      extractingId.value = null
    }
  }

  /** 商务联动：把访谈转化为商务线索，汇入商务洞察线索池 */
  function generateLead(id: string) {
    const rec = records.value.find((r) => r.id === id)
    if (!rec || rec.linked_lead_id || !rec.extraction?.lead_candidate) return
    const ai = useAIStore()
    const lead = ai.addLeadFromInterview(rec)
    rec.linked_lead_id = lead.id
    rec.status = 'linked'
    refreshSummary()
  }

  /** 将访谈关联到已有反馈（模拟联动：编号已由 AI 语义匹配预设） */
  function linkFeedback(id: string, feedbackId: string) {
    const rec = records.value.find((r) => r.id === id)
    if (!rec) return
    if (!rec.linked_feedback_ids.includes(feedbackId)) {
      rec.linked_feedback_ids.push(feedbackId)
    }
  }

  function refreshSummary() {
    if (!summary.value) return
    const extracted = records.value.filter((r) => r.status === 'extracted' || r.status === 'linked')
    summary.value = {
      ...summary.value,
      extracted: extracted.length,
      pending_extraction: records.value.filter((r) => r.status === 'recorded').length,
      lead_candidates: extracted.filter((r) => r.extraction?.lead_candidate).length,
      generated_leads: records.value.filter((r) => r.linked_lead_id).length,
      matched_needs_count: new Set(extracted.flatMap((r) => r.extraction?.matched_needs ?? [])).size,
    }
  }

  return {
    records,
    summary,
    loading,
    extractingId,
    fetchAll,
    runExtraction,
    generateLead,
    linkFeedback,
  }
})