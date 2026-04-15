<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useSystemData } from '../composables/useSystemData'

const { loading, error, forecastColumns, sampleData, loadData } = useSystemData()
const selectedModel = ref('随机森林')
const selectedSeries = ref('')

const modelOptions = computed(() =>
  forecastColumns.value.filter((item) => item !== '月份'),
)

const seriesOptions = computed(() =>
  ['全部系列', ...[...new Set(sampleData.value.map((item) => item['产品系列']).filter(Boolean))]],
)

const chartFrames = computed(() => {
  const frames = []
  frames.push(
    { key: 'sales-trend', title: '历史销量趋势图', src: '/api/charts/sales-trend/' },
    { key: 'forecast-multi', title: '多模型未来预测图', src: '/api/charts/forecast-multi/' },
  )

  if (selectedModel.value) {
    frames.push({
      key: `model-${selectedModel.value}`,
      title: `${selectedModel.value} 预测图`,
      src: `/api/charts/model-forecast/?model=${encodeURIComponent(selectedModel.value)}`,
    })

    const seriesParam = selectedSeries.value && selectedSeries.value !== '全部系列'
      ? `&series=${encodeURIComponent(selectedSeries.value)}`
      : ''
    frames.push({
      key: `series-${selectedModel.value}-${selectedSeries.value}`,
      title: selectedSeries.value && selectedSeries.value !== '全部系列'
        ? `${selectedSeries.value} 未来销量预测`
        : '各系列未来销量预测',
      src: `/api/charts/series-forecast/?model=${encodeURIComponent(selectedModel.value)}${seriesParam}`,
    })
  }

  return frames
})

watch(modelOptions, (items) => {
  if (items.length && !items.includes(selectedModel.value)) {
    selectedModel.value = items[0]
  }
})

onMounted(async () => {
  await loadData()
  if (modelOptions.value.length && !modelOptions.value.includes(selectedModel.value)) {
    selectedModel.value = modelOptions.value[0]
  }
})
</script>

<template>
  <section class="page-stack">
    <div v-if="loading" class="plain-panel status-panel">系统数据加载中...</div>
    <div v-else-if="error" class="plain-panel status-panel error-panel">{{ error }}</div>

    <template v-else>
      <section class="plain-panel">
        <div class="section-line">
          <h3>图表筛选</h3>
          <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
            <label style="display: flex; gap: 6px; align-items: center;">
              <span class="muted">模型</span>
              <select v-model="selectedModel" class="inline-select">
                <option v-for="item in modelOptions" :key="item" :value="item">{{ item }}</option>
              </select>
            </label>
            <label style="display: flex; gap: 6px; align-items: center;">
              <span class="muted">系列</span>
              <select v-model="selectedSeries" class="inline-select">
                <option v-for="item in seriesOptions" :key="item" :value="item">{{ item }}</option>
              </select>
            </label>
          </div>
        </div>
      </section>

      <section class="chart-grid">
        <article v-for="frame in chartFrames" :key="frame.key" class="plain-panel pyecharts-card">
          <h3>{{ frame.title }}</h3>
          <iframe :src="frame.src" :title="frame.title" class="chart-frame"></iframe>
        </article>
      </section>
    </template>
  </section>
</template>
