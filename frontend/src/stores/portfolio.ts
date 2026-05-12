import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const usePortfolioStore = defineStore('portfolio', () => {
  const portfolio = ref<any>({
    totalValue: 0, totalCost: 0, totalProfit: 0, profitPercent: 0,
    positions: [], cash: 0, availableCash: 0, maxPositions: 5
  })
  const loading = ref(false)

  const totalValue = computed(() => portfolio.value.totalValue)
  const totalProfit = computed(() => portfolio.value.totalProfit)
  const positions = computed(() => portfolio.value.positions || [])

  // 尚书省：获取持仓
  async function fetchPortfolio() {
    loading.value = true
    try {
      const res = await api.get('/portfolio')
      portfolio.value = res.data
    } finally {
      loading.value = false
    }
  }

  // 尚书省：添加持仓
  async function addPosition(code: string, name: string, shares: number, buyPrice: number) {
    const res = await api.post('/portfolio', { code, name, shares, buyPrice })
    await fetchPortfolio()
    return res.data
  }

  // 尚书省：卖出
  async function sellPosition(id: string, sellPrice: number) {
    const res = await api.post(`/portfolio/${id}/sell`, { sellPrice })
    await fetchPortfolio()
    return res.data
  }

  // 门下省：风控检查
  async function checkRisk(params: { action: string; code: string; price: number; quantity: number; portfolioValue: number }) {
    const res = await api.post('/risk/check', params)
    return res.data
  }

  return {
    portfolio, loading, totalValue, totalProfit, positions,
    fetchPortfolio, addPosition, sellPosition, checkRisk
  }
})
