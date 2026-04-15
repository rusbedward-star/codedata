<script setup>
import { computed, onMounted } from 'vue'

import { useSystemData } from '../composables/useSystemData'

const { loading, error, modules, loadData } = useSystemData()

const frontendCards = computed(() => modules.value.frontend_modules || [])
const backendCards = computed(() => modules.value.backend_modules || [])
const optimizeCards = computed(() => modules.value.optimizations || [])

const apiRows = [
  { path: '/api/overview/', method: 'GET', target: '系统首页' },
  { path: '/api/sample-data/', method: 'GET', target: '数据中心' },
  { path: '/api/metrics/', method: 'GET', target: '模型评估' },
  { path: '/api/forecast/', method: 'GET', target: '预测结果' },
  { path: '/api/model-detail/', method: 'GET', target: '详情联动' },
  { path: '/api/charts/model-forecast/', method: 'GET', target: '图表中心' },
]

onMounted(() => loadData())
</script>

<template>
  <section class="page-stack">
    <div v-if="loading" class="plain-panel status-panel">系统数据加载中...</div>
    <div v-else-if="error" class="plain-panel status-panel error-panel">{{ error }}</div>

    <template v-else>
      <section class="two-column">
        <article class="plain-panel">
          <h3>前端模块</h3>
          <div class="module-grid">
            <div v-for="item in frontendCards" :key="item.name" class="module-card">
              <strong>{{ item.name }}</strong>
            </div>
          </div>
        </article>

        <article class="plain-panel">
          <h3>后端模块</h3>
          <div class="module-grid">
            <div v-for="item in backendCards" :key="item.name" class="module-card">
              <strong>{{ item.name }}</strong>
            </div>
          </div>
        </article>
      </section>

      <section class="two-column">
        <article class="plain-panel">
          <h3>接口总览</h3>
          <div class="table-box compact-table">
            <table>
              <thead>
                <tr>
                  <th>路径</th>
                  <th>方法</th>
                  <th>页面</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in apiRows" :key="row.path">
                  <td>{{ row.path }}</td>
                  <td>{{ row.method }}</td>
                  <td>{{ row.target }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="plain-panel">
          <h3>优化项</h3>
          <div class="module-grid">
            <div v-for="item in optimizeCards" :key="item" class="module-card module-card-wide">
              <span>{{ item }}</span>
            </div>
          </div>
        </article>
      </section>
    </template>
  </section>
</template>
