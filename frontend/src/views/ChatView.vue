<template>
  <div class="page chat-view">
    <div class="page-title fade-in fade-in-1">💬 AI智能问答</div>

    <!-- 快捷问题 -->
    <div class="quick-questions fade-in fade-in-2">
      <button
        v-for="q in quickQuestions"
        :key="q"
        class="quick-btn"
        @click="sendQuick(q)"
      >
        {{ q }}
      </button>
    </div>

    <!-- 对话区域 -->
    <div class="chat-history" ref="chatEl">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="chat-msg"
        :class="msg.role"
      >
        <div class="msg-avatar">{{ msg.role === 'ai' ? '🤖' : '👤' }}</div>
        <div class="msg-bubble card" :class="msg.role === 'ai' ? 'ai-bubble' : 'user-bubble'">
          <div v-if="msg.role === 'ai'" class="ai-label">StockMind AI</div>
          <div class="msg-content" v-html="formatContent(msg.content)"></div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="chat-input-bar">
      <input
        v-model="inputText"
        class="chat-input"
        placeholder="问股票、问大盘、问持仓..."
        @keyup.enter="sendMessage"
      />
      <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim()">
        ➤
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'

interface Message {
  role: 'ai' | 'user'
  content: string
  time: string
}

const chatEl = ref<HTMLElement>()
const inputText = ref('')

const quickQuestions = [
  '大盘今天怎么样？',
  '推荐几只股票',
  '看看我的持仓',
  '茅台还能买吗'
]

const messages = ref<Message[]>([
  {
    role: 'ai',
    content: '您好！我是StockMind AI，您的智能炒股助手。\n\n我可以帮您：\n📊 分析个股走势\n🧠 诊断持仓风险\n💡 推荐优质股票\n📈 解读大盘行情\n\n有什么想聊的？',
    time: ''
  }
])

const formatContent = (content: string) => {
  return content
    .replace(/\n/g, '<br>')
    .replace(/✅/g, '<span style="color:var(--success)">✅</span>')
    .replace(/⚠️/g, '<span style="color:var(--accent)">⚠️</span>')
    .replace(/🔴/g, '<span style="color:var(--danger)">🔴</span>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

const scrollBottom = () => {
  nextTick(() => {
    if (chatEl.value) {
      chatEl.value.scrollTop = chatEl.value.scrollHeight
    }
  })
}

const sendMessage = () => {
  const text = inputText.value.trim()
  if (!text) return

  messages.value.push({ role: 'user', content: text, time: '' })
  inputText.value = ''
  scrollBottom()

  // 模拟AI回复
  setTimeout(() => {
    const reply = getAIReply(text)
    messages.value.push({ role: 'ai', content: reply, time: '' })
    scrollBottom()
  }, 800)
}

const sendQuick = (q: string) => {
  inputText.value = q
  sendMessage()
}

const getAIReply = (question: string): string => {
  if (question.includes('大盘') || question.includes('今天怎么样')) {
    return `📊 **今日大盘分析**\n\n沪深300当前 **3820.5**，上涨 **+0.82%** ↑\n创业板指 **1568.3**，上涨 **+1.15%** ↑\n\n✅ **市场状态：多头格局**\n- 三大指数均在20日均线上方\n- 成交量温和放大\n- 北向资金今日净买入 **+32亿**\n\n💡 **操作建议**：可适度加仓，但避免追高。关注新能源、白酒板块机会。`
  }

  if (question.includes('推荐')) {
    return `🚀 **今日AI推荐**\n\n**贵州茅台 600519** ⭐评分92\n- 买入区间：¥1840~1880\n- 目标价：¥1980\n- 止损价：¥1757\n- AI理由：北向资金连续3日净买入，MACD金叉，ROE维持25%\n\n**宁德时代 300750** ⭐评分88\n- 买入区间：¥320~330\n- 目标价：¥350\n- 止损价：¥305\n- AI理由：新能源政策利好，量价齐升，机构加仓`
  }

  if (question.includes('持仓')) {
    return `💼 **您的持仓状态**\n\n✅ **比亚迪** 002594\n浮盈 **+¥1,360** (+2.85%) 状态正常\n建议持有，突破¥250考虑止盈\n\n⚠️ **宁德时代** 300750\n浮亏 **-¥3,810** (-6.41%) 接近止损\n建议减仓50%，等待反弹确认\n\n⚠️ **贵州茅台** 600519\n浮盈 **+¥5,000** (+1.39%) 状态正常\n建议持有，目标¥1950`
  }

  if (question.includes('茅台') || question.includes('600519')) {
    return `🏥 **贵州茅台 600519 诊断**\n\n✅ **基本面**：业绩稳定，ROE 25%，毛利率维持80%以上，现金流健康\n✅ **资金面**：北向资金连续3日净买入，共计 **+2.8亿**\n✅ **技术面**：MACD金叉，20日均线支撑有效\n⚠️ **估值面**：PE 32，处于历史中位偏上\n⚠️ **风险点**：白酒消费数据近期偏弱\n\n💡 **建议**：可轻仓（10%），首仓5%，回踩确认再加。止损设¥1750，目标¥1950。`
  }

  return `收到您的问题：${question}\n\n我正在分析，请稍候... 或者换个问法试试？\n\n例如：「大盘怎么样」「推荐股票」「看看持仓」`
}
</script>

<style scoped>
.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.quick-btn {
  background: var(--bg-elevated);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.quick-btn:active {
  transform: scale(0.96);
  border-color: var(--primary);
  color: var(--primary);
}

.chat-history {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: calc(100vh - 280px);
  overflow-y: auto;
  margin-bottom: 16px;
  padding-right: 4px;
}

.chat-msg {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.chat-msg.ai { flex-direction: row; }
.chat-msg.user { flex-direction: row-reverse; }

.msg-avatar {
  font-size: 22px;
  min-width: 36px;
  text-align: center;
}

.ai-bubble {
  flex: 1;
  max-width: 85%;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px 16px 16px 4px;
  padding: 12px 14px;
}

.user-bubble {
  flex: 1;
  max-width: 85%;
  background: var(--primary);
  color: white;
  border-radius: 16px 16px 4px 16px;
  padding: 12px 14px;
  font-size: 14px;
}

.ai-label {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  font-weight: 600;
}

.msg-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.user-bubble .msg-content {
  color: white;
}

.chat-input-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 8px 8px 8px 16px;
}

.chat-input {
  flex: 1;
  background: none;
  border: none;
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
}

.chat-input::placeholder {
  color: var(--text-dim);
}

.send-btn {
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.send-btn:active {
  transform: scale(0.95);
}

.send-btn:disabled {
  background: var(--bg-elevated);
  color: var(--text-dim);
  cursor: not-allowed;
}
</style>