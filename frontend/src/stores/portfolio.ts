import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const usePortfolioStore = defineStore('portfolio', () => {
  const portfolio = ref<any>({
    totalValue: 0, totalCost: 0, totalProfit: 0, profitPercent: 0,
    positions: [], cash: 0, availableCash: 0, maxPositions: 5
  })
  const loading = ref(false)

  const totalValue = computed(() => portfolio.value.totalValue || 0)
  const totalProfit = computed(() => portfolio.value.totalProfit || 0)
  const positions = computed(() => portfolio.value.positions || [])

  async function fetchPortfolio() {
    loading.value = true
    try {
      const res: any = await api.get('/portfolio')
      portfolio.value = (res as any).data || portfolio.value
    } catch { /* ignore */ }
    finally { loading.value = false }
  }

  async function addPosition(code: string, name: string, shares: number, buyPrice: number) {
    const res: any = await api.post('/portfolio', { code, name, quantity: shares, buy_price: buyPrice, buy_date: new Date().toISOString().split('T')[0] })
    await fetchPortfolio()
    return res.data
  }

  async function sellPosition(id: string, sellPrice: number) {
    const res: any = await api.post(`/portfolio/${id}/sell`, { sell_price: sellPrice, reason: 'manual' })
    await fetchPortfolio()
    return res.data
  }

  async function checkRisk(params: any) {
    const res: any = await api.post('/risk/check', params || {})
    return res.data
  }

  return {
    portfolio, loading, totalValue, totalProfit, positions,
    fetchPortfolio, addPosition, sellPosition, checkRisk
  }
})
