<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import { useSystemData } from '../composables/useSystemData'

const { loading, error, overview, insights, loadData } = useSystemData()

const cards = computed(() => {
  if (!overview.value) {
    return []
  }

  return [
    { label: '月度样本量', value: overview.value.dataset_rows },
    { label: '预测月份数', value: overview.value.forecast_months },
    { label: '模型数量', value: overview.value.model_count },
    { label: '图表数量', value: overview.value.chart_count },
  ]
})

const jumpLinks = [
  { to: '/data-center', label: '样本数据' },
  { to: '/metrics', label: '模型指标' },
  { to: '/forecast', label: '预测结果' },
  { to: '/charts', label: '图表中心' },
  { to: '/system', label: '系统设计' },
]

const insightCards = computed(() => {
  if (!insights.value) {
    return []
  }

  return [
    { label: 'RMSE 优选', value: insights.value.best_rmse_model || '-' },
    { label: 'MAPE 优选', value: insights.value.best_mape_model || '-' },
    { label: '峰值月份', value: insights.value.peak_forecast?.month || '-' },
    { label: '峰值模型', value: insights.value.peak_forecast?.model || '-' },
  ]
})

onMounted(() => loadData())
</script>

<template>
  <section class="page-stack">
    <div v-if="loading" class="plain-panel status-panel">系统数据加载中...</div>
    <div v-else-if="error" class="plain-panel status-panel error-panel">{{ error }}</div>

    <template v-else>
      <section class="plain-panel action-panel">
        <div class="quick-links">
          <RouterLink
            v-for="item in jumpLinks"
            :key="item.to"
            :to="item.to"
            class="mini-link"
          >
            {{ item.label }}
          </RouterLink>
        </div>
      </section>

      <section class="summary-row">
        <article v-for="card in cards" :key="card.label" class="plain-panel stat-box">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </article>
      </section>

      <section class="two-column">
        <article class="plain-panel">
          <div class="section-line">
            <h3>默认模型</h3>
            <RouterLink to="/metrics" class="mini-link">详情</RouterLink>
          </div>
          <div class="metric-stack">
            <div class="metric-row">
              <span>模型</span>
              <strong>{{ overview?.best_model?.name || '暂无' }}</strong>
            </div>
            <div class="metric-row">
              <span>MAE</span>
              <strong>{{ overview?.best_model?.mae ?? '-' }}</strong>
            </div>
            <div class="metric-row">
              <span>RMSE</span>
              <strong>{{ overview?.best_model?.rmse ?? '-' }}</strong>
            </div>
            <div class="metric-row">
              <span>MAPE</span>
              <strong>{{ overview?.best_model?.mape ?? '-' }}</strong>
            </div>
          </div>
        </article>

        <article class="plain-panel">
          <h3>运行概览</h3>
          <div class="mini-stat-grid">
            <div v-for="item in insightCards" :key="item.label" class="mini-stat-card">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </article>
      </section>
    </template>
  </section>
</template>
