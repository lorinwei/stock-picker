import axios from 'axios'
import type { ApiResponse } from '@/types'

// 后端地址 — 开发时通过 Vite 代理走 /api
// 生产环境改为部署地址
const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

// 响应拦截器：直接返回 data
api.interceptors.response.use(
  (res) => res.data as any,
  (err) => {
    const msg = err.response?.data?.message || err.message || '网络错误'
    console.error('API Error:', msg)
    return Promise.reject(new Error(msg))
  }
)

export default api
