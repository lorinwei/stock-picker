import axios from 'axios'
import type { ApiResponse } from '@/types'

// StockMind V2 三省六部 API
const WORKER_URL = 'https://stock-picker-ten.vercel.app';

const api = axios.create({
  baseURL: `${WORKER_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if exists
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response.data as ApiResponse<any>,
  (error) => {
    const message = error.response?.data?.message || error.message || '网络错误'
    console.error('API Error:', message)
    return Promise.reject(error)
  }
)

export default api
