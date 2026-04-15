<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import DataTable from '../components/DataTable.vue'
import { useSystemData } from '../composables/useSystemData'

const { loading, error, metrics, bestModel, loadData } = useSystemData()

const columns = computed(() => (metrics.value.length ? Object.keys(metrics.value[0]) : []))

const bestMapeModel = computed(() => {
  if (!metrics.value.length) {
    return ''
  }
  return [...metrics.value].sort((a, b) => parseFloat(a['MAPE']) - parseFloat(b['MAPE']))[0]['模型']
})

onMounted(() => loadData())
</script>

<template>
  <section class="page-stack">
    <div v-if="loading" class="plain-panel status-panel">系统数据加载中...</div>
    <div v-else-if="error" class="plain-panel status-panel error-panel">{{ error }}</div>

    <template v-else>
      <section class="summary-row compact-three">
        <article class="plain-panel stat-box">
          <span>RMSE 最优模型</span>
          <strong>{{ bestModel }}</strong>
        </article>
        <article class="plain-panel stat-box">
          <span>MAPE 最优模型</span>
          <strong>{{ bestMapeModel }}</strong>
        </article>
        <article class="plain-panel stat-box">
          <span>图表跳转</span>
          <strong><RouterLink to="/charts?category=metrics">指标页</RouterLink></strong>
        </article>
      </section>

      <section class="plain-panel">
        <div class="section-line">
          <h3>评估结果</h3>
          <RouterLink to="/charts?category=metrics" class="mini-link">图表</RouterLink>
        </div>
        <DataTable :columns="columns" :rows="metrics" :highlight-model="bestModel" />
      </section>
    </template>
  </section>
</template>
