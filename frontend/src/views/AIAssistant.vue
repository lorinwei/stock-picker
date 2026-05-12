<script setup lang="ts">
import { ref } from 'vue'
import { NCard, NButton, NSpace, NInput, NSelect, NScrollbar, NEmpty, NSpin } from 'naive-ui'
import type { AIRequest, AIResponse } from '@/types'

const messages = ref<{ role: 'user' | 'assistant'; content: string; time: string }[]>([])
const inputMessage = ref('')
const selectedType = ref<'strategy' | 'diagnosis' | 'review'>('diagnosis')
const loading = ref(false)

const typeOptions = [
  { label: '策略问诊', value: 'diagnosis' },
  { label: '策略生成', value: 'strategy' },
  { label: '持仓复盘', value: 'review' },
]

const quickQuestions = [
  '分析当前持仓风险',
  '推荐低估值的白马股',
  'MACD金叉选股策略回测',
  '如何设置止损点位',
]

async function sendMessage() {
  if (!inputMessage.value.trim()) return
  
  const userMsg = {
    role: 'user' as const,
    content: inputMessage.value,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  messages.value.push(userMsg)
  const question = inputMessage.value
  inputMessage.value = ''
  loading.value = true

  try {
    // TODO: call API
    await new Promise(r => setTimeout(r, 1000))
    const responses: Record<string, string> = {
      '分析当前持仓风险': '根据当前持仓分析，您的组合最大风险敞口集中在白酒板块，建议适当分散配置，考虑配置银行股降低相关性。整体风险在可控范围内，当前VAR为3.2%。',
      '推荐低估值的白马股': '根据筛选条件，推荐以下低估白马股：\n1. 招商银行(600036) PE: 8.5，估值处于历史低位\n2. 中国平安(601318) PE: 9.2，寿险改革接近尾声\n3. 万科A(000002) PE: 7.8，行业龙头，安全边际高',
      'MACD金叉选股策略回测': 'MACD金叉策略在近一年回测中表现良好：\n- 总收益: +18.5%\n- 年化收益: 18.5%\n- 最大回撤: 12.3%\n- 胜率: 62.5%\n建议配合KDJ指标使用，过滤假信号。',
      '如何设置止损点位': '止损设置建议：\n1. 固定止损：买入价下方8-10%\n2. 移动止损：跟随股价创新高逐步上移\n3. 时间止损：持有超过20个交易日未达预期止损\n4. 逻辑止损：跌破关键支撑位止损',
    }
    const botMsg = {
      role: 'assistant' as const,
      content: responses[question] || '正在分析您的问题，请稍候...',
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    messages.value.push(botMsg)
  } finally {
    loading.value = false
  }
}

function handleQuickQuestion(q: string) {
  inputMessage.value = q
  sendMessage()
}
</script>

<template>
  <div class="h-[calc(100vh-120px)] flex flex-col">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-bold">AI助手</h2>
      <NSelect
        v-model:value="selectedType"
        :options="typeOptions"
        style="width: 140px"
      />
    </div>

    <!-- Chat Area -->
    <NCard class="flex-1 card-base flex flex-col overflow-hidden">
      <NScrollbar class="flex-1 p-4">
        <NEmpty v-if="messages.length === 0" description="向我提问，开始智能分析" />
        <div v-else class="space-y-4">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
          >
            <div
              :class="[
                'max-w-[70%] p-3 rounded-lg',
                msg.role === 'user' 
                  ? 'bg-primary/20 border border-primary/30' 
                  : 'bg-dark-bg border border-dark-border'
              ]"
            >
              <div class="whitespace-pre-wrap text-sm">{{ msg.content }}</div>
              <div class="text-xs text-dark-muted mt-1 text-right">{{ msg.time }}</div>
            </div>
          </div>
        </div>
        <div v-if="loading" class="flex justify-start">
          <div class="bg-dark-bg border border-dark-border p-3 rounded-lg">
            <NSpin size="small" />
            <span class="ml-2 text-sm text-dark-muted">AI正在分析...</span>
          </div>
        </div>
      </NScrollbar>

      <!-- Quick Questions -->
      <div v-if="messages.length === 0" class="px-4 pb-2">
        <div class="text-sm text-dark-muted mb-2">快捷问题：</div>
        <NSpace>
          <NButton
            v-for="q in quickQuestions"
            :key="q"
            size="small"
            secondary
            @click="handleQuickQuestion(q)"
          >
            {{ q }}
          </NButton>
        </NSpace>
      </div>

      <!-- Input -->
      <div class="border-t border-dark-border p-4">
        <div class="flex gap-2">
          <NInput
            v-model:value="inputMessage"
            placeholder="输入您的问题..."
            @keyup.enter="sendMessage"
          />
          <NButton type="primary" @click="sendMessage" :loading="loading">
            发送
          </NButton>
        </div>
      </div>
    </NCard>
  </div>
</template>
