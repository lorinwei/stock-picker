<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { NCard, NForm, NFormItem, NInput, NInputNumber, NSelect, NButton, NSpin, NEmpty, NTag, NProgress } from 'naive-ui'
import Plotly from 'plotly.js-dist'
import api from '@/api'

// ---- 配置 ----
const config = ref({
  stockCode: '600519',
  mkt: '1',
  startDate: '2024-01-01',
  endDate: '2025-12-31',
  initialCapital: 100000,
  strategyType: 'momentum'
})

const strategyOptions = ref<{ label: string; value: string }[]>([])
const stockOptions = [
  { label: '贵州茅台 600519', value: '600519' },
  { label: '宁德时代 300750', value: '300750' },
  { label: '招商银行 600036', value: '600036' },
  { label: '比亚迪 002594', value: '002594' },
  { label: '五粮液 000858', value: '000858' },
  { label: '中国平安 601318', value: '601318' },
  { label: '恒瑞医药 600276', value: '600276' },
]

// ---- 结果 ----
const result = ref<any>(null)
const running = ref(false)
const errorMsg = ref('')
const chartRef = ref<HTMLDivElement>()

// ---- 策略列表 ----
async function loadStrategies() {
  try {
    const res = await api.get('/backtest/strategies')
    strategyOptions.value = res.data.map((s: any) => ({ label: s.label, value: s.name }))
  } catch {
    strategyOptions.value = [
      { label: '动量策略（均线多头）', value: 'momentum' },
      { label: '均值回归策略', value: 'mean_reversion' },
      { label: '突破策略', value: 'breakout' },
      { label: 'RSI策略', value: 'rsi' },
    ]
  }
}

// ---- 跑回测 ----
async function runBacktest() {
  running.value = true
  errorMsg.value = ''
  result.value = null
  try {
    const res = await api.get('/backtest', {
      params: {
        code: config.value.stockCode,
        mkt: config.value.mkt,
        start: config.value.startDate,
        end: config.value.endDate,
        strategy: config.value.strategyType,
        initialCash: config.value.initialCapital
      }
    })
    result.value = res.data
    // 渲染权益曲线
    setTimeout(() => renderEquityChart(res.data), 100)
  } catch (e: any) {
    errorMsg.value = e?.message || '回测失败，请检查参数'
  } finally {
    running.value = false
  }
}

// ---- Plotly 权益曲线 ----
function renderEquityChart(data: any) {
  if (!chartRef.value || !data?.equityCurve?.length) return

  const eq = data.equityCurve
  const dates = eq.map((e: any) => e.date)
  const values = eq.map((e: any) => e.value)

  // 买卖点
  const buyTrades = data.trades?.filter((t: any) => t.buyDate) || []
  const sellTrades = data.trades?.filter((t: any) => t.sellDate) || []

  const buyX: string[] = [], buyY: number[] = []
  const sellX: string[] = [], sellY: number[] = []
  buyTrades.forEach((t: any) => {
    const pt = eq.find((e: any) => e.date >= t.buyDate)
    if (pt) { buyX.push(pt.date); buyY.push(pt.value) }
  })
  sellTrades.forEach((t: any) => {
    const pt = eq.find((e: any) => e.date >= t.sellDate)
    if (pt) { sellX.push(pt.date); sellY.push(pt.value) }
  })

  const traces: any[] = [
    {
      type: 'scatter', mode: 'lines',
      x: dates, y: values, name: '权益曲线',
      line: { color: '#3b82f6', width: 2 },
      fill: 'tozeroy', fillcolor: 'rgba(59,130,246,0.1)'
    }
  ]
  if (buyX.length) {
    traces.push({ type: 'scatter', mode: 'markers', x: buyX, y: buyY, name: '买入',
      marker: { color: '#10b981', size: 10, symbol: 'triangle-up' } })
  }
  if (sellX.length) {
    traces.push({ type: 'scatter', mode: 'markers', x: sellX, y: sellY, name: '卖出',
      marker: { color: '#f43f5e', size: 10, symbol: 'triangle-down' } })
  }

  const layout = {
    paper_bgcolor: '#0f172a', plot_bgcolor: '#1e293b',
    font: { color: '#94a3b8', family: 'sans-serif' },
    margin: { t: 20, r: 20, b: 50, l: 70 },
    showlegend: true,
    legend: { orientation: 'h', y: 1.1, x: 0.5, xanchor: 'center', font: { color: '#94a3b8', size: 12 } },
    xaxis: { gridcolor: '#334155', linecolor: '#334155', tickcolor: '#334155', type: 'date' },
    yaxis: { gridcolor: '#334155', linecolor: '#334155', tickcolor: '#334155',
      tickformat: ',.0f', title: { text: '账户净值', standoff: 10 } },
    height: 360, dragmode: 'zoom' as const, hovermode: 'x unified'
  }

  Plotly.newPlot(chartRef.value, traces, layout, { displayModeBar: false, responsive: true })
}

// ---- 计算颜色 ----
const returnColor = computed(() => {
  if (!result.value) return 'text-dark'
  return result.value.totalReturn >= 0 ? 'text-accent-green' : 'text-accent-red'
})

onMounted(() => {
  loadStrategies()
  runBacktest()
})
</script>

