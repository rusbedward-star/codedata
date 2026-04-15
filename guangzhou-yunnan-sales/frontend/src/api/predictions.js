import request from './request'

export const getPredictions = (params) => request.get('/predictions/', { params })
export const runPrediction = (data) => request.post('/predictions/run/', data)
export const analyzeWithAI = (predictions) => request.post('/predictions/analyze/', { predictions })

export const exportPredictions = (params) => {
  return request.get('/predictions/export/', {
    params,
    responseType: 'blob'
  })
}
