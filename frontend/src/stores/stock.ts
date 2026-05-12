import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useStockStore = defineStore('stock', () => {
  const currentStock = ref<any>(null)
  const marketOverview = ref<any>(null)
  const todaySignals = ref<any>(null)
  const stockPool = ref<any>({ items: [], total: 0 })
  const klineData = ref<any[]>([])
  const indicators = ref<any>(null)
  const loading = ref(false)

  const hasSignals = computed(() => todaySignals.value?.mainPick != null)

  // 太子院：获取大盘数据
  async function fetchMarketOverview() {
    loading.value = true
    try {
      const res = await api.get('/market/overview')
      marketOverview.value = res.data
    } finally {
      loading.value = false
    }
  }

  // 中书省：获取今日AI信号
  async function fetchTodaySignals() {
    loading.value = true
    try {
      const res = await api.get('/signals/today')
      todaySignals.value = res.data
    } finally {
      loading.value = false
    }
  }

  // 中书省：获取选股池
  async function fetchStockPool(category = 'all', page = 1, pageSize = 20) {
    loading.value = true
    try {
      const res = await api.get('/stockpool', { params: { category, page, pageSize } })
      stockPool.value = res.data
    } finally {
      loading.value = false
    }
  }

  // 太子院：获取K线+指标
  async function fetchKLine(code: string, ktype = 'D', start?: string, end?: string) {
    loading.value = true
    try {
      const res = await api.get('/kline', { params: { code, ktype, start, end } })
      klineData.value = res.data.klines || []
      indicators.value = res.data.indicators || null
    } finally {
      loading.value = false
    }
  }

  // 股票列表
  async function fetchStockList() {
    const res = await api.get('/stock/list')
    return res.data
  }

  return {
    currentStock, marketOverview, todaySignals, stockPool, klineData, indicators, loading, hasSignals,
    fetchMarketOverview, fetchTodaySignals, fetchStockPool, fetchKLine, fetchStockList
  }
})
