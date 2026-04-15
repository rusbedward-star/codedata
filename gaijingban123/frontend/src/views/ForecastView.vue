<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import DataTable from '../components/DataTable.vue'
import { useSystemData } from '../composables/useSystemData'
import { getAiAnalysis, getModelDetail } from '../api'

const { loading, error, forecast, forecastColumns, loadData } = useSystemData()
const monthKeyword = ref('')
const selectedModel = ref('随机森林')
const modelDetail = ref(null)
const aiAnalysis = ref('')
const aiError = ref('')
const analyzing = ref(false)

const modelColumns = computed(() =>
  forecastColumns.value.filter((item) => item !== '月份'),
)

const filteredRows = computed(() => {
  if (!monthKeyword.value.trim()) {
    return forecast.value
  }
  return forecast.value.filter((row) => row['月份']?.includes(monthKeyword.value.trim()))
})

function fmtVal(v) {
  const n = parseFloat(v)
  return isNaN(n) ? v : `${n.toFixed(2)} 万支`
}

const formattedRows = computed(() =>
  filteredRows.value.map((row) => {
    const out = {}
    for (const col of forecastColumns.value) {
      out[col] = col === '月份' ? row[col] : fmtVal(row[col])
    }
    return out
  }),
)

const selectedPreview = computed(() => {
  if (!selectedModel.value) {
    return []
  }
  return filteredRows.value.slice(0, 6).map((row) => ({
    month: row['月份'],
    value: fmtVal(row[selectedModel.value]),
  }))
})

async function loadModelDetail(modelName) {
  if (!modelName) {
    modelDetail.value = null
    return
  }
  modelDetail.value = await getModelDetail(modelName)
}

async function loadAiAnalysis() {
  if (!selectedModel.value) {
    aiAnalysis.value = ''
    aiError.value = ''
    return
  }

  analyzing.value = true
  aiError.value = ''
  try {
    const response = await getAiAnalysis(
      selectedModel.value,
      filteredRows.value.map((row) => row['月份']).filter(Boolean),
    )
    aiAnalysis.value = response.analysis || ''
  } catch (loadError) {
    aiAnalysis.value = ''
    aiError.value = loadError.message || 'AI 分析失败'
  } finally {
    analyzing.value = false
  }
}

watch(selectedModel, (modelName) => {
  aiAnalysis.value = ''
  aiError.value = ''
  loadModelDetail(modelName)
})

onMounted(async () => {
  await loadData()
  if (modelColumns.value.length && !modelColumns.value.includes(selectedModel.value)) {
    selectedModel.value = modelColumns.value[0]
  }
  await loadModelDetail(selectedModel.value)
})
</script>

<template>
  <section class="page-stack">
    <div v-if="loading" class="plain-panel status-panel">系统数据加载中...</div>
    <div v-else-if="error" class="plain-panel status-panel error-panel">{{ error }}</div>

    <template v-else>
      <section class="two-column">
        <article class="plain-panel">
          <h3>查询</h3>
          <div class="form-grid">
            <label>
              <span>月份检索</span>
              <input v-model="monthKeyword" placeholder="如 2026-06" />
            </label>
            <label>
              <span>重点模型</span>
              <select v-model="selectedModel">
                <option v-for="item in modelColumns" :key="item" :value="item">{{ item }}</option>
              </select>
            </label>
          </div>
          <div class="button-row">
            <button
              type="button"
              class="action-button"
              :disabled="analyzing || !selectedModel"
              @click="loadAiAnalysis"
            >
              {{ analyzing ? '星火分析中...' : '星火 AI 分析' }}
            </button>
          </div>
        </article>

        <article class="plain-panel">
          <h3>模型详情</h3>
          <div v-if="modelDetail" class="detail-row">
            <span>模型：{{ modelDetail.model }}</span>
            <span>MAE：{{ modelDetail.metrics.MAE }}</span>
            <span>RMSE：{{ modelDetail.metrics.RMSE }}</span>
            <span>MAPE：{{ modelDetail.metrics['MAPE(%)'] }}</span>
          </div>
          <ul class="simple-list">
            <li v-for="item in selectedPreview" :key="item.month">
              {{ item.month }}：{{ item.value }}
            </li>
          </ul>
        </article>
      </section>

      <section class="plain-panel">
        <h3>预测表</h3>
        <DataTable :columns="forecastColumns" :rows="formattedRows" />
      </section>

      <section v-if="aiAnalysis || aiError" class="plain-panel analysis-panel">
        <h3>星火分析</h3>
        <p v-if="aiAnalysis" class="analysis-text">{{ aiAnalysis }}</p>
        <p v-else class="analysis-text error-text">{{ aiError }}</p>
      </section>
    </template>
  </section>
</template>
