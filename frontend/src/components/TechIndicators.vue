<script setup lang="ts">
import { NSpace, NCheckbox, NCheckboxGroup, NButton, NPopover } from 'naive-ui'
import type { IndicatorType } from '@/types'

const props = defineProps<{
  selected: IndicatorType[]
}>()

const emit = defineEmits<{
  change: [indicators: IndicatorType[]]
}>()

const allIndicators: { label: string; value: IndicatorType; desc: string }[] = [
  { label: 'MA均线', value: 'MA', desc: '移动平均线' },
  { label: 'MACD', value: 'MACD', desc: '指数平滑异同移动平均线' },
  { label: 'RSI', value: 'RSI', desc: '相对强弱指标' },
  { label: 'KDJ', value: 'KDJ', desc: '随机指标' },
  { label: 'BOLL', value: 'BOLL', desc: '布林带' },
  { label: '九转', value: 'NineTurn', desc: '九转序列' },
]

function toggleIndicator(value: IndicatorType) {
  const newSelected = props.selected.includes(value)
    ? props.selected.filter(v => v !== value)
    : [...props.selected, value]
  emit('change', newSelected)
}

function reset() {
  emit('change', ['MA', 'MACD'])
}
</script>

<template>
  <div class="card-base">
    <div class="flex items-center justify-between mb-3">
      <span class="text-sm text-dark-muted">技术指标</span>
      <NButton size="tiny" @click="reset">重置</NButton>
    </div>
    <NSpace>
      <NPopover
        v-for="ind in allIndicators"
        :key="ind.value"
        trigger="hover"
        placement="top"
      >
        <template #trigger>
          <button
            :class="[
              'px-3 py-1.5 rounded text-sm border transition',
              selected.includes(ind.value)
                ? 'bg-accent-cyan/20 border-accent-cyan text-accent-cyan'
                : 'bg-dark-bg border-dark-border text-dark-muted hover:border-dark-muted'
            ]"
            @click="toggleIndicator(ind.value)"
          >
            {{ ind.label }}
          </button>
        </template>
        <div>
          <div class="font-medium">{{ ind.label }}</div>
          <div class="text-xs text-dark-muted">{{ ind.desc }}</div>
        </div>
      </NPopover>
    </NSpace>
  </div>
</template>
