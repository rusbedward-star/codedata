<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

import {
  createSampleData,
  deleteSampleData,
  getForecastJob,
  importSampleData,
  startForecastJob,
  updateSampleData,
} from '../api'
import { useSystemData } from '../composables/useSystemData'

const { loading, error, overview, sampleColumns, sampleData, loadData } = useSystemData()
const saving = ref(false)
const submitError = ref('')
const submitMessage = ref('')
const editingDate = ref('')
const importFile = ref(null)

const forecastJobRunning = ref(false)
const forecastJobMessage = ref('')
const forecastJobError = ref('')
let forecastJobPollTimer = null

const form = reactive({
  date: '',
  sales: '',
  last_month_sales: '',
  last_year_same_month: '',
  is_holiday: '0',
  is_promo: '0',
  region: '',
  product_series: '',
})

const stackItems = computed(() => overview.value?.tech_stack || [])
const summaryItems = computed(() => {
  if (!overview.value) {
    return []
  }

  return [
    { label: '样本条数', value: overview.value.dataset_rows },
    { label: '起始月份', value: overview.value.date_range?.start || '-' },
    { label: '结束月份', value: overview.value.date_range?.end || '-' },
    { label: '模型数量', value: overview.value.model_count },
  ]
})

const regionOptions = computed(() =>
  [...new Set(sampleData.value.map((item) => item['地区']).filter(Boolean))],
)

const seriesOptions = computed(() =>
  [...new Set(sampleData.value.map((item) => item['产品系列']).filter(Boolean))],
)

function fillForm(row = null) {
  form.date = row?.['日期'] || row?.date || ''
  form.sales = row?.['销售额(万支)'] ?? row?.sales ?? ''
  form.last_month_sales = row?.['上月销量(万支)'] ?? row?.last_month_sales ?? ''
  form.last_year_same_month = row?.['去年同月销量(万支)'] ?? row?.last_year_same_month ?? ''
  form.is_holiday = String(row?.['是否节假日'] ?? row?.is_holiday ?? '0')
  form.is_promo = String(row?.['是否促销'] ?? row?.is_promo ?? '0')
  form.region = row?.['地区'] || row?.region || ''
  form.product_series = row?.['产品系列'] || row?.product_series || ''
}

function startCreate() {
  editingDate.value = ''
  submitError.value = ''
  submitMessage.value = ''
  fillForm()
}

function startEdit(row) {
  editingDate.value = row['日期'] || row.date
  submitError.value = ''
  submitMessage.value = ''
  fillForm(row)
}

