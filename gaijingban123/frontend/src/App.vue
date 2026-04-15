<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()

const navigation = [
  { to: '/', label: '系统首页' },
  { to: '/data-center', label: '数据中心' },
  { to: '/metrics', label: '模型评估' },
  { to: '/forecast', label: '预测结果' },
  { to: '/charts', label: '图表中心' },
  { to: '/system', label: '系统设计' },
]

const pageTitle = computed(() => {
  const current = navigation.find((item) => item.to === route.path)
  return current?.label || '系统页面'
})
</script>

<template>
  <div class="app-shell">
    <aside class="side-nav">
      <div class="brand-block">
        <h1>牙膏销量分析与预测系统</h1>
      </div>

      <nav class="nav-list">
        <RouterLink
          v-for="item in navigation"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ active: route.path === item.to }"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>

    <div class="main-layout">
      <header class="top-bar">
        <div>
          <h2>{{ pageTitle }}</h2>
        </div>
        <div class="top-summary">
          <span>Vue 3</span>
          <span>Django</span>
          <span>PyTorch</span>
        </div>
      </header>

      <main class="content-area">
        <RouterView />
      </main>
    </div>
  </div>
</template>
