<script setup lang="ts">
/**
 * FS-4 路线图与任务 + FS-5 回复与回传（决策 → 行动 → 闭环）。
 * 路线图看板按状态分组（规划/进行中/已排期/已上线），任务可从洞察主题创建；
 * 底部为 AI 回复草稿工作流：草稿 → 审批 → 回传（发送后 mock 回写反馈状态）。
 */
import { computed, onMounted, reactive, ref } from 'vue'

import Drawer from '@/components/common/Drawer.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SfIcon from '@/components/common/SfIcon.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useInsightsStore } from '@/stores/insights'
import type { DraftStatus, RoadmapItem, RoadmapStatus, TaskItem, TaskStatus } from '@/types'
import { formatDate } from '@/utils'

const insights = useInsightsStore()

const board = computed(() => insights.roadmap)
const loading = computed(() => insights.roadmapLoading)

const GROUPS: Array<{ key: RoadmapStatus; label: string; tone: 'info' | 'warning' | 'success' | 'neutral' }> = [
  { key: 'planning', label: '规划', tone: 'info' },
  { key: 'in_progress', label: '进行中', tone: 'warning' },
  { key: 'scheduled', label: '已排期', tone: 'neutral' },
  { key: 'released', label: '已上线', tone: 'success' },
]

const DRAFT_FLOW: Array<{ from: DraftStatus; to: DraftStatus; label: string; tone: 'info' | 'success' | 'warning' }> = [
  { from: 'draft', to: 'approved', label: '审批', tone: 'info' },
  { from: 'approved', to: 'sent', label: '回传', tone: 'success' },
]

const TASK_LABEL: Record<TaskStatus, string> = { todo: '待办', doing: '进行', done: '完成' }

const createOpen = ref(false)
const form = reactive({ roadmap_id: '', title: '', owner: '产品组', priority: 2 })

const sentCount = computed(() => board.value?.drafts.filter((d) => d.status === 'sent').length ?? 0)
const draftCount = computed(() => board.value?.drafts.filter((d) => d.status !== 'sent').length ?? 0)

onMounted(() => {
  void insights.fetchRoadmap()
})

function itemsOf(status: RoadmapStatus) {
  return board.value?.items.filter((i) => i.status === status) ?? []
}

function tasksOf(item: RoadmapItem) {
  return board.value?.tasks.filter((t) => t.roadmap_id === item.id) ?? []
}

function openCreate(item?: RoadmapItem) {
  form.roadmap_id = item?.id ?? board.value?.items[0]?.id ?? ''
  form.title = item ? `优化：${item.title}` : ''
  createOpen.value = true
}

async function submitCreate() {
  if (!form.roadmap_id || !form.title.trim()) return
  await insights.createTask({ roadmap_id: form.roadmap_id, title: form.title.trim(), owner: form.owner, priority: form.priority })
  createOpen.value = false
  form.title = ''
}

async function cycleTask(task: TaskItem) {
  const next: TaskStatus = task.status === 'done' ? 'todo' : task.status === 'todo' ? 'doing' : 'done'
  await insights.changeTaskStatus(task.id, next)
}

async function draftAction(draftId: string, to: DraftStatus) {
  await insights.changeDraftStatus(draftId, to)
}
</script>

