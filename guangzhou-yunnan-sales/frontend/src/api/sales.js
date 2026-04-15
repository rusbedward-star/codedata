import request from './request'

export const getProducts = () => request.get('/products/')
export const getRegions = () => request.get('/regions/')

export const getSales = (params) => request.get('/sales/', { params })
export const createSale = (data) => request.post('/sales/', data)
export const updateSale = (id, data) => request.patch(`/sales/${id}/`, data)
export const deleteSale = (id) => request.delete(`/sales/${id}/`)

export const exportSales = (params) => {
  return request.get('/sales/export/', {
    params,
    responseType: 'blob'
  })
}
