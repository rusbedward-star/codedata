import { describe, expect, test, vi } from 'vitest'

vi.mock('../src/api', () => ({
  getOverview: vi.fn(async () => ({
    project_name: '冰柠销量分析与预测系统',
    dataset_rows: 26,
  })),
  getMetrics: vi.fn(async () => ({
    best_model: '随机森林',
    items: [{ 模型: '随机森林', RMSE: 8.4209 }],
  })),
  getForecast: vi.fn(async () => ({
    columns: ['月份', '随机森林'],
    items: [{ 月份: '2026-03', 随机森林: 63.85 }],
  })),
  getImages: vi.fn(async () => ({
    items: [{ title: 'MAE 指标图', url: '/api/media/results/MAE指标对比图.png/' }],
  })),
  getModules: vi.fn(async () => ({
    frontend_modules: [{ name: '系统总览模块' }],
    backend_modules: [{ name: '结果聚合服务' }],
    optimizations: ['采用前后端分离架构'],
  })),
  getSampleData: vi.fn(async () => ({
    columns: ['date', 'sales'],
    items: [{ date: '2024-01', sales: 85.67 }],
  })),
  getInsights: vi.fn(async () => ({
    recommendations: ['优先采用随机森林作为默认展示模型'],
  })),
}))

import { useSystemData } from '../src/composables/useSystemData'

describe('useSystemData', () => {
  test('loads and exposes shared system state', async () => {
    const store = useSystemData()

    await store.loadData(true)

    expect(store.loading.value).toBe(false)
    expect(store.error.value).toBe('')
    expect(store.overview.value.project_name).toBe('冰柠销量分析与预测系统')
    expect(store.bestModel.value).toBe('随机森林')
    expect(store.forecastColumns.value).toEqual(['月份', '随机森林'])
    expect(store.sampleColumns.value).toEqual(['date', 'sales'])
    expect(store.modules.value.frontend_modules).toHaveLength(1)
    expect(store.insights.value.recommendations).toHaveLength(1)
  })
})