<template>
  <div class="rm">
    <section class="card head">
      <div class="head-left">
        <h2 class="title">路线图与任务</h2>
        <span class="sub">从洞察主题到行动闭环</span>
      </div>
      <div class="stats">
        <span v-for="g in GROUPS" :key="g.key" class="stat">
          <StatusBadge :label="g.label" :tone="g.tone" />
          <span class="num">{{ itemsOf(g.key).length }}</span>
        </span>
        <span class="stat">
          <StatusBadge label="草稿/审批" tone="warning" />
          <span class="num">{{ draftCount }}</span>
        </span>
        <span class="stat">
          <StatusBadge label="已回传" tone="success" />
          <span class="num">{{ sentCount }}</span>
        </span>
        <button type="button" class="btn primary" @click="openCreate()">
          <SfIcon name="plus" :size="15" /> 新建任务
        </button>
      </div>
    </section>

    <Skeleton v-if="loading" :rows="8" />
    <EmptyState v-else-if="!board || board.items.length === 0" text="暂无路线图数据" />
    <div v-else class="board">
      <section v-for="g in GROUPS" :key="g.key" class="col">
        <div class="col-head">
          <StatusBadge :label="g.label" :tone="g.tone" />
          <span class="num">{{ itemsOf(g.key).length }}</span>
        </div>
        <article v-for="item in itemsOf(g.key)" :key="item.id" class="r-card">
          <div class="r-top">
            <span class="r-title">{{ item.title }}</span>
            <button type="button" class="icon-btn" title="新建关联任务" @click="openCreate(item)">
              <SfIcon name="plus" :size="14" />
            </button>
          </div>
          <div class="r-meta">
            <span>{{ item.owner }} · {{ item.version }}</span>
            <span class="due">{{ item.due_date ? `截至 ${formatDate(item.due_date)}` : '' }}</span>
          </div>
          <div class="prog">
            <div class="prog-track"><div class="prog-fill" :style="{ width: `${item.progress}%` }" /></div>
            <span class="prog-num num">{{ item.progress }}%</span>
          </div>
          <ul class="task-list">
            <li v-for="t in tasksOf(item)" :key="t.id" class="task" :class="{ done: t.status === 'done' }">
              <button type="button" class="tick" :class="{ on: t.status !== 'todo' }" @click="cycleTask(t)">
                <SfIcon v-if="t.status === 'done'" name="check" :size="13" />
              </button>
              <span class="task-title" :title="TASK_LABEL[t.status]">{{ t.title }}</span>
              <StatusBadge :label="TASK_LABEL[t.status]" tone="muted" />
            </li>
          </ul>
        </article>
      </section>
    </div>

    <!-- FS-5 回复与回传 -->
    <section class="card drafts">
      <div class="head-left">
        <h2 class="title">回复与回传</h2>
        <span class="sub">AI 起草 · 人工审批 · 回传客户</span>
      </div>
      <EmptyState v-if="board && board.drafts.length === 0" text="暂无回复草稿" />
      <div v-else class="draft-grid">
        <article v-for="d in board?.drafts ?? []" :key="d.id" class="d-card">
          <div class="d-top">
            <span class="d-id">{{ d.id }}</span>
            <StatusBadge
              :label="d.status === 'draft' ? '草稿' : d.status === 'approved' ? '已审批' : '已回传'"
              :tone="d.status === 'draft' ? 'warning' : d.status === 'approved' ? 'info' : 'success'"
            />
          </div>
          <p class="d-excerpt">{{ d.excerpt }}</p>
          <p class="d-body">{{ d.draft }}</p>
          <div class="d-foot">
            <span class="d-tone">{{ d.tone }}</span>
            <span class="d-time">{{ formatDate(d.updated_at) }}</span>
          </div>
          <div v-if="d.status !== 'sent'" class="d-acts">
            <button
              v-for="f in DRAFT_FLOW.filter((x) => x.from === d.status)"
              :key="f.to"
              type="button"
              class="btn sm"
              :class="f.to === 'sent' ? 'primary' : ''"
              @click="draftAction(d.id, f.to)"
            >
              {{ f.label }}
            </button>
          </div>
        </article>
      </div>
    </section>

    <Drawer :open="createOpen" title="新建任务" @close="createOpen = false">
      <form class="form" @submit.prevent="submitCreate">
        <label class="field">
          <span>路线图</span>
          <select v-model="form.roadmap_id" class="ctrl">
            <option v-for="item in board?.items ?? []" :key="item.id" :value="item.id">{{ item.title }}</option>
          </select>
        </label>
        <label class="field">
          <span>任务标题</span>
          <input v-model="form.title" class="ctrl" type="text" placeholder="输入任务标题" />
        </label>
        <label class="field">
          <span>负责人</span>
          <input v-model="form.owner" class="ctrl" type="text" />
        </label>
        <label class="field">
          <span>优先级</span>
          <select v-model.number="form.priority" class="ctrl">
            <option :value="1">P1 高</option>
            <option :value="2">P2 中</option>
            <option :value="3">P3 低</option>
          </select>
        </label>
        <button type="submit" class="btn primary block">创建</button>
      </form>
    </Drawer>
  </div>
</template>

