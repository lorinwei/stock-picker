<script setup lang="ts">
import { ref } from 'vue'
import { NCard, NButton, NSpace, NInput, NScrollbar, NEmpty, NSpin } from 'naive-ui'
import api from '@/api'

const messages = ref<{ role: 'user' | 'assistant'; content: string; time: string }[]>([])
const inputMessage = ref('')
const loading = ref(false)

const quickQuestions = [
  '今天大盘怎么样',
  'AI推荐什么股票',
  '我的持仓怎么样',
  '最近哪些板块强',
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
    const res = await api.post('/ai/chat', { message: question })
    // 拦截器返回 { code, data: { reply } }，所以 res.data 是 { reply }
    const replyText = (res as any).data?.reply || (res as any).reply || '抱歉，AI暂时无法回答这个问题。'
    // 把 markdown 的 ** 替换成更轻量的格式（前端用 pre-wrap 显示）
    const botMsg = {
      role: 'assistant' as const,
      content: replyText,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    messages.value.push(botMsg)
  } catch (e: any) {
    messages.value.push({
      role: 'assistant' as const,
      content: `查询失败：${e?.message || '网络错误'}`,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })
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
