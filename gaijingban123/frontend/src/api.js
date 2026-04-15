const API_BASE = '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  if (!response.ok) {
    let errorMessage = `接口请求失败: ${path}`
    try {
      const payload = await response.json()
      errorMessage = payload.error || payload.detail || errorMessage
    } catch {
      // ignore non-json error payloads
    }
    throw new Error(errorMessage)
  }
  return response.json()
}

export function getOverview() {
  return request('/overview/')
}

export function getMetrics() {
  return request('/metrics/')
}

export function getForecast() {
  return request('/forecast/')
}

export function getImages() {
  return request('/images/')
}

export function getModules() {
  return request('/modules/')
}

export function getSampleData() {
  return request('/sample-data/')
}

export function createSampleData(payload) {
  return request('/sample-data/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export function updateSampleData(date, payload) {
  return request(`/sample-data/${encodeURIComponent(date)}/`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export function deleteSampleData(date) {
  return request(`/sample-data/${encodeURIComponent(date)}/`, {
    method: 'DELETE',
  })
}

export async function importSampleData(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE}/sample-data/import/`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    let errorMessage = 'Excel 导入失败'
    try {
      const payload = await response.json()
      errorMessage = payload.error || payload.detail || errorMessage
    } catch {
      // ignore non-json error payloads
    }
    throw new Error(errorMessage)
  }

  return response.json()
}

export function getInsights() {
  return request('/insights/')
}

export function getModelDetail(model) {
  const params = new URLSearchParams({ model })
  return request(`/model-detail/?${params.toString()}`)
}

export function getAiAnalysis(model, months = []) {
  const params = new URLSearchParams({ model })
  months.forEach((month) => params.append('months', month))
  return request(`/ai-analysis/?${params.toString()}`)
}

export function startForecastJob() {
  return request('/forecast-jobs/', {
    method: 'POST',
  })
}

export function getForecastJob(jobId) {
  return request(`/forecast-jobs/${jobId}/`)
}
