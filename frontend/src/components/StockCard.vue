<script setup lang="ts">
import { computed } from 'vue'
import type { Stock } from '@/types'

const props = defineProps<{
  stock: Stock
  size?: 'small' | 'default'
}>()

const changeClass = computed(() =>
  props.stock.change >= 0 ? 'text-accent-green' : 'text-accent-red'
)

const formattedChange = computed(() => {
  const sign = props.stock.change >= 0 ? '+' : ''
  return `${sign}${props.stock.changePercent.toFixed(2)}%`
})

const formattedPrice = computed(() => `¥${props.stock.price.toFixed(2)}`)

const formattedVolume = computed(() => {
  const vol = props.stock.volume
  if (vol >= 100000000) return `${(vol / 100000000).toFixed(2)}亿`
  if (vol >= 10000) return `${(vol / 10000).toFixed(2)}万`
  return vol.toString()
})
</script>

<template>
  <div :class="['card-base cursor-pointer hover:border-accent-cyan/50 transition', size === 'small' ? 'p-3' : '']">
    <div class="flex items-center justify-between mb-2">
      <div>
        <span class="font-medium">{{ stock.name }}</span>
        <span class="text-sm text-dark-muted ml-2">{{ stock.code }}</span>
      </div>
      <span :class="['font-bold', changeClass]">{{ formattedChange }}</span>
    </div>
    <div class="flex items-center justify-between text-sm">
      <span class="text-xl font-bold">{{ formattedPrice }}</span>
      <span class="text-dark-muted">成交量: {{ formattedVolume }}</span>
    </div>
  </div>
</template>
