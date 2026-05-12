<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NGrid, NGi, NStatistic, NButton, NSpace } from 'naive-ui'
import SignalBadge from '@components/SignalBadge.vue'
import StockCard from '@components/StockCard.vue'
import type { Stock, TradeSignal } from '@/types'

const todaySignals = ref<TradeSignal[]>([])
const hotStocks = ref<Stock[]>([])
const aiReviewReady = ref(false)

onMounted(() => {
  // Mock data
  todaySignals.value = [
    { date: '2024-01-15', type: 'BUY', price: 185.50, reason: 'MACD金叉', strength: 85 },
    { date: '2024-01-15', type: 'BUY', price: 42.30, reason: 'KDJ超卖', strength: 78 },
    { date: '2024-01-15', type: 'SELL', price: 128.80, reason: '九转序列高9', strength: 72 },
  ]
  hotStocks.value = [
    { code: '600519', name: '贵州茅台', price: 1850, change: 25.5, changePercent: 1.4, volume: 2345678, amount: 4321000000, amplitude: 3.2, turnover: 0.85, pe: 45.6, marketCap: 2324000000000 },
    { code: '000858', name: '五粮液', price: 168.5, change: -2.3, changePercent: -1.35, volume: 1234567, amount: 207890000, amplitude: 2.8, turnover: 1.2, pe: 32.1, marketCap: 654300000000 },
    { code: '600036', name: '招商银行', price: 35.8, change: 0.45, changePercent: 1.27, volume: 3456789, amount: 123456000, amplitude: 1.9, turnover: 0.45, pe: 8.5, marketCap: 890000000000 },
  ]
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold">仪表盘</h2>
      <NSpace>
        <NButton size="small" @click="aiReviewReady = true">
          <template #icon><span class="i-carbon-refresh" /></template>
          刷新数据
        </NButton>
      </NSpace>
    </div>

    <!-- Stats Cards -->
    <NGrid :cols="4" :x-gap="16" :y-gap="16">
      <NGi>
        <NCard class="card-base">
          <NStatistic label="总资产">
            <template #default>
              <span class="text-xl font-bold">¥ 1,000,000</span>
            </template>
          </NStatistic>
        </NCard>
      </NGi>
      <NGi>
        <NCard class="card-base">
          <NStatistic label="今日收益">
            <template #default>
              <span class="text-xl font-bold text-accent-green">+¥ 5,280</span>
            </template>
          </NStatistic>
        </NCard>
      </NGi>
      <NGi>
        <NCard class="card-base">
          <NStatistic label="持仓数量">
            <template #default>
              <span class="text-xl font-bold">8</span>
            </template>
          </NStatistic>
        </NCard>
      </NGi>
      <NGi>
        <NCard class="card-base">
          <NStatistic label="今日信号">
            <template #default>
              <span class="text-xl font-bold text-accent-cyan">{{ todaySignals.length }}</span>
            </template>
          </NStatistic>
        </NCard>
      </NGi>
    </NGrid>

    <!-- Today's Signals -->
    <NCard title="今日交易信号" class="card-base">
      <div v-if="todaySignals.length === 0" class="text-center py-8 text-dark-muted">
        暂无信号
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="(signal, idx) in todaySignals"
          :key="idx"
          class="flex items-center justify-between p-3 bg-dark-bg rounded-lg border border-dark-border"
        >
          <div class="flex items-center gap-4">
            <SignalBadge :type="signal.type" />
            <div>
              <div class="font-medium">{{ signal.reason }}</div>
              <div class="text-sm text-dark-muted">价格: ¥{{ signal.price }}</div>
            </div>
          </div>
          <div class="text-right">
            <div class="text-sm text-dark-muted">{{ signal.date }}</div>
            <div class="text-sm" :class="signal.type === 'BUY' ? 'text-accent-green' : 'text-accent-red'">
              强度 {{ signal.strength }}%
            </div>
          </div>
        </div>
      </div>
    </NCard>

    <!-- AI Review Entry -->
    <NCard title="AI智能复盘" class="card-base">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-dark-muted">基于最新市场数据，AI将为您分析当前持仓状况并给出优化建议</p>
        </div>
        <NButton type="primary" @click="$router.push('/ai')">
          <template #icon><span class="i-carbon-bot" /></template>
          开始AI复盘
        </NButton>
      </div>
    </NCard>

    <!-- Hot Stocks -->
    <NCard title="热门股票" class="card-base">
      <div class="grid grid-cols-3 gap-4">
        <StockCard v-for="stock in hotStocks" :key="stock.code" :stock="stock" />
      </div>
    </NCard>
  </div>
</template>