<style scoped>
.rm {
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
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-3);
  flex-wrap: wrap;
}
.head-left {
  display: flex;
  align-items: baseline;
  gap: var(--sf-space-2);
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
.stats {
  display: flex;
  align-items: center;
  gap: var(--sf-space-3);
  flex-wrap: wrap;
}
.stat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.num {
  font-size: var(--sf-font-13);
  font-weight: 600;
  color: var(--sf-text);
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
  padding: 0 10px;
  font-size: var(--sf-font-12);
}
.btn.block {
  width: 100%;
  justify-content: center;
  margin-top: var(--sf-space-2);
}
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: var(--sf-radius-sm);
  background: transparent;
  color: var(--sf-text-faint);
  cursor: pointer;
}
.icon-btn:hover {
  background: var(--sf-bg);
  color: var(--sf-primary);
}
.board {
  display: grid;
  grid-template-columns: repeat(4, minmax(260px, 1fr));
  gap: var(--sf-space-3);
  align-items: start;
}
.col {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
}
.col-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2px;
}
.r-card {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  box-shadow: var(--sf-shadow);
  padding: var(--sf-space-2) var(--sf-space-3);
}
.r-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sf-space-2);
}
.r-title {
  font-size: var(--sf-font-13);
  font-weight: 600;
  line-height: 1.35;
}
.r-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  margin-top: 3px;
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
}
.due {
  color: var(--sf-text-faint);
  white-space: nowrap;
}
.prog {
  display: flex;
  align-items: center;
  gap: var(--sf-space-2);
  margin-top: var(--sf-space-2);
}
.prog-track {
  flex: 1;
  height: 5px;
  border-radius: 3px;
  background: var(--sf-bg);
  overflow: hidden;
}
.prog-fill {
  height: 100%;
  background: var(--sf-primary);
  border-radius: 3px;
}
.prog-num {
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
}
.task-list {
  list-style: none;
  margin: var(--sf-space-2) 0 0;
  padding: 0;
}
.task {
  display: flex;
  align-items: center;
  gap: var(--sf-space-2);
  min-height: 28px;
}
.task + .task {
  border-top: 1px dashed var(--sf-border);
}
.task.done .task-title {
  text-decoration: line-through;
  color: var(--sf-text-faint);
}
.tick {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid var(--sf-border);
  background: var(--sf-surface);
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
}
.tick.on {
  background: var(--sf-success);
  border-color: var(--sf-success);
}
.tick:hover {
  border-color: var(--sf-success);
}
.task-title {
  flex: 1;
  font-size: var(--sf-font-12);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.drafts {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-2);
}
.draft-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--sf-space-3);
}
.d-card {
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius);
  background: var(--sf-surface);
  padding: var(--sf-space-2) var(--sf-space-3);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.d-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
}
.d-id {
  font-size: var(--sf-font-12);
  font-weight: 600;
  color: var(--sf-text-secondary);
}
.d-excerpt {
  margin: 0;
  font-size: var(--sf-font-12);
  color: var(--sf-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.d-body {
  margin: 0;
  font-size: var(--sf-font-13);
  line-height: 1.5;
  color: var(--sf-text);
}
.d-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sf-space-2);
  font-size: var(--sf-font-12);
  color: var(--sf-text-faint);
}
.d-acts {
  display: flex;
  gap: var(--sf-space-2);
  padding-top: var(--sf-space-1);
  border-top: 1px solid var(--sf-border);
}
.form {
  display: flex;
  flex-direction: column;
  gap: var(--sf-space-3);
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: var(--sf-font-13);
  color: var(--sf-text-secondary);
}
.ctrl {
  height: 32px;
  border: 1px solid var(--sf-border);
  border-radius: var(--sf-radius-sm);
  background: var(--sf-surface);
  color: var(--sf-text);
  font-size: var(--sf-font-13);
  padding: 0 var(--sf-space-2);
}
.ctrl:focus {
  outline: none;
  border-color: var(--sf-primary);
}
@media (max-width: 1200px) {
  .board {
    grid-template-columns: repeat(2, minmax(260px, 1fr));
  }
  .draft-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 700px) {
  .board {
    grid-template-columns: 1fr;
  }
  .draft-grid {
    grid-template-columns: 1fr;
  }
}
</style>