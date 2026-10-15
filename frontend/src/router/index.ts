import { createRouter, createWebHistory } from 'vue-router'
import type { IconName } from '@/components/common/SfIcon.vue'

/**
 * 路由表：应用壳连通全部页面切片入口（FS-0）。
 * 页面主体按切片推进实现；后续可扩展反馈详情 /auth（政务版统一身份认证）等。
 */
declare module 'vue-router' {
  interface RouteMeta {
    title: string
    icon?: IconName
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/pages/dashboard/DashboardPage.vue'),
      meta: { title: '总览', icon: 'dashboard' },
    },
    {
      path: '/feedback',
      name: 'feedback',
      component: () => import('@/pages/feedback/FeedbackListPage.vue'),
      meta: { title: '反馈管理', icon: 'feedback' },
    },
    {
      path: '/insights',
      name: 'insights',
      component: () => import('@/pages/insights/InsightsPage.vue'),
      meta: { title: '洞察与决策', icon: 'insights' },
    },
    {
      path: '/roadmap',
      name: 'roadmap',
      component: () => import('@/pages/roadmap/RoadmapPage.vue'),
      meta: { title: '路线图', icon: 'roadmap' },
    },
    {
      path: '/automation',
      name: 'automation',
      component: () => import('@/pages/automation/AutomationPage.vue'),
      meta: { title: 'AI 自动化', icon: 'automation' },
    },
    {
      path: '/business',
      name: 'business',
      component: () => import('@/pages/business/BusinessPage.vue'),
      meta: { title: '商务洞察', icon: 'briefcase' },
    },
    {
      path: '/gov',
      name: 'gov',
      component: () => import('@/pages/gov/GovPage.vue'),
      meta: { title: '政务适配', icon: 'gov' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/pages/settings/SettingsPage.vue'),
      meta: { title: '系统设置', icon: 'settings' },
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} - SignalFlow` : 'SignalFlow'
})

export default router