async function submitForm() {
  saving.value = true
  submitError.value = ''
  submitMessage.value = ''

  const payload = {
    date: form.date,
    sales: form.sales,
    last_month_sales: form.last_month_sales,
    last_year_same_month: form.last_year_same_month,
    is_holiday: form.is_holiday,
    is_promo: form.is_promo,
    region: form.region,
    product_series: form.product_series,
  }

  try {
    const response = editingDate.value
      ? await updateSampleData(editingDate.value, payload)
      : await createSampleData(payload)

    await loadData(true)
    submitMessage.value =
      response.notice || (editingDate.value ? '样本数据已更新' : '样本数据已新增')
    editingDate.value = payload.date
    fillForm(payload)
  } catch (requestError) {
    submitError.value = requestError.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function removeRow(row) {
  const rowDate = row['日期'] || row.date
  if (!window.confirm(`确认删除 ${rowDate} 这条月度样本吗？`)) {
    return
  }

  saving.value = true
  submitError.value = ''
  submitMessage.value = ''

  try {
    const response = await deleteSampleData(rowDate)
    await loadData(true)
    if (editingDate.value === rowDate) {
      startCreate()
    }
    submitMessage.value = response.notice || '样本数据已删除'
  } catch (requestError) {
    submitError.value = requestError.message || '删除失败'
  } finally {
    saving.value = false
  }
}

async function importExcel() {
  if (!importFile.value) {
    submitError.value = '请先选择 Excel 文件'
    return
  }
  saving.value = true
  submitError.value = ''
  submitMessage.value = ''
  try {
    const result = await importSampleData(importFile.value)
    await loadData(true)
    const msg = `导入完成：共 ${result.total_rows} 行，成功 ${result.imported_count} 条，跳过 ${result.skipped_count} 条`
    submitMessage.value = result.skipped_count > 0
      ? `${msg}（跳过月份：${result.skipped_dates.join('、')}）`
      : msg
    importFile.value = null
  } catch (importError) {
    submitError.value = importError.message || 'Excel 导入失败'
  } finally {
    saving.value = false
  }
}

async function runForecastScript() {
  forecastJobRunning.value = true
  forecastJobMessage.value = '正在启动预测任务...'
  forecastJobError.value = ''

  try {
    const response = await startForecastJob()
    const jobId = response.job_id

    forecastJobMessage.value = '预测任务运行中，请稍候...'

    // Poll job status every 2 seconds
    forecastJobPollTimer = setInterval(async () => {
      try {
        const job = await getForecastJob(jobId)

        if (job.status === 'succeeded') {
          clearInterval(forecastJobPollTimer)
          forecastJobPollTimer = null
          forecastJobRunning.value = false
          forecastJobMessage.value = '预测任务完成！正在刷新数据...'

          // Reload all data to reflect new results
          await loadData(true)
          forecastJobMessage.value = '预测结果已更新'

          // Clear message after 5 seconds
          setTimeout(() => {
            forecastJobMessage.value = ''
          }, 5000)
        } else if (job.status === 'failed') {
          clearInterval(forecastJobPollTimer)
          forecastJobPollTimer = null
          forecastJobRunning.value = false
          forecastJobError.value = job.error_message || '预测任务失败'
        }
      } catch (pollError) {
        clearInterval(forecastJobPollTimer)
        forecastJobPollTimer = null
        forecastJobRunning.value = false
        forecastJobError.value = '无法获取任务状态'
      }
    }, 2000)
  } catch (startError) {
    forecastJobRunning.value = false
    forecastJobError.value = startError.message || '启动预测任务失败'
  }
}

onMounted(async () => {
  await loadData()
  fillForm()
})

onUnmounted(() => {
  if (forecastJobPollTimer) {
    clearInterval(forecastJobPollTimer)
  }
})
</script>

<template>
  <section class="page-stack">
    <div v-if="loading" class="plain-panel status-panel">系统数据加载中...</div>
    <div v-else-if="error" class="plain-panel status-panel error-panel">{{ error }}</div>

    <template v-else>
      <section class="summary-row">
        <article v-for="item in summaryItems" :key="item.label" class="plain-panel stat-box">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </section>

      <section class="plain-panel">
        <div class="section-line">
          <h3>月度样本</h3>
          <div class="tag-list">
            <span v-for="item in stackItems" :key="item">{{ item }}</span>
          </div>
        </div>
        <p class="muted">
          这里可以直接新增、修改、删除月度样本。保存后会写回源数据文件，但模型评估结果和预测图不会自动重算。
        </p>
      </section>

      <section class="plain-panel">
        <div class="section-line">
          <h3>{{ editingDate ? `编辑样本 ${editingDate}` : '新增月度样本' }}</h3>
          <div class="quick-links">
            <button type="button" class="mini-link mini-button" @click="startCreate">切换到新增</button>
          </div>
        </div>

        <div class="editor-grid">
          <label>
            <span>月份</span>
            <input v-model="form.date" type="month" />
          </label>
          <label>
            <span>销量</span>
            <input v-model="form.sales" type="number" step="0.01" placeholder="如 85.67" />
          </label>
          <label>
            <span>上月销量</span>
            <input
              v-model="form.last_month_sales"
              type="number"
              step="0.01"
              placeholder="如 78.23"
            />
          </label>
          <label>
            <span>去年同月销量</span>
            <input
              v-model="form.last_year_same_month"
              type="number"
              step="0.01"
              placeholder="可留空"
            />
          </label>
          <label>
            <span>节假日</span>
            <select v-model="form.is_holiday">
              <option value="0">否</option>
              <option value="1">是</option>
            </select>
          </label>
          <label>
            <span>促销</span>
            <select v-model="form.is_promo">
              <option value="0">否</option>
              <option value="1">是</option>
            </select>
          </label>
          <label>
            <span>地区</span>
            <input v-model="form.region" list="region-options" placeholder="如 天河区" />
          </label>
          <label>
            <span>产品系列</span>
            <input
              v-model="form.product_series"
              list="series-options"
              placeholder="如 冰柠系列"
            />
          </label>
        </div>

        <datalist id="region-options">
          <option v-for="item in regionOptions" :key="item" :value="item"></option>
        </datalist>
        <datalist id="series-options">
          <option v-for="item in seriesOptions" :key="item" :value="item"></option>
        </datalist>

        <div class="button-row editor-actions">
          <button type="button" class="action-button" :disabled="saving" @click="submitForm">
            {{ saving ? '保存中...' : editingDate ? '保存修改' : '新增数据' }}
          </button>
          <button type="button" class="ghost-button" :disabled="saving" @click="startCreate">
            清空表单
          </button>
          <button
            type="button"
            class="ghost-button"
            :disabled="forecastJobRunning || saving"
            @click="runForecastScript"
          >
            {{ forecastJobRunning ? '预测任务运行中...' : '重新运行预测脚本' }}
          </button>
          <label class="ghost-button" style="display: inline-flex; align-items: center; cursor: pointer">
            <input
              type="file"
              accept=".xlsx,.xls"
              style="display: none"
              @change="(event) => { importFile = event.target.files?.[0] || null }"
            />
            导入 Excel
          </label>
          <button type="button" class="ghost-button" :disabled="saving || !importFile" @click="importExcel">
            {{ saving ? '处理中...' : '开始导入' }}
          </button>
        </div>

        <p v-if="importFile" class="muted">已选择文件：{{ importFile.name }}</p>
        <p v-if="forecastJobMessage" class="inline-message success-text">{{ forecastJobMessage }}</p>
        <p v-if="forecastJobError" class="inline-message error-text">{{ forecastJobError }}</p>
        <p v-if="submitMessage" class="inline-message success-text">{{ submitMessage }}</p>
        <p v-if="submitError" class="inline-message error-text">{{ submitError }}</p>
      </section>

      <section class="plain-panel">
        <div class="section-line">
          <h3>全部样本</h3>
          <span class="muted">点“编辑”后会把该行带入上方表单</span>
        </div>
        <div class="table-box">
          <table>
            <thead>
              <tr>
                <th v-for="column in sampleColumns" :key="column">{{ column }}</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in sampleData" :key="row.date">
                <td v-for="column in sampleColumns" :key="column">{{ row[column] }}</td>
                <td>
                  <div class="table-action-row">
                    <button type="button" class="table-button" @click="startEdit(row)">编辑</button>
                    <button type="button" class="table-button danger-button" @click="removeRow(row)">
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </section>
</template>
