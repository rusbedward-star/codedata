import request from './request'

export const login = (data) => request.post('/auth/login/', data)
export const refreshToken = (data) => request.post('/auth/refresh/', data)
export const getMe = () => request.get('/auth/me/')
