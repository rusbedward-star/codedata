import request from './request'

export const getSalesTrend = (params) => request.get('/analytics/trend/', { params })
export const getProductMix = (params) => request.get('/analytics/product-mix/', { params })
export const getRegionDist = (params) => request.get('/analytics/region-dist/', { params })
export const getChannelDist = (params) => request.get('/analytics/channel-dist/', { params })
export const getSummary = () => request.get('/analytics/summary/')
