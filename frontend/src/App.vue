<script setup lang="ts">
/**
 * FS-0 应用壳：左侧图标式侧边栏 + 顶栏 + 内容区。
 * 布局遵循 docs/frontend-development-plan.md §5.3：侧边 72px 图标式、顶栏 52px、
 * 紧凑 12px 内容间距；主题切换（浅/深）即时生效。
 */
import { useRoute } from 'vue-router'

import SfIcon, { type IconName } from '@/components/common/SfIcon.vue'
import { useAppStore } from '@/stores'

const route = useRoute()
const app = useAppStore()

const isMock = import.meta.env.VITE_USE_MOCK !== 'false'

/** 开源仓库地址：顶栏 GitHub 入口点击后在新标签打开，便于查看与 Star */
const repoUrl = 'https://github.com/wybyMrH/SignalFlow'

const navItems: Array<{ to: string; label: string; icon: IconName }> = [
  { to: '/', label: '总览', icon: 'dashboard' },
  { to: '/feedback', label: '反馈管理', icon: 'feedback' },
  { to: '/insights', label: '洞察与决策', icon: 'insights' },
  { to: '/roadmap', label: '路线图', icon: 'roadmap' },
  { to: '/automation', label: 'AI 自动化', icon: 'automation' },
  { to: '/workflows', label: '工作流配置', icon: 'workflow' },
  { to: '/business', label: '商务洞察', icon: 'briefcase' },
  { to: '/interview', label: '客户访谈', icon: 'mic' },
  { to: '/gov', label: '政务适配', icon: 'gov' },
  { to: '/agents', label: 'Agent 配置', icon: 'agent' },
  { to: '/resources', label: '资源管理', icon: 'server' },
  { to: '/settings', label: '系统设置', icon: 'settings' },
]
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand" title="SignalFlow">
        <SfIcon name="logo" :size="26" class="brand-icon" />
        <span class="brand-text">SignalFlow</span>
      </div>
      <nav class="nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :title="item.label"
        >
          <SfIcon :name="item.icon" :size="20" />
          <span class="nav-label">{{ item.label }}</span>
        </RouterLink>
      </nav>
      <button class="theme-toggle" type="button" :title="app.theme === 'light' ? '切换深色' : '切换浅色'" @click="app.toggleTheme()">
        <SfIcon :name="app.theme === 'light' ? 'moon' : 'sun'" :size="20" />
      </button>
    </aside>

    <div class="main">
      <header class="topbar">
        <h1 class="page-title">{{ route.meta.title }}</h1>
        <div class="topbar-right">
          <span v-if="isMock" class="mock-badge" title="当前使用模拟数据，设 VITE_USE_MOCK=false 切换真实后端">Mock</span>
          <a
            class="gh-link"
            :href="repoUrl"
            target="_blank"
            rel="noopener noreferrer"
            title="在 GitHub 打开 SignalFlow 仓库并 Star 支持"
          >
            <SfIcon name="github" :size="18" />
            <span class="gh-star"><SfIcon name="need" :size="12" />Star</span>
          </a>
          <span class="user">管理员</span>
        </div>
      </header>
      <main class="content">
        <RouterView v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  display: flex;
  min-height: 100vh;
}

/* 侧边栏：72px 图标式（浅色主题淡色底，活跃项品牌蓝） */
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--sf-sidebar-w);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 0 10px;
  background: var(--sf-sidebar-bg);
  color: var(--sf-sidebar-text);
  border-right: 1px solid var(--sf-sidebar-border);
  z-index: 20;
}

.brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  margin-bottom: 14px;
  color: var(--sf-sidebar-text);
}
.brand-icon {
  color: var(--sf-primary);
}
.brand-text {
  font-size: 10px;
  letter-spacing: 0.5px;
  opacity: 0.65;
  color: var(--sf-sidebar-muted);
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  align-items: center;
  flex: 1;
  overflow-y: auto;
  scrollbar-width: none;
}
.nav::-webkit-scrollbar {
  display: none;
}

.nav-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  width: 80px;
  height: 56px;
  border-radius: var(--sf-radius-sm);
  color: var(--sf-sidebar-muted);
  text-decoration: none;
  transition: background 0.18s ease, color 0.18s ease;
}
.nav-item:hover {
  background: var(--sf-primary-soft);
  color: var(--sf-primary);
}
.nav-item.router-link-active {
  background: var(--sf-primary);
  color: #fff;
}
.nav-label {
  font-size: 10px;
  line-height: 1;
  white-space: nowrap;
}

.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: var(--sf-radius-sm);
  background: transparent;
  color: var(--sf-sidebar-muted);
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease;
}
.theme-toggle:hover {
  background: var(--sf-primary-soft);
  color: var(--sf-primary);
}

/* 右侧主区域 */
.main {
  flex: 1;
  margin-left: var(--sf-sidebar-w);
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--sf-header-h);
  padding: 0 var(--sf-space-4);
  background: var(--sf-surface);
  border-bottom: 1px solid var(--sf-border);
}
.page-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.mock-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  color: var(--sf-primary);
  background: var(--sf-primary-soft);
  border: 1px solid var(--sf-primary-border);
}
.user {
  font-size: 13px;
  color: var(--sf-text-secondary);
}

/* GitHub 入口：图标 + Star 引导，悬停高亮 */
.gh-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 9px;
  border-radius: 10px;
  color: var(--sf-text-secondary);
  text-decoration: none;
  border: 1px solid var(--sf-border);
  transition: color 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}
.gh-link:hover {
  color: var(--sf-primary);
  border-color: var(--sf-primary-border);
  background: var(--sf-primary-soft);
}
.gh-star {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  line-height: 1;
}

.content {
  flex: 1;
  padding: var(--sf-space-4);
  min-width: 0;
  width: 100%;
  /* 全屏（如 1920）下限制内容宽度居中，避免行过长、信息密度被稀释 */
  max-width: 1480px;
  margin: 0 auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>