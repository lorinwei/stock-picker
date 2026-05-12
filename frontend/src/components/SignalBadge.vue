<script setup lang="ts">
import { computed } from 'vue'
import type { SignalType } from '@/types'

const props = defineProps<{
  type: SignalType
  size?: 'small' | 'default'
}>()

const config = {
  BUY: { label: '买入', class: 'signal-buy' },
  SELL: { label: '卖出', class: 'signal-sell' },
  WATCH: { label: '观察', class: 'bg-accent-yellow/10 text-accent-yellow border border-accent-yellow/30 px-2 py-0.5 rounded text-xs' },
  HOLD: { label: '持有', class: 'bg-dark-muted/10 text-dark-muted border border-dark-muted/30 px-2 py-0.5 rounded text-xs' }
}

const badgeClass = computed(() => {
  const base = props.size === 'small' ? 'text-xs px-1.5 py-0.5' : 'text-sm px-2 py-0.5'
  return `${base} rounded ${config[props.type].class}`
})
</script>

<template>
  <span :class="badgeClass">{{ config[type].label }}</span>
</template>
