<template>
  <div class="page">
    <div class="card fade fade-1">
      <div class="card-header">账户概览</div>
      <div style="display:flex;gap:24px;margin-bottom:10px">
        <div><div style="font-size:12px;color:var(--text3)">总资产</div><div class="num" style="font-size:20px;font-weight:700">{{ fmt(totalValue + availableCash) }}</div></div>
        <div><div style="font-size:12px;color:var(--text3)">总盈亏</div><div :class="totalProfit >= 0 ? 'up' : 'down'" class="num" style="font-size:20px;font-weight:700">{{ totalProfit >= 0 ? '+' : '' }}{{ fmt(totalProfit) }} <span style="font-size:14px;font-weight:500">({{ profitPct }})</span></div></div>
      </div>
      <div style="height:4px;background:var(--surface2);border-radius:2px;overflow:hidden">
        <div style="height:100%;background:linear-gradient(90deg,var(--blue),var(--green));border-radius:2px;transition:width 0.3s" :style="{width: posRatio + '%'}"></div>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text3);margin-top:4px">
        <span>仓位 {{ posRatio }}%</span>
        <span>可用 {{ fmt(availableCash) }}</span>
      </div>
    </div>

    <div v-if="warnings.length" class="card fade fade-2" style="border-color:var(--red-bg);background:var(--red-bg)">
      <div class="card-header" style="color:var(--red)">风控提醒</div>
      <div v-for="w in warnings" style="font-size:13px;color:var(--red);padding:2px 0">{{ w }}</div>
    </div>

    <div v-if="loading" class="state-box"><div class="msg">加载中...</div></div>

    <div v-else-if="positions.length === 0" class="state-box">
      <div class="msg">暂无持仓</div>
      <div class="sub">在首页查看今日选股信号后买入</div>
    </div>

    <div v-else class="card fade fade-3" style="padding:0">
      <div v-for="(p,i) in positions" :key="p.id" class="pos-item" style="border-bottom:1px solid var(--border)">
        <div class="top">
          <span class="name">{{ p.name }}</span>
          <span class="code">{{ shortCode(p.code) }}</span>
          <span class="qty">{{ p.quantity }}股</span>
          <span v-if="p.risk_status" class="status tag" :class="riskTag(p.risk_status.status)" style="margin-left:auto">{{ riskText(p.risk_status.status) }}</span>
        </div>
        <div class="detail">
          <div><span class="l">买入</span><span class="v num">¥{{ p.buy_price || 0 }}</span></div>
          <div><span class="l">现价</span><span class="v num">{{ p.current_price ? '¥' + p.current_price : '--' }}</span></div>
          <div><span class="l">盈亏</span><span :class="(p.profit_pct || 0) >= 0 ? 'up' : 'down'" class="num">{{ p.profit_pct || 0 }}%</span></div>
        </div>
        <div class="stop">止损 ¥{{ p.stop_loss_price || '--' }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api'

const loading = ref(true)
const positions = ref<any[]>([])
const totalValue = ref(0)
const totalProfit = ref(0)
const profitPct = ref('0.00')
const availableCash = ref(0)
const posRatio = ref(0)
const warnings = ref<string[]>([])

function fmt(n: number) { return '¥' + (n || 0).toFixed(2) }
function shortCode(c: string) { return (c || '').replace(/^[szsh]+/, '') }
function riskTag(s: string) { return { stop_loss:'tag-red', warning:'tag-gold', take_profit:'tag-green', time_stop:'tag-blue', normal:'tag-blue' }[s] || 'tag-blue' }
function riskText(s: string) { return { stop_loss:'止损', warning:'警戒', take_profit:'止盈', time_stop:'时间止盈', normal:'正常' }[s] || s || '--' }

onMounted(async () => {
  try {
    const res: any = await api.get('/portfolio')
    const d = res.data || {}
    positions.value = d.positions || []
    totalValue.value = d.totalValue || 0
    totalProfit.value = d.totalProfit || 0
    profitPct.value = (d.profitPercent || 0).toFixed(2)
    availableCash.value = d.availableCash || 0
    const tot = totalValue.value + availableCash.value
    posRatio.value = tot > 0 ? Math.round(totalValue.value / tot * 100) : 0

    const ws: string[] = []
    for (const p of positions.value) {
      const rs = p.risk_status
      if (!rs) continue
      if (rs.status === 'stop_loss') ws.push(`${p.name} 触发止损`)
      if (rs.status === 'warning') ws.push(`${p.name} 接近止损`)
    }
    warnings.value = ws
  } catch {}
  loading.value = false
})
</script>
