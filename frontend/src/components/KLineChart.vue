<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import Plotly from 'plotly.js-dist'
import type { KLineData, TradeSignal, IndicatorType } from '@/types'

const props = defineProps<{
  data: KLineData[]
  indicators: IndicatorType[]
  signals?: TradeSignal[]
  equityCurve?: { date: string; value: number }[]
}>()

const chartRef = ref<HTMLDivElement>()
let plotlyInstance: any = null

const hasCandlestick = computed(() => props.data && props.data.length > 0)
const hasEquity = computed(() => props.equityCurve && props.equityCurve.length > 0)

function generateLayout(height: number) {
  return {
    paper_bgcolor: '#0d1117',
    plot_bgcolor: '#161b22',
    font: { color: '#c9d1d9', family: 'sans-serif' },
    margin: { t: 20, r: 20, b: 40, l: 60 },
    showlegend: false,
    xaxis: {
      gridcolor: '#30363d',
      linecolor: '#30363d',
      tickcolor: '#30363d',
      rangeslider: { visible: false },
      type: 'date'
    },
    yaxis: {
      gridcolor: '#30363d',
      linecolor: '#30363d',
      tickcolor: '#30363d',
      title: { text: '价格', standoff: 10 },
      tickformat: ',.2f'
    },
    height,
    dragmode: 'zoom' as const,
    hovermode: 'x unified'
  }
}

async function renderCandlestickChart() {
  if (!chartRef.value || !hasCandlestick.value) return

  const data = props.data
  const dates = data.map(d => d.date)
  const volumes = data.map(d => d.volume)

  const traces: any[] = [
    {
      type: 'candlestick',
      x: dates,
      open: data.map(d => d.open),
      high: data.map(d => d.high),
      low: data.map(d => d.low),
      close: data.map(d => d.close),
      name: 'K线',
      increasing: { line: { color: '#00ff88' }, fillcolor: 'rgba(0, 255, 136, 0.3)' },
      decreasing: { line: { color: '#ff4757' }, fillcolor: 'rgba(255, 71, 87, 0.3)' },
      yaxis: 'y'
    },
    {
      type: 'bar',
      x: dates,
      y: volumes,
      name: '成交量',
      marker: { color: '#00d4ff', opacity: 0.5 },
      yaxis: 'y2'
    }
  ]

  // MA indicators
  if (props.indicators.includes('MA')) {
    const closes = data.map(d => d.close)
    const ma5 = calculateMA(closes, 5)
    const ma10 = calculateMA(closes, 10)
    const ma20 = calculateMA(closes, 20)
    traces.push(
      { type: 'scatter', mode: 'lines', x: dates, y: ma5, name: 'MA5', line: { color: '#ffd93d', width: 1 } },
      { type: 'scatter', mode: 'lines', x: dates, y: ma10, name: 'MA10', line: { color: '#00d4ff', width: 1 } },
      { type: 'scatter', mode: 'lines', x: dates, y: ma20, name: 'MA20', line: { color: '#ff6b81', width: 1 } }
    )
  }

  // Signals
  if (props.signals && props.signals.length > 0) {
    const buySignals = props.signals.filter(s => s.type === 'BUY')
    const sellSignals = props.signals.filter(s => s.type === 'SELL')
    
    if (buySignals.length > 0) {
      traces.push({
        type: 'scatter',
        mode: 'markers',
        x: buySignals.map(s => s.date),
        y: buySignals.map(s => s.price),
        name: '买入信号',
        marker: { symbol: 'triangle-up', size: 14, color: '#00ff88', line: { color: '#000', width: 2 } }
      })
    }
    if (sellSignals.length > 0) {
      traces.push({
        type: 'scatter',
        mode: 'markers',
        x: sellSignals.map(s => s.date),
        y: sellSignals.map(s => s.price),
        name: '卖出信号',
        marker: { symbol: 'triangle-down', size: 14, color: '#ff4757', line: { color: '#000', width: 2 } }
      })
    }
  }

  const layout = generateLayout(500)
  ;(layout as any).xaxis.title = ''
  ;(layout as any).yaxis2 = {
    title: { text: '成交量', standoff: 10 },
    overlaying: 'y',
    side: 'right',
    gridcolor: 'transparent',
    showgrid: false
  }

  if (plotlyInstance) {
    await Plotly.react(chartRef.value, traces, layout, { responsive: true })
  } else {
    plotlyInstance = await Plotly.newPlot(chartRef.value, traces, layout, { responsive: true })
  }
}

async function renderEquityChart() {
  if (!chartRef.value || !hasEquity.value) return

  const data = props.equityCurve!
  const traces: any[] = [{
    type: 'scatter',
    mode: 'lines',
    x: data.map(d => d.date),
    y: data.map(d => d.value),
    name: '权益曲线',
    line: { color: '#00d4ff', width: 2 },
    fill: 'tozeroy',
    fillcolor: 'rgba(0, 212, 255, 0.2)'
  }]

  // Signals on equity curve
  if (props.signals && props.signals.length > 0) {
    const buySignals = props.signals.filter(s => s.type === 'BUY')
    const sellSignals = props.signals.filter(s => s.type === 'SELL')
    const dateToEquity = new Map(data.map(d => [d.date, d.value]))
    
    if (buySignals.length > 0) {
      const buyY = buySignals.map(s => dateToEquity.get(s.date) || s.price)
      traces.push({
        type: 'scatter',
        mode: 'markers',
        x: buySignals.map(s => s.date),
        y: buyY,
        name: '买入',
        marker: { symbol: 'triangle-up', size: 14, color: '#00ff88' }
      })
    }
    if (sellSignals.length > 0) {
      const sellY = sellSignals.map(s => dateToEquity.get(s.date) || s.price)
      traces.push({
        type: 'scatter',
        mode: 'markers',
        x: sellSignals.map(s => s.date),
        y: sellY,
        name: '卖出',
        marker: { symbol: 'triangle-down', size: 14, color: '#ff4757' }
      })
    }
  }

  const layout = generateLayout(400)

  if (plotlyInstance) {
    await Plotly.react(chartRef.value, traces, layout, { responsive: true })
  } else {
    plotlyInstance = await Plotly.newPlot(chartRef.value, traces, layout, { responsive: true })
  }
}

function calculateMA(closes: number[], period: number): number[] {
  const result: number[] = []
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      result.push(NaN)
    } else {
      const sum = closes.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0)
      result.push(sum / period)
    }
  }
  return result
}

watch(() => [props.data, props.indicators, props.signals, props.equityCurve], () => {
  if (hasCandlestick.value) {
    renderCandlestickChart()
  } else if (hasEquity.value) {
    renderEquityChart()
  }
}, { deep: true })

onMounted(async () => {
  if (hasCandlestick.value) {
    await renderCandlestickChart()
  } else if (hasEquity.value) {
    await renderEquityChart()
  }
})

onUnmounted(() => {
  if (plotlyInstance) {
    Plotly.purge(chartRef.value!)
    plotlyInstance = null
  }
})
</script>

<template>
  <div ref="chartRef" class="w-full" />
</template>
