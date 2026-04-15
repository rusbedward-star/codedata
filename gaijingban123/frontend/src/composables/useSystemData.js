import { reactive, toRefs } from 'vue'

import {
  getForecast,
  getImages,
  getInsights,
  getMetrics,
  getModules,
  getOverview,
  getSampleData,
} from '../api'

const state = reactive({
  loading: false,
  loaded: false,
  error: '',
  overview: null,
  metrics: [],
  bestModel: '',
  forecast: [],
  forecastColumns: [],
  images: [],
  modules: {
    frontend_modules: [],
    backend_modules: [],
    optimizations: [],
  },
  sampleData: [],
  sampleColumns: [],
  insights: {
    recommendations: [],
  },
})

async function loadData(force = false) {
  if (state.loaded && !force) {
    return
  }

  state.loading = true
  state.error = ''

  try {
    const [overview, metrics, forecast, images, modules, sampleData, insights] =
      await Promise.all([
        getOverview(),
        getMetrics(),
        getForecast(),
        getImages(),
        getModules(),
        getSampleData(),
        getInsights(),
      ])

    state.overview = overview
    state.metrics = metrics.items ?? []
    state.bestModel = metrics.best_model ?? ''
    state.forecast = forecast.items ?? []
    state.forecastColumns = forecast.columns ?? []
    state.images = images.items ?? []
    state.modules = modules
    state.sampleData = sampleData.items ?? []
    state.sampleColumns = sampleData.columns ?? []
    state.insights = insights
    state.loaded = true
  } catch (error) {
    state.error = error.message || '系统数据加载失败'
  } finally {
    state.loading = false
  }
}

export function useSystemData() {
  return {
    ...toRefs(state),
    loadData,
  }
}
