<template>
  <div class="page">
    <div class="card fade fade-1">
      <div class="card-header">策略回测</div>
      <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">
        <input v-model="stockCode" placeholder="股票代码,如 600519" class="input" style="flex:1;min-width:120px">
        <select v-model="strategy" class="input" style="width:120px">
          <option value="value_trend">价值趋势</option>
          <option value="momentum">动量策略</option>
          <option value="breakout">突破策略</option>
        </select>
        <button class="btn btn-primary btn-sm" @click="run">回测</button>
      </div>
      <div v-if="result" style="font-size:13px">
        <div style="display:flex;gap:16px;padding:8px 0;border-bottom:1px solid var(--border);flex-wrap:wrap">
          <span><span style="color:var(--text3)">总收益</span> <span class="num" :class="result.total_return >= 0 ? 'up' : 'down'">{{ result.total_return }}%</span></span>
          <span><span style="color:var(--text3)">回撤</span> <span class="num down">{{ result.max_drawdown }}%</span></span>
          <span><span style="color:var(--text3)">胜率</span> <span class="num">{{ result.win_rate }}%</span></span>
          <span><span style="color:var(--text3)">交易</span> <span class="num">{{ result.num_trades }}次</span></span>
        </div>
        <div v-if="result.trades && result.trades.length" style="margin-top:8px">
          <div style="font-size:12px;color:var(--text3);margin-bottom:4px">最近交易</div>
          <div v-for="t in result.trades.slice(-5)" :key="t.entry_date" style="display:flex;gap:12px;font-size:12px;padding:4px 0;border-bottom:1px solid var(--border)">
            <span>{{ t.entry_date }}</span>
            <span>买入 ¥{{ t.entry_price }}</span>
            <span v-if="t.exit_date">{{ t.exit_date }} ¥{{ t.exit_price }}</span>
            <span :class="t.pnl >= 0 ? 'up' : 'down'" class="num">{{ t.pnl >= 0 ? '+' : '' }}{{ t.pnl }}%</span>
          </div>
        </div>
      </div>
      <div v-if="running" style="padding:12px 0;text-align:center;color:var(--text3)">回测执行中...</div>
      <div v-if="error" style="padding:8px 0;color:var(--red);font-size:13px">{{ error }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '@/api'

const stockCode = ref('600519')
const strategy = ref('value_trend')
const result = ref<any>(null)
const running = ref(false)
const error = ref('')

async function run() {
  if (!stockCode.value.trim()) return
  running.value = true
  error.value = ''
  result.value = null
  try {
    const res: any = await api.post('/backtest/run', {
      stock_code: stockCode.value,
      strategy_type: strategy.value,
      initial_cash: 100000,
    })
    if (res.data?.error) {
      error.value = res.data.error
    } else {
      result.value = res.data
    }
  } catch (e: any) {
    error.value = e.message || '回测失败'
  }
  running.value = false
}
</script>

<style scoped>
.input { padding:8px 12px; border-radius:var(--radius2); border:1px solid var(--border); background:var(--bg2); color:var(--text); font-size:13px; outline:none; }
.input:focus { border-color: var(--blue); }
select.input { cursor: pointer; }
</style>
