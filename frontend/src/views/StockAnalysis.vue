<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { NSpace, NSelect, NInput, NButton, NSpin } from 'naive-ui'
import KLineChart from '@components/KLineChart.vue'
import TechIndicators from '@components/TechIndicators.vue'
import SignalBadge from '@components/SignalBadge.vue'
import { useStockStore } from '@stores/stock'
import type { IndicatorType } from '@/types'

const route = useRoute()
const stockStore = useStockStore()

const stockCode = ref(route.params.code as string || '600519')
const periodOptions = [
  { label: '日K', value: 'daily' },
  { label: '周K', value: 'weekly' },
  { label: '月K', value: 'monthly' },
  { label: '60分钟', value: '60min' },
  { label: '30分钟', value: '30min' },
]
const selectedPeriod = ref('daily')

const stockInfo = computed(() => stockStore.currentStock)
const klineData = computed(() => stockStore.klineData)
const signals = computed(() => stockStore.signals)
const loading = computed(() => stockStore.loading)
const selectedIndicators = computed(() => stockStore.selectedIndicators)

async function loadData() {
  await stockStore.fetchStockInfo(stockCode.value)
  await stockStore.fetchKLineData(stockCode.value, selectedPeriod.value)
  await stockStore.fetchSignals(stockCode.value)
}

function handleIndicatorChange(indicators: IndicatorType[]) {
  stockStore.selectedIndicators.splice(0, stockStore.selectedIndicators.length, ...indicators)
}

function handleSearch() {
  if (stockCode.value.length >= 6) {
    loadData()
  }
}

onMounted(() => {
  loadData()
})

watch(selectedPeriod, () => {
  loadData()
})
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold">K线分析</h2>
      <NSpace align="center">
        <NInput
          v-model:value="stockCode"
          placeholder="股票代码"
          style="width: 120px"
          @keyup.enter="handleSearch"
        />
        <NSelect
          v-model:value="selectedPeriod"
          :options="periodOptions"
          style="width: 100px"
        />
        <NButton type="primary" @click="handleSearch">查询</NButton>
      </NSpace>
    </div>

    <!-- Stock Info -->
    <div v-if="stockInfo" class="card-base flex items-center justify-between">
      <div>
        <span class="text-2xl font-bold mr-4">{{ stockInfo.name }}</span>
        <span class="text-dark-muted">{{ stockInfo.code }}</span>
      </div>
      <div class="text-right">
        <span class="text-3xl font-bold">¥{{ stockInfo.price }}</span>
        <span
          class="ml-2 text-lg"
          :class="stockInfo.change >= 0 ? 'text-accent-green' : 'text-accent-red'"
        >
          {{ stockInfo.change >= 0 ? '+' : '' }}{{ stockInfo.change }} ({{ stockInfo.changePercent.toFixed(2) }}%)
        </span>
      </div>
    </div>

    <!-- Indicators Panel -->
    <TechIndicators
      :selected="selectedIndicators"
      @change="handleIndicatorChange"
    />

    <!-- K-Line Chart -->
    <NSpin :show="loading">
      <KLineChart
        :data="klineData"
        :indicators="selectedIndicators"
        :signals="signals"
        class="h-[500px]"
      />
    </NSpin>

    <!-- Trade Signals -->
    <div v-if="signals.length > 0" class="card-base">
      <h3 class="text-lg font-semibold mb-4">买卖信号</h3>
      <div class="space-y-2">
        <div
          v-for="(signal, idx) in signals"
          :key="idx"
          class="flex items-center justify-between py-2 border-b border-dark-border last:border-0"
        >
          <div class="flex items-center gap-3">
            <SignalBadge :type="signal.type" />
            <span class="text-dark-muted">{{ signal.date }}</span>
            <span>{{ signal.reason }}</span>
          </div>
          <div class="text-right">
            <span class="font-medium">¥{{ signal.price }}</span>
            <span class="ml-4 text-sm text-dark-muted">强度 {{ signal.strength }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
