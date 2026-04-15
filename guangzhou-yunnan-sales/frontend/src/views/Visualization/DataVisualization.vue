<template>
  <div class="viz-page">
    <div class="viz-header">
      <span>数据可视化分析</span>
      <el-select v-model="selectedYear" size="small" style="width:110px;margin-left:16px" @change="loadAll">
        <el-option label="2024年" value="2024" />
        <el-option label="2025年" value="2025" />
        <el-option label="全部" value="" />
      </el-select>
    </div>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover" class="chart-card">
          <template #header><span>月度销售趋势（万支）</span></template>
          <v-chart :option="trendOption" style="height:320px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="10">
        <el-card shadow="hover" class="chart-card">
          <template #header><span>产品销售结构占比</span></template>
          <v-chart :option="pieOption" style="height:320px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card shadow="hover" class="chart-card">
          <template #header><span>区域销售分布（万支）</span></template>
          <v-chart :option="regionOption" style="height:320px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <template #header><span>渠道销售占比</span></template>
          <v-chart :option="channelOption" style="height:280px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <template #header><span>月度销量热力图（支）</span></template>
          <v-chart :option="barCompareOption" style="height:280px" autoresize />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { getSalesTrend, getProductMix, getRegionDist, getChannelDist } from '@/api/analytics'

export default {
  name: 'DataVisualization',
  setup() {
    const selectedYear = ref('')
    const trendOption = ref({})
    const pieOption = ref({})
    const regionOption = ref({})
    const channelOption = ref({})
    const barCompareOption = ref({})

    const loadAll = async () => {
      const year = selectedYear.value
      const [trendRes, pieRes, regionRes, channelRes, trend24, trend25] = await Promise.all([
        getSalesTrend({ year }),
        getProductMix({ year }),
        getRegionDist({ year }),
        getChannelDist({ year }),
        getSalesTrend({ year: '2024' }),
        getSalesTrend({ year: '2025' }),
      ])

      // 趋势图
      trendOption.value = {
        tooltip: { trigger: 'axis' },
        legend: { data: ['销量(万支)'] },
        xAxis: { type: 'category', data: trendRes.data.map(d => d.month), axisLabel: { rotate: 45, fontSize: 10 } },
        yAxis: { type: 'value', name: '万支' },
        series: [{
          name: '销量(万支)', type: 'line', data: trendRes.data.map(d => d.quantity),
          smooth: true, areaStyle: { opacity: 0.15 }, lineStyle: { color: '#409eff', width: 2 },
          markPoint: { data: [{ type: 'max', name: '最大值' }, { type: 'min', name: '最小值' }] }
        }],
        grid: { left: 60, right: 30, bottom: 70 },
      }

      // 产品饼图
      const COLORS = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
      pieOption.value = {
        tooltip: { trigger: 'item', formatter: '{b}: {c}支 ({d}%)' },
        legend: { orient: 'vertical', right: 20, top: 'middle', textStyle: { fontSize: 12 } },
        series: [{
          type: 'pie', radius: ['45%', '72%'], center: ['40%', '50%'],
          data: pieRes.data.map((d, i) => ({ name: d.name, value: d.value, itemStyle: { color: COLORS[i % COLORS.length] } })),
          label: { show: true, formatter: '{d}%', fontSize: 12 },
          labelLine: { show: true },
        }]
      }

      // 区域柱状图
      regionOption.value = {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        xAxis: { type: 'category', data: regionRes.data.map(d => d.name), axisLabel: { rotate: 30, fontSize: 11 } },
        yAxis: { type: 'value', name: '万支' },
        series: [{ type: 'bar', data: regionRes.data.map(d => d.value), itemStyle: { color: '#67c23a', borderRadius: [4, 4, 0, 0] } }],
        grid: { left: 55, right: 20, bottom: 65 },
      }

      // 渠道饼图
      channelOption.value = {
        tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
        legend: { bottom: 8 },
        series: [{
          type: 'pie', radius: '62%', center: ['50%', '44%'],
          data: channelRes.data.map(d => ({ name: d.name, value: d.value })),
          label: { formatter: '{b}\n{d}%' },
        }]
      }

      // 2024 vs 2025 对比柱状图
      const months24 = trend24.data.map(d => d.month.slice(5))
      const vals24 = trend24.data.map(d => d.quantity)
      const vals25 = trend25.data.map(d => d.quantity)
      barCompareOption.value = {
        tooltip: { trigger: 'axis' },
        legend: { data: ['2024年', '2025年'] },
        xAxis: { type: 'category', data: months24, axisLabel: { fontSize: 11 } },
        yAxis: { type: 'value', name: '万支' },
        series: [
          { name: '2024年', type: 'bar', data: vals24, itemStyle: { color: '#b0c4de', borderRadius: [3, 3, 0, 0] } },
          { name: '2025年', type: 'bar', data: vals25, itemStyle: { color: '#409eff', borderRadius: [3, 3, 0, 0] } },
        ],
        grid: { left: 50, right: 20, bottom: 40 },
      }
    }

    onMounted(loadAll)

    return { selectedYear, trendOption, pieOption, regionOption, channelOption, barCompareOption, loadAll }
  }
}
</script>

<style scoped>
.viz-page { padding: 4px; }
.viz-header { font-size: 16px; font-weight: 600; margin-bottom: 20px; display: flex; align-items: center; }
.chart-card { border-radius: 8px; }
</style>
