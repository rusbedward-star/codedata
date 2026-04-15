import { afterEach, describe, expect, test, vi } from 'vitest'

import { getAiAnalysis, getModelDetail, getOverview } from '../src/api'

describe('api helpers', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('requests overview data from overview endpoint', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ project_name: 'demo' }),
      }),
    )

    const result = await getOverview()

    expect(fetch).toHaveBeenCalledWith('/api/overview/', {})
    expect(result.project_name).toBe('demo')
  })

  test('encodes model name in detail request', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ model: '随机森林' }),
      }),
    )

    const result = await getModelDetail('随机森林')

    expect(fetch).toHaveBeenCalledWith(
      '/api/model-detail/?model=%E9%9A%8F%E6%9C%BA%E6%A3%AE%E6%9E%97',
      {},
    )
    expect(result.model).toBe('随机森林')
  })

  test('requests spark analysis for the selected model', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ analysis: '趋势整体平稳' }),
      }),
    )

    const result = await getAiAnalysis('随机森林')

    expect(fetch).toHaveBeenCalledWith('/api/ai-analysis/?model=%E9%9A%8F%E6%9C%BA%E6%A3%AE%E6%9E%97', {})
    expect(result.analysis).toBe('趋势整体平稳')
  })
})
