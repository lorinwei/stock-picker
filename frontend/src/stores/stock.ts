import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useStockStore = defineStore('stock', () => {
  const marketOverview = ref<any>(null)
  const todaySignals = ref<any>(null)
  const stockPool = ref<any>({ items: [], total: 0 })
  const klineData = ref<any[]>([])
  const indicators = ref<any>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const hasSignals = computed(() => {
    const s = todaySignals.value
    return s?.mainPick != null || (s?.signals?.length ?? 0) > 0
  })

  async function fetchMarketOverview() {
    loading.value = true
    try {
      const res: any = await api.get('/market/overview')
      marketOverview.value = res.data
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchTodaySignals() {
    loading.value = true
    try {
      const res: any = await api.get('/signals/today')
      todaySignals.value = res.data
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchStockPool(category = 'all', page = 1, pageSize = 20) {
    loading.value = true
    try {
      const res: any = await api.get('/stockpool', { params: { category, page, pageSize } })
      stockPool.value = res.data || { items: [], total: 0 }
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchKLine(code: string, ktype = 'D', start?: string, end?: string) {
    loading.value = true
    try {
      const res: any = await api.get('/kline', { params: { code, ktype, start, end } })
      klineData.value = res.data.klines || []
      indicators.value = res.data.indicators || null
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchStockList() {
    const res: any = await api.get('/stock/list')
    return res.data || []
  }

  return {
    marketOverview, todaySignals, stockPool, klineData, indicators,
    loading, error, hasSignals,
    fetchMarketOverview, fetchTodaySignals, fetchStockPool, fetchKLine, fetchStockList
  }
})
