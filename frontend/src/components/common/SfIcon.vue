<script setup lang="ts">
/**
 * 内联 SVG 图标集（本地化，不引 CDN / webfont，政务"数据不出域"约束）。
 * 全部使用 currentColor，尺寸/颜色由外部控制。
 */
defineProps<{ name: IconName; size?: number }>()

export type IconName =
  | 'logo'
  | 'dashboard'
  | 'feedback'
  | 'insights'
  | 'roadmap'
  | 'gov'
  | 'settings'
  | 'sun'
  | 'moon'
  | 'search'
  | 'chevron-right'
  | 'trend-up'
  | 'trend-down'
  | 'trend-flat'
  | 'check'
  | 'close'
  | 'filter'
  | 'plus'
  | 'send'
  | 'clock'
  | 'alert'
  | 'refresh'
  | 'external'
  | 'file'
  | 'term'
  | 'shield'
  | 'link'
  | 'magic'
  | 'spinner'
  | 'circle'
  | 'label'
  | 'chat'
  | 'sentiment'
  | 'checklist'
</script>

<template>
  <svg
    :width="size ?? 20"
    :height="size ?? 20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- 品牌：信号波形 -->
    <path v-if="name === 'logo'" d="M3 12h3l2-5 3 10 2.5-7 1.5 2H21" />
    <!-- 总览：栅格 -->
    <template v-else-if="name === 'dashboard'">
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.5" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.5" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.5" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="1.5" />
    </template>
    <!-- 反馈：消息气泡 -->
    <template v-else-if="name === 'feedback'">
      <path d="M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v7a2.5 2.5 0 0 1-2.5 2.5H9l-4.2 3.4c-.6.5-1.5.1-1.5-.7V6.5Z" />
      <path d="M8 9h8M8 12.5h5" />
    </template>
    <!-- 洞察：灯泡 -->
    <template v-else-if="name === 'insights'">
      <path d="M9 18h6M10 21h4" />
      <path d="M12 3a6 6 0 0 1 3.5 10.9c-.7.6-1 1.4-1 2.1h-5c0-.7-.3-1.5-1-2.1A6 6 0 0 1 12 3Z" />
    </template>
    <!-- 路线图：里程碑旗标 -->
    <template v-else-if="name === 'roadmap'">
      <path d="M5 21V4" />
      <path d="M5 4.5h10l-1.5 3L15 10.5H5" />
    </template>
    <!-- 政务：盾牌 -->
    <template v-else-if="name === 'gov'">
      <path d="M12 3l7 2.5v5c0 4.6-3 7.6-7 9.5-4-1.9-7-4.9-7-9.5v-5L12 3Z" />
      <path d="M9.5 12l1.8 1.8 3.4-3.6" />
    </template>
    <!-- 设置：齿轮 -->
    <template v-else-if="name === 'settings'">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2.8v3M12 18.2v3M21.2 12h-3M5.8 12h-3M18.5 5.5l-2.1 2.1M7.6 16.4l-2.1 2.1M18.5 18.5l-2.1-2.1M7.6 7.6 5.5 5.5" />
    </template>
    <template v-else-if="name === 'sun'">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2.8v2.2M12 19v2.2M2.8 12H5M19 12h2.2M5 5l1.6 1.6M17.4 17.4 19 19M19 5l-1.6 1.6M6.6 17.4 5 19" />
    </template>
    <template v-else-if="name === 'moon'">
      <path d="M20 14.5A8 8 0 0 1 9.5 4 7 7 0 1 0 20 14.5Z" />
    </template>
    <template v-else-if="name === 'search'">
      <circle cx="11" cy="11" r="6.5" />
      <path d="m16 16 4.5 4.5" />
    </template>
    <template v-else-if="name === 'chevron-right'">
      <path d="m9 5.5 6.5 6.5L9 18.5" />
    </template>
    <template v-else-if="name === 'trend-up'">
      <path d="M3.5 17.5 10 11l3.5 3.5L20.5 6" />
      <path d="M15 6h5.5v5.5" />
    </template>
    <template v-else-if="name === 'trend-down'">
      <path d="M3.5 6.5 10 13l3.5-3.5L20.5 18" />
      <path d="M15 18h5.5v-5.5" />
    </template>
    <template v-else-if="name === 'trend-flat'">
      <path d="M3.5 12h17" />
    </template>
    <template v-else-if="name === 'check'">
      <path d="m4.5 12.5 5 5L19.5 6.5" />
    </template>
    <template v-else-if="name === 'close'">
      <path d="M6 6l12 12M18 6 6 18" />
    </template>
    <!-- 筛选：漏斗 -->
    <template v-else-if="name === 'filter'">
      <path d="M4 5h16l-6 7v5l-4 2v-7L4 5Z" />
    </template>
    <!-- 新建：加号 -->
    <template v-else-if="name === 'plus'">
      <path d="M12 5v14M5 12h14" />
    </template>
    <!-- 回传/发送：纸飞机 -->
    <template v-else-if="name === 'send'">
      <path d="M21 3 10.5 13.5M21 3l-6.8 18-3.7-7.7L2.7 9.8 21 3Z" />
    </template>
    <!-- 时钟：待处理/时长 -->
    <template v-else-if="name === 'clock'">
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7v5l3.5 2" />
    </template>
    <!-- 预警：三角感叹号 -->
    <template v-else-if="name === 'alert'">
      <path d="M12 4 2.8 19.5h18.4L12 4Z" />
      <path d="M12 10v4M12 16.8v.2" />
    </template>
    <!-- 刷新：旋转箭头 -->
    <template v-else-if="name === 'refresh'">
      <path d="M20 12a8 8 0 1 1-2.34-5.66" />
      <path d="M20 3v4h-4" />
    </template>
    <!-- 外链：跳出 -->
    <template v-else-if="name === 'external'">
      <path d="M14 4h6v6M20 4l-9 9" />
      <path d="M18 13v6a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 4 19V8a1.5 1.5 0 0 1 1.5-1.5H11" />
    </template>
    <!-- 文档：材料/清单 -->
    <template v-else-if="name === 'file'">
      <path d="M6 3h8l4 4v14H6V3Z" />
      <path d="M14 3v4h4M9.5 12h5M9.5 15.5h5" />
    </template>
    <!-- 话术/术语：对话线 -->
    <template v-else-if="name === 'term'">
      <path d="M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v7a2.5 2.5 0 0 1-2.5 2.5H9l-4.2 3.2V6.5Z" />
      <path d="M8.5 9h7M8.5 12h4" />
    </template>
    <!-- 盾牌：政务认证/督办 -->
    <template v-else-if="name === 'shield'">
      <path d="M12 3l7 2.5v5c0 4.6-3 7.6-7 9.5-4-1.9-7-4.9-7-9.5v-5L12 3Z" />
    </template>
    <!-- 链接：渠道接入 -->
    <template v-else-if="name === 'link'">
      <path d="M10 14a4.5 4.5 0 0 0 6.5.5l3-3a4.5 4.5 0 0 0-6.4-6.4l-1.5 1.5" />
      <path d="M14 10a4.5 4.5 0 0 0-6.5-.5l-3 3a4.5 4.5 0 0 0 6.4 6.4l1.5-1.5" />
    </template>
    <!-- 魔法/智能：AI 自动化 -->
    <template v-else-if="name === 'magic'">
      <path d="M12 2v4M12 18v4M2 12h4M18 12h4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
    </template>
    <!-- 旋转/加载：工作流运行中 -->
    <template v-else-if="name === 'spinner'">
      <path d="M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20" stroke-dasharray="32 16" />
    </template>
    <!-- 空心圆：占位 -->
    <template v-else-if="name === 'circle'">
      <circle cx="12" cy="12" r="9" />
    </template>
    <!-- 标签：自动分类 -->
    <template v-else-if="name === 'label'">
      <path d="M4 5.5A1.5 1.5 0 0 1 5.5 4h6a1.5 1.5 0 0 1 1.1.5l5.4 5.4a1.5 1.5 0 0 1 0 2.2l-5.4 5.4a1.5 1.5 0 0 1-2.2 0l-5.4-5.4A1.5 1.5 0 0 1 4 11.5v-6Z" />
      <circle cx="8" cy="8.5" r="1" fill="currentColor" stroke="none" />
    </template>
    <!-- 对话气泡：消息/回复 -->
    <template v-else-if="name === 'chat'">
      <path d="M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v7a2.5 2.5 0 0 1-2.5 2.5H9l-4.2 3.4c-.6.5-1.5.1-1.5-.7V6.5Z" />
      <path d="M8 9h8M8 12.5h5" />
    </template>
    <!-- 情感/心形：情感监测 -->
    <template v-else-if="name === 'sentiment'">
      <path d="M12 21a9 9 0 1 1 0-18 9 9 0 0 1 0 18Z" />
      <path d="M9 10h.01M15 10h.01" />
      <path d="M9.5 14.5a3.5 3.5 0 0 0 5 0" />
    </template>
    <!-- 清单：材料校验 -->
    <template v-else-if="name === 'checklist'">
      <path d="M4 6h16M4 12h16M4 18h10" />
      <path d="M18 16l1.5 1.5L22 15" />
    </template>
  </svg>
</template>