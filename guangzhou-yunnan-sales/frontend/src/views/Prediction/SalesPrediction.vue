<template>
  <div class="prediction-page">
    <!-- 参数设置 -->
    <el-card shadow="never" class="param-card">
      <template #header><span>预测参数设置</span></template>
      <el-form :inline="true" :model="params">
        <el-form-item label="预测开始月份">
          <el-date-picker
            v-model="params.start_month"
            type="month"
            value-format="YYYY-MM"
            placeholder="选择月份"
            style="width:140px"
          />
        </el-form-item>
        <el-form-item label="预测结束月份">
          <el-date-picker
            v-model="params.end_month"
            type="month"
            value-format="YYYY-MM"
            placeholder="选择月份"
            style="width:140px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="DataAnalysis" :loading="running" @click="handleRun" v-if="isAdmin">
            执行预测
          </el-button>
          <el-button type="warning" icon="MagicStick" :loading="analyzing" @click="handleAnalyze" :disabled="tableData.length === 0">
            AI 分析
          </el-button>
          <el-button type="success" icon="Download" @click="handleExport">导出结果</el-button>
          <el-button @click="loadPredictions">刷新数据</el-button>
        </el-form-item>
      </el-form>
      <div class="model-info">
        <el-tag type="info" size="small">预测模型：SARIMA季节分解模型</el-tag>
        <el-text type="info" size="small" style="margin-left:12px">
          基于2024-2025年历史销量数据，结合季节性指数与节假日效应进行预测
        </el-text>
      </div>
    </el-card>

    <!-- 预测图表 -->
    <el-card shadow="never" class="chart-card" style="margin-top:16px">
      <template #header><span>销量预测折线图（万支）</span></template>
      <v-chart :option="chartOption" style="height:320px" autoresize />
    </el-card>

    <!-- 预测结果表 -->
    <el-card shadow="never" class="table-card" style="margin-top:16px">
      <template #header>
        <div class="card-header">
          <span>2026年3月 - 2027年2月 销量预测表</span>
          <el-tag type="success" size="small">共{{ tableData.length }}条预测记录</el-tag>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" border stripe style="width:100%">
        <el-table-column prop="month" label="月份" width="110" />
        <el-table-column label="预测销量(万支)" width="140" align="right">
          <template #default="{ row }">
            <span class="qty-val">{{ row.predicted_quantity }}</span>
          </template>
        </el-table-column>
        <el-table-column label="环比变化" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.mom_change_pct === null || row.mom_change_pct === undefined">–</span>
            <el-tag
              v-else
              :type="row.mom_change_pct >= 0 ? 'success' : 'danger'"
              size="small"
            >
              {{ row.mom_change_pct >= 0 ? '+' : '' }}{{ row.mom_change_pct }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="key_factors" label="预测关键因素" min-width="180" />
        <el-table-column prop="model_type" label="预测模型" width="110" />
      </el-table>
    </el-card>
    <!-- AI 分析结果 -->
    <el-card shadow="never" class="analysis-card" style="margin-top:16px" v-if="aiAnalysis">
      <template #header><span>AI 预测分析</span></template>
      <div class="analysis-text">{{ aiAnalysis }}</div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { getPredictions, runPrediction, exportPredictions, analyzeWithAI } from '@/api/predictions'

export default {
  name: 'SalesPrediction',
  setup() {
    const store = useStore()
    const isAdmin = computed(() => store.getters.isAdmin)
    const loading = ref(false)
    const running = ref(false)
    const analyzing = ref(false)
    const tableData = ref([])
    const aiAnalysis = ref('')
    const params = reactive({ start_month: '2026-03', end_month: '2027-02' })
    const chartOption = ref({})

    const buildChart = (data) => {
      const months = data.map(d => d.month)
      const values = data.map(d => d.predicted_quantity)
      const momValues = data.map(d => d.mom_change_pct)

      chartOption.value = {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const d = params[0]
            const row = data[d.dataIndex]
            let s = `<b>${d.name}</b><br/>`
            s += `预测销量：<b>${d.value}</b> 万支<br/>`
            if (row.mom_change_pct !== null && row.mom_change_pct !== undefined) {
              const sign = row.mom_change_pct >= 0 ? '+' : ''
              s += `环比变化：${sign}${row.mom_change_pct}%<br/>`
            }
            s += `关键因素：${row.key_factors}`
            return s
          }
        },
        legend: { data: ['预测销量(万支)'] },
        xAxis: { type: 'category', data: months, axisLabel: { rotate: 30, fontSize: 11 } },
        yAxis: [
          { type: 'value', name: '销量(万支)', min: 40 },
        ],
        series: [{
          name: '预测销量(万支)',
          type: 'line',
          data: values,
          smooth: true,
          lineStyle: { color: '#e6a23c', width: 3 },
          itemStyle: { color: '#e6a23c' },
          areaStyle: { opacity: 0.12, color: '#e6a23c' },
          markPoint: {
            data: [
              { type: 'max', name: '最高', itemStyle: { color: '#f56c6c' } },
              { type: 'min', name: '最低', itemStyle: { color: '#409eff' } },
            ]
          },
          label: { show: true, formatter: '{c}', fontSize: 11, position: 'top' },
        }],
        grid: { left: 60, right: 30, bottom: 60, top: 40 },
      }
    }

    const loadPredictions = async () => {
      loading.value = true
      try {
        const res = await getPredictions({
          start_month: params.start_month,
          end_month: params.end_month,
        })
        tableData.value = res.data
        if (res.data.length > 0) {
          buildChart(res.data)
        }
      } finally {
        loading.value = false
      }
    }

    const handleRun = async () => {
      running.value = true
      try {
        const res = await runPrediction({
          start_month: params.start_month,
          end_month: params.end_month,
        })
        ElMessage.success(res.data.detail)
        await loadPredictions()
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '预测失败')
      } finally {
        running.value = false
      }
    }

    const handleExport = async () => {
      const res = await exportPredictions({
        start_month: params.start_month,
        end_month: params.end_month,
      })
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = 'prediction_results.csv'
      a.click()
      URL.revokeObjectURL(url)
    }

    onMounted(loadPredictions)

    const handleAnalyze = async () => {
      analyzing.value = true
      aiAnalysis.value = ''
      try {
        const res = await analyzeWithAI(tableData.value)
        aiAnalysis.value = res.data.analysis
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || 'AI 分析失败')
      } finally {
        analyzing.value = false
      }
    }

    return { isAdmin, loading, running, analyzing, tableData, aiAnalysis, params, chartOption, loadPredictions, handleRun, handleAnalyze, handleExport }
  }
}
</script>

<style scoped>
.prediction-page { padding: 4px; }
.param-card { }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.model-info { margin-top: 12px; display: flex; align-items: center; }
.qty-val { font-weight: 600; color: #e6a23c; font-size: 15px; }
.analysis-text { white-space: pre-wrap; line-height: 1.8; color: #606266; }
</style>
