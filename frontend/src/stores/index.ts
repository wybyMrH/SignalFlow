import { ref } from 'vue'
import { defineStore } from 'pinia'

/**
 * 全局应用状态：品牌信息 + 主题切换（浅/深，persist 到 localStorage，
 * 通过 html.dark 类切换 CSS 变量主题，见 styles/main.css 与
 * docs/frontend-development-plan.md §5.1）。
 */
type Theme = 'light' | 'dark'

const THEME_KEY = 'sf-theme'

function readInitialTheme(): Theme {
  const saved = localStorage.getItem(THEME_KEY)
  return saved === 'dark' ? 'dark' : 'light'
}

export const useAppStore = defineStore('app', () => {
  const appName = ref('SignalFlow')
  const theme = ref<Theme>(readInitialTheme())

  function applyTheme(next: Theme) {
    theme.value = next
    document.documentElement.classList.toggle('dark', next === 'dark')
    localStorage.setItem(THEME_KEY, next)
  }

  function toggleTheme() {
    applyTheme(theme.value === 'light' ? 'dark' : 'light')
  }

  // 入口初始化一次
  applyTheme(theme.value)

  return { appName, theme, toggleTheme }
})

export * from './feedback'
export * from './insights'