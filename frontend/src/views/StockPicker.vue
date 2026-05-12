<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NDataTable, NButton, NSelect, NSpace, NInput, NTag } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import SignalBadge from '@components/SignalBadge.vue'
import type { PickerResult, SignalType } from '@/types'

const columns: DataTableColumns<PickerResult> = [
  { title: '股票代码', key: 'code', width: 120 },
  { title: '股票名称', key: 'name', width: 120 },
  {
    title: '综合评分',
    key: 'score',
    width: 120,
    render: (row) => {
      const color = row.score >= 80 ? 'success' : row.score >= 60 ? 'warning' : 'error'
      return h(NTag, { type: color, round: true }, () => row.score.toString())
    }
  },
  {
    title: '信号',
    key: 'signals',
    width: 200,
    render: (row) => {
      return h(NSpace, { size: 'small' }, () =>
        row.signals.map((s: SignalType) => h(SignalBadge, { type: s, size: 'small' }))
      )
    }
  },
  { title: '推荐理由', key: 'reasons', ellipsis: { tooltip: true } },
  {
    title: '涨跌幅',
    key: 'change',
    width: 100,
    render: (row) => {
      const color = row.change >= 0 ? 'text-accent-green' : 'text-accent-red'
      return h('span', { class: color }, `${row.change >= 0 ? '+' : ''}${row.change.toFixed(2)}%`)
    }
  },
  { title: '成交量', key: 'volume', width: 120 },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row) => {
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, { size: 'small', onClick: () => viewDetail(row.code) }, () => '详情'),
      ])
    }
  }
]

import { h } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const pickerResults = ref<PickerResult[]>([])
const strategyOptions = [
  { label: 'MACD金叉策略', value: 'macd' },
  { label: 'KDJ超卖策略', value: 'kdj' },
  { label: '量价齐升策略', value: 'volume' },
  { label: '综合评分策略', value: 'combined' },
]
const selectedStrategy = ref('combined')

onMounted(() => {
  // Mock data
  pickerResults.value = [
    { code: '600519', name: '贵州茅台', score: 88, signals: ['BUY', 'WATCH'], reasons: ['MACD金叉', '量价齐升'], change: 2.35, volume: 2345678 },
    { code: '000858', name: '五粮液', score: 82, signals: ['BUY'], reasons: ['KDJ金叉', '站上MA5'], change: 1.85, volume: 1234567 },
    { code: '600036', name: '招商银行', score: 76, signals: ['BUY', 'HOLD'], reasons: ['估值偏低', '北向资金买入'], change: 0.95, volume: 3456789 },
    { code: '300750', name: '宁德时代', score: 74, signals: ['WATCH'], reasons: ['技术面企稳'], change: -0.52, volume: 2345678 },
    { code: '601318', name: '中国平安', score: 71, signals: ['HOLD'], reasons: ['布林中轨支撑'], change: 0.23, volume: 4567890 },
  ]
})

function viewDetail(code: string) {
  router.push(`/analysis/${code}`)
}

function handleSearch() {
  // TODO: call API
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold">智能选股</h2>
      <NSpace align="center">
        <NSelect
          v-model:value="selectedStrategy"
          :options="strategyOptions"
          placeholder="选择策略"
          style="width: 160px"
        />
        <NButton type="primary" @click="handleSearch">开始选股</NButton>
      </NSpace>
    </div>

    <NCard title="选股结果" class="card-base">
      <NDataTable
        :columns="columns"
        :data="pickerResults"
        :bordered="false"
        :row-key="(row: PickerResult) => row.code"
      />
    </NCard>

    <NCard title="筛选条件" class="card-base">
      <p class="text-dark-muted">支持多维度筛选：技术指标、财务数据、市场情绪、资金流向等</p>
    </NCard>
  </div>
</template>