<template>
  <div class="space-y-4 pb-20">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold">📊 策略回测</h2>
      <NButton type="primary" :loading="running" @click="runBacktest" size="small">
        {{ running ? '回测中…' : '▶ 开始回测' }}
      </NButton>
    </div>

    <!-- 配置卡片 -->
    <NCard title="回测配置" size="small" class="card-base">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <NFormItem label="股票" size="small">
          <NSelect v-model:value="config.stockCode" :options="stockOptions" size="small" />
        </NFormItem>
        <NFormItem label="开始日期" size="small">
          <NInput v-model:value="config.startDate" type="date" size="small" />
        </NFormItem>
        <NFormItem label="结束日期" size="small">
          <NInput v-model:value="config.endDate" type="date" size="small" />
        </NFormItem>
        <NFormItem label="初始资金(¥)" size="small">
          <NInputNumber v-model:value="config.initialCapital" :min="10000" :step="10000" size="small" />
        </NFormItem>
        <NFormItem label="策略" size="small" class="col-span-2">
          <NSelect v-model:value="config.strategyType" :options="strategyOptions" size="small" />
        </NFormItem>
      </div>
    </NCard>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-400">
      ⚠️ {{ errorMsg }}
    </div>

    <!-- 加载状态 -->
    <div v-if="running" class="flex flex-col items-center justify-center py-16 gap-3">
      <NSpin size="large" />
      <span class="text-dark-muted text-sm">正在拉取真实K线数据…</span>
    </div>

    <!-- 回测结果 -->
    <template v-else-if="result">
      <!-- 标的信息 -->
      <div class="bg-dark-card rounded-xl p-4 border border-dark-border">
        <div class="flex items-center gap-3 mb-2">
          <span class="text-lg font-bold">{{ result.stockName }}</span>
          <NTag size="small" type="info">{{ result.stockCode }}</NTag>
          <NTag size="small" type="success">{{ result.strategyName }}</NTag>
        </div>
        <div class="text-xs text-dark-muted">
          {{ result.startDate }} → {{ result.endDate }} · 交易次数 {{ result.totalTrades }} 笔
        </div>
      </div>

      <!-- 核心指标 -->
      <div class="grid grid-cols-3 md:grid-cols-6 gap-2">
        <NCard size="small" class="card-base text-center">
          <div class="text-xs text-dark-muted mb-1">总收益率</div>
          <div class="text-lg font-bold" :class="returnColor">
            {{ result.totalReturn >= 0 ? '+' : '' }}{{ result.totalReturn }}%
          </div>
        </NCard>
        <NCard size="small" class="card-base text-center">
          <div class="text-xs text-dark-muted mb-1">年化收益</div>
          <div class="text-lg font-bold" :class="returnColor">
            {{ result.annualizedReturn >= 0 ? '+' : '' }}{{ result.annualizedReturn }}%
          </div>
        </NCard>
        <NCard size="small" class="card-base text-center">
          <div class="text-xs text-dark-muted mb-1">最大回撤</div>
          <div class="text-lg font-bold text-accent-red">-{{ result.maxDrawdown }}%</div>
        </NCard>
        <NCard size="small" class="card-base text-center">
          <div class="text-xs text-dark-muted mb-1">胜率</div>
          <div class="text-lg font-bold text-accent-green">{{ result.winRate }}%</div>
        </NCard>
        <NCard size="small" class="card-base text-center">
          <div class="text-xs text-dark-muted mb-1">盈亏比</div>
          <div class="text-lg font-bold">{{ result.profitFactor }}</div>
        </NCard>
        <NCard size="small" class="card-base text-center">
          <div class="text-xs text-dark-muted mb-1">夏普比率</div>
          <div class="text-lg font-bold">{{ result.sharpeRatio }}</div>
        </NCard>
      </div>

      <!-- 权益曲线 -->
      <NCard title="📈 权益曲线" size="small" class="card-base">
        <div ref="chartRef" class="w-full" style="min-height:360px" />
      </NCard>

      <!-- 买卖记录 -->
      <NCard title="📋 交易记录" size="small" class="card-base">
        <div v-if="!result.trades?.length" class="text-center py-8 text-dark-muted text-sm">
          本周期无触发交易
        </div>
        <div v-else class="space-y-2 max-h-64 overflow-y-auto">
          <div
            v-for="(t, i) in result.trades"
            :key="i"
            class="flex items-center gap-3 py-2 border-b border-dark-border last:border-0 text-sm"
          >
            <span class="text-xs px-2 py-0.5 rounded font-mono"
              :class="t.profitPct >= 0 ? 'bg-accent-green/10 text-accent-green' : 'bg-accent-red/10 text-accent-red'">
              {{ t.profitPct >= 0 ? '+' : '' }}{{ t.profitPct }}%
            </span>
            <span class="text-dark-muted text-xs">{{ t.buyDate }}</span>
            <span class="text-accent-green text-xs">买 ¥{{ t.buyPrice }}</span>
            <span class="text-dark-muted">→</span>
            <span class="text-accent-red text-xs">卖 ¥{{ t.sellPrice }} ({{ t.sellDate }})</span>
            <span class="ml-auto text-xs text-dark-muted">{{ t.reason }}</span>
          </div>
        </div>
      </NCard>
    </template>

    <!-- 空状态 -->
    <NEmpty v-else-if="!running" description="点击上方按钮开始回测" class="py-16" />
  </div>
</template>