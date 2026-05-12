<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NGrid, NGi, NChart } from 'naive-ui'
import type { StrategyMetrics, SectorData } from '@/types'

const metrics = ref<StrategyMetrics>({
  momentum: 72,
  volatility: 45,
  liquidity: 88,
  valuation: 65,
  growth: 78,
  stability: 82
})

const sectors = ref<SectorData[]>([
  { name: '白酒', strength: 85, change: 2.3, stocks: [] },
  { name: '新能源车', strength: 78, change: 1.5, stocks: [] },
  { name: '银行', strength: 65, change: 0.8, stocks: [] },
  { name: '医药', strength: 58, change: -0.5, stocks: [] },
  { name: '半导体', strength: 72, change: 1.2, stocks: [] },
  { name: '消费电子', strength: 55, change: -1.2, stocks: [] },
])

const radarOptions = {
  title: { text: '策略雷达', textStyle: { color: '#c9d1d9' } },
  legend: { textStyle: { color: '#8b949e' } },
  radar: {
    indicator: [
      { name: '动量', max: 100 },
      { name: '波动', max: 100 },
      { name: '流动性', max: 100 },
      { name: '估值', max: 100 },
      { name: '成长', max: 100 },
      { name: '稳定性', max: 100 },
    ],
    axisLine: { lineStyle: { color: '#30363d' } },
    splitLine: { lineStyle: { color: '#30363d' } },
    splitArea: { areaStyle: { color: ['#161b22', '#1a1f26'] } },
  },
  series: [{
    type: 'radar',
    data: [{
      value: [metrics.value.momentum, metrics.value.volatility, metrics.value.liquidity, 
              metrics.value.valuation, metrics.value.growth, metrics.value.stability],
      name: '当前策略',
      lineStyle: { color: '#00d4ff' },
      areaStyle: { color: 'rgba(0, 212, 255, 0.3)' },
      itemStyle: { color: '#00d4ff' }
    }]
  }]
}

const barOptions = {
  title: { text: '板块强弱', textStyle: { color: '#c9d1d9' } },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: sectors.value.map(s => s.name), axisLine: { lineStyle: { color: '#30363d' } }, axisLabel: { color: '#8b949e' } },
  yAxis: { type: 'value', axisLine: { lineStyle: { color: '#30363d' } }, axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#30363d' } } },
  series: [{
    type: 'bar',
    data: sectors.value.map(s => ({
      value: s.strength,
      itemStyle: { color: s.change >= 0 ? '#00ff88' : '#ff4757' }
    })),
    barWidth: '50%',
  }]
}
</script>

<template>
  <div class="space-y-4">
    <h2 class="text-2xl font-bold">策略雷达</h2>

    <NGrid :cols="2" :x-gap="16">
      <!-- Radar Chart -->
      <NGi>
        <NCard title="策略评分" class="card-base">
          <div id="radar-chart" class="h-[400px]" />
        </NCard>
      </NGi>

      <!-- Sector Strength -->
      <NGi>
        <NCard title="板块强弱" class="card-base">
          <div id="bar-chart" class="h-[400px]" />
        </NCard>
      </NGi>
    </NGrid>

    <!-- Sector List -->
    <NCard title="板块详情" class="card-base">
      <div class="space-y-3">
        <div
          v-for="sector in sectors"
          :key="sector.name"
          class="flex items-center justify-between p-3 bg-dark-bg rounded-lg border border-dark-border"
        >
          <div class="flex items-center gap-4">
            <span class="font-medium w-20">{{ sector.name }}</span>
            <div class="flex items-center gap-2">
              <div class="w-24 h-2 bg-dark-border rounded-full overflow-hidden">
                <div
                  class="h-full bg-accent-cyan rounded-full"
                  :style="{ width: sector.strength + '%' }"
                />
              </div>
              <span class="text-sm text-dark-muted">{{ sector.strength }}</span>
            </div>
          </div>
          <span
            class="text-lg font-bold"
            :class="sector.change >= 0 ? 'text-accent-green' : 'text-accent-red'"
          >
            {{ sector.change >= 0 ? '+' : '' }}{{ sector.change.toFixed(2) }}%
          </span>
        </div>
      </div>
    </NCard>
  </div>
</template>
