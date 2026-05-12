<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { NCard, NButton, NSpace, NStatistic, NAlert, NProgress } from 'naive-ui'
import PortfolioTable from '@components/PortfolioTable.vue'
import { usePortfolioStore } from '@stores/portfolio'
import type { Position, RiskStatus } from '@/types'

const portfolioStore = usePortfolioStore()
const positions = computed(() => portfolioStore.positions)
const riskStatus = computed(() => portfolioStore.riskStatus)
const portfolio = computed(() => portfolioStore.portfolio)

const riskColors = {
  safe: 'success',
  warning: 'warning',
  danger: 'error'
} as const

const riskLabels = {
  safe: '风控正常',
  warning: '注意风险',
  danger: '风险警告'
} as const
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold">持仓管理</h2>
      <NSpace>
        <NButton type="primary">
          <template #icon><span class="i-carbon-add" /></template>
          添加持仓
        </NButton>
        <NButton>
          <template #icon><span class="i-carbon-sync" /></template>
          同步数据
        </NButton>
      </NSpace>
    </div>

    <!-- Summary Stats -->
    <div class="grid grid-cols-4 gap-4">
      <NCard class="card-base">
        <NStatistic label="总资产">
          <template #default>
            <span class="text-xl font-bold">¥ {{ portfolio.totalValue.toLocaleString() }}</span>
          </template>
        </NStatistic>
      </NCard>
      <NCard class="card-base">
        <NStatistic label="持仓市值">
          <template #default>
            <span class="text-xl font-bold">¥ {{ (portfolio.totalValue - portfolio.cash).toLocaleString() }}</span>
          </template>
        </NStatistic>
      </NCard>
      <NCard class="card-base">
        <NStatistic label="总收益">
          <template #default>
            <span
              class="text-xl font-bold"
              :class="portfolio.totalProfit >= 0 ? 'text-accent-green' : 'text-accent-red'"
            >
              {{ portfolio.totalProfit >= 0 ? '+' : '' }}¥ {{ portfolio.totalProfit.toLocaleString() }}
            </span>
          </template>
        </NStatistic>
      </NCard>
      <NCard class="card-base">
        <NStatistic label="收益率">
          <template #default>
            <span
              class="text-xl font-bold"
              :class="portfolio.profitPercent >= 0 ? 'text-accent-green' : 'text-accent-red'"
            >
              {{ portfolio.profitPercent >= 0 ? '+' : '' }}{{ portfolio.profitPercent.toFixed(2) }}%
            </span>
          </template>
        </NStatistic>
      </NCard>
    </div>

    <!-- Risk Status -->
    <NCard class="card-base">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <NAlert
            :type="riskColors[riskStatus.warningLevel]"
            :title="riskLabels[riskStatus.warningLevel]"
          >
            <template #icon>
              <span class="i-carbon-warning" />
            </template>
          </NAlert>
          <div class="grid grid-cols-4 gap-8 text-sm">
            <div>
              <div class="text-dark-muted">最大回撤</div>
              <div class="font-medium">-{{ riskStatus.maxDrawdown.toFixed(1) }}%</div>
            </div>
            <div>
              <div class="text-dark-muted">夏普比率</div>
              <div class="font-medium">{{ riskStatus.sharpeRatio.toFixed(2) }}</div>
            </div>
            <div>
              <div class="text-dark-muted">波动率</div>
              <div class="font-medium">{{ riskStatus.volatility.toFixed(1) }}%</div>
            </div>
            <div>
              <div class="text-dark-muted">VaR (95%)</div>
              <div class="font-medium">{{ riskStatus.var.toFixed(1) }}%</div>
            </div>
          </div>
        </div>
        <div class="text-right text-sm text-dark-muted">
          <div>持仓限制: {{ riskStatus.positionLimit }}%</div>
          <div>个股限制: {{ riskStatus.singleStockLimit }}%</div>
        </div>
      </div>
    </NCard>

    <!-- Position Limits Progress -->
    <div class="grid grid-cols-2 gap-4">
      <NCard class="card-base">
        <div class="mb-2 text-sm text-dark-muted">总持仓占比</div>
        <NProgress
          type="line"
          :percentage="Math.round((1 - portfolio.cash / portfolio.totalValue) * 100)"
          :color="riskStatus.positionLimit > 70 ? '#ffd93d' : '#00ff88'"
          rail-color="#30363d"
        />
      </NCard>
      <NCard class="card-base">
        <div class="mb-2 text-sm text-dark-muted">可用资金</div>
        <NProgress
          type="line"
          :percentage="Math.round(portfolio.availableCash / portfolio.totalValue * 100)"
          :color="'#00d4ff'"
          rail-color="#30363d"
        />
      </NCard>
    </div>

    <!-- Positions Table -->
    <PortfolioTable :positions="positions" />
  </div>
</template>
