<template>
  <div class="dashboard">
    <!-- KPI卡片 -->
    <el-row :gutter="20" class="kpi-row">
      <el-col :span="6" v-for="card in kpiCards" :key="card.label">
        <el-card class="kpi-card" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-icon" :style="{ background: card.color }">
              <el-icon size="28" color="#fff"><component :is="card.icon" /></el-icon>
            </div>
            <div class="kpi-info">
              <div class="kpi-value">{{ card.value }}</div>
              <div class="kpi-label">{{ card.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>近两年月度销售趋势（万支）</span>
              <el-select v-model="trendYear" size="small" style="width:100px" @change="loadTrend">
                <el-option label="2024年" value="2024" />
                <el-option label="2025年" value="2025" />
                <el-option label="全部" value="" />
              </el-select>
            </div>
          </template>
          <v-chart :option="trendOption" style="height:300px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>产品销售占比</span></template>
          <v-chart :option="pieOption" style="height:300px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>区域销售分布（万支）</span></template>
          <v-chart :option="regionOption" style="height:280px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>渠道销售占比</span></template>
          <v-chart :option="channelOption" style="height:280px" autoresize />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { getSalesTrend, getProductMix, getRegionDist, getChannelDist, getSummary } from '@/api/analytics'

export default {
  name: 'Dashboard',
  setup() {
    const trendYear = ref('')
    const kpiCards = ref([
      { label: '总销量（万支）', value: '–', icon: 'Box', color: '#409eff' },
      { label: '总销售额（万元）', value: '–', icon: 'Money', color: '#67c23a' },
      { label: '2025年销量（万支）', value: '–', icon: 'TrendCharts', color: '#e6a23c' },
      { label: '年同比增长', value: '–', icon: 'DataAnalysis', color: '#f56c6c' },
    ])

    const trendOption = ref({})
    const pieOption = ref({})
    const regionOption = ref({})
    const channelOption = ref({})

    const loadSummary = async () => {
      const res = await getSummary()
      const d = res.data
      kpiCards.value[0].value = d.total_quantity_wan.toLocaleString()
      kpiCards.value[1].value = d.total_amount_wan.toLocaleString()
      kpiCards.value[2].value = d.quantity_2025_wan.toLocaleString()
      kpiCards.value[3].value = (d.yoy_growth_pct > 0 ? '+' : '') + d.yoy_growth_pct + '%'
    }

    const loadTrend = async () => {
      const res = await getSalesTrend({ year: trendYear.value })
      const months = res.data.map(d => d.month)
      const values = res.data.map(d => d.quantity)
      trendOption.value = {
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: months, axisLabel: { rotate: 45, fontSize: 11 } },
        yAxis: { type: 'value', name: '万支' },
        series: [{ type: 'line', data: values, smooth: true, areaStyle: { opacity: 0.1 }, lineStyle: { color: '#409eff' }, itemStyle: { color: '#409eff' } }],
        grid: { left: 50, right: 20, bottom: 60 },
      }
    }

    const loadProductMix = async () => {
      const res = await getProductMix({})
      pieOption.value = {
        tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
        legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { fontSize: 11 } },
        series: [{
          type: 'pie', radius: ['40%', '70%'],
          data: res.data.map(d => ({ name: d.name, value: d.value })),
          label: { show: false },
        }]
      }
    }

    const loadRegionDist = async () => {
      const res = await getRegionDist({})
      const names = res.data.map(d => d.name)
      const values = res.data.map(d => d.value)
      regionOption.value = {
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: names, axisLabel: { fontSize: 11 } },
        yAxis: { type: 'value', name: '万支' },
        series: [{ type: 'bar', data: values, itemStyle: { color: '#67c23a' } }],
        grid: { left: 50, right: 20, bottom: 40 },
      }
    }

    const loadChannelDist = async () => {
      const res = await getChannelDist({})
      channelOption.value = {
        tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
        legend: { bottom: 10 },
        series: [{
          type: 'pie', radius: '65%',
          data: res.data.map(d => ({ name: d.name, value: d.value })),
          label: { formatter: '{b}\n{d}%' },
        }]
      }
    }

    onMounted(async () => {
      await Promise.all([loadSummary(), loadTrend(), loadProductMix(), loadRegionDist(), loadChannelDist()])
    })

    return { trendYear, kpiCards, trendOption, pieOption, regionOption, channelOption, loadTrend }
  }
}
</script>

<style scoped>
.dashboard { padding: 4px; }
.kpi-row { margin-bottom: 20px; }
.kpi-card { border-radius: 8px; }
.kpi-content { display: flex; align-items: center; gap: 16px; }
.kpi-icon { width: 56px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.kpi-value { font-size: 24px; font-weight: 700; color: #1a1a1a; line-height: 1.2; }
.kpi-label { font-size: 13px; color: #888; margin-top: 4px; }
.chart-row { margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
