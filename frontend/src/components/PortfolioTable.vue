<script setup lang="ts">
import { h } from 'vue'
import { NDataTable, NButton, NSpace, NTag } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { Position } from '@/types'
import SignalBadge from './SignalBadge.vue'

const props = defineProps<{
  positions: Position[]
}>()

const columns: DataTableColumns<Position> = [
  { title: '股票代码', key: 'code', width: 120 },
  { title: '股票名称', key: 'name', width: 120 },
  { title: '持仓数量', key: 'shares', width: 100, align: 'right' },
  { title: '成本价', key: 'cost', width: 100, align: 'right', render: (r) => `¥${r.cost.toFixed(2)}` },
  { title: '现价', key: 'currentPrice', width: 100, align: 'right', render: (r) => `¥${r.currentPrice.toFixed(2)}` },
  {
    title: '市值',
    key: 'marketValue',
    width: 120,
    align: 'right',
    render: (r) => `¥${r.marketValue.toLocaleString()}`
  },
  {
    title: '盈亏',
    key: 'profit',
    width: 120,
    align: 'right',
    render: (r) => {
      const color = r.profit >= 0 ? 'success' : 'error'
      return h(NTag, { type: color }, () =>
        `${r.profit >= 0 ? '+' : ''}¥${r.profit.toLocaleString()}`
      )
    }
  },
  {
    title: '收益率',
    key: 'profitPercent',
    width: 100,
    align: 'right',
    render: (r) => {
      const color = r.profitPercent >= 0 ? 'success' : 'error'
      return h(NTag, { type: color }, () =>
        `${r.profitPercent >= 0 ? '+' : ''}${r.profitPercent.toFixed(2)}%`
      )
    }
  },
  {
    title: '占比',
    key: 'positionRatio',
    width: 100,
    align: 'right',
    render: (r) => `${r.positionRatio.toFixed(1)}%`
  },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render: (r) => {
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, { size: 'small', type: 'primary', ghost: true }, () => '加仓'),
        h(NButton, { size: 'small', type: 'error', ghost: true }, () => '减仓'),
      ])
    }
  }
]

const data = props.positions.length > 0 ? props.positions : [
  { code: '600519', name: '贵州茅台', shares: 100, cost: 1750, currentPrice: 1850, marketValue: 185000, profit: 10000, profitPercent: 5.71, positionRatio: 18.5 },
  { code: '000858', name: '五粮液', shares: 500, cost: 165, currentPrice: 168.5, marketValue: 84250, profit: 1750, profitPercent: 2.12, positionRatio: 8.4 },
  { code: '600036', name: '招商银行', shares: 2000, cost: 34.5, currentPrice: 35.8, marketValue: 71600, profit: 2600, profitPercent: 3.77, positionRatio: 7.2 },
]
</script>

<template>
  <NDataTable
    :columns="columns"
    :data="data"
    :bordered="false"
    :row-key="(row: Position) => row.code"
    class="card-base"
  />
</template>
