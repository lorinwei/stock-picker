<template>
  <div class="page">
    <!-- 市场状态条 -->
    <div class="market-bar" :class="typeClass">
      <span class="label">市场</span>
      <span class="status" :class="statusTag">{{ statusText }}</span>
      <span style="font-size:12px;color:var(--text3);margin-left:auto">仓位上限 {{ posLimit }}%</span>
    </div>

    <div v-if="loading" class="state-box"><div class="msg">正在扫描全市场...</div><div class="sub">缠论分型分析进行中</div></div>

    <div v-else-if="stocks.length === 0" class="state-box">
      <div class="msg">当前无符合条件的缠论买点</div>
      <div class="sub">系统持续跟踪中</div>
    </div>

    <div v-else class="card" style="padding:0">
      <div v-for="(s,i) in stocks" :key="s.code" class="signal-card" style="border-bottom:1px solid var(--border);padding:12px 14px">
        <div class="top">
          <span class="rank" style="font-size:12px">#{{ s.rank || (i+1) }}</span>
          <span class="name">{{ s.name }}</span>
          <span class="code">{{ shortCode(s.code) }}</span>
          <span class="score num" style="margin-left:auto;color:var(--gold);font-weight:600">{{ s.score }}</span>
        </div>
        <span class="bp" :class="'bp-' + bpLevel(s.buy_point)">{{ bpLabel(s.buy_point) }}</span>
        <div class="meta">
          <span><span class="l">现价</span><span class="v num">¥{{ s.price || '--' }}</span></span>
          <span><span class="l">PE</span><span class="v num">{{ s.pe || '--' }}</span></span>
          <span><span class="l">ROE</span><span class="v num">{{ s.roe || '--' }}%</span></span>
          <span v-if="s.change_pct"><span class="l">涨跌</span><span :class="s.change_pct >= 0 ? 'up' : 'down'" class="num">{{ s.change_pct >= 0 ? '+' : '' }}{{ s.change_pct }}%</span></span>
        </div>
        <div class="reasons" v-if="s.entry_reasons && s.entry_reasons.length">
          <span v-for="r in s.entry_reasons.slice(0,3)">{{ r }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api'

const loading = ref(true)
const stocks = ref<any[]>([])
const statusText = ref('--')
const statusTag = ref('tag-gold')
const posLimit = ref(40)
const typeClass = ref('')

function shortCode(c: string) { return (c || '').replace(/^[szsh]+/, '') }
function bpLevel(bp: string) { return { '1st_buy': '1', '2nd_buy': '2', '3rd_buy': '3' }[bp] || '0' }
function bpLabel(bp: string) { return { '1st_buy': '一买', '2nd_buy': '二买', '3rd_buy': '三买' }[bp] || bp || '--' }

onMounted(async () => {
  try {
    const [mr, sr]: any = await Promise.all([
      api.get('/market/overview').catch(() => ({ data: {} })),
      api.get('/picker/signals').catch(() => ({ data: {} })),
    ])
    const md = mr.data || {}
    const m = md.marketStatus || '震荡'
    statusText.value = m
    statusTag.value = m === '牛市' ? 'tag-green' : m === '熊市' ? 'tag-red' : 'tag-gold'
    posLimit.value = md.positionLimit ? Math.round(md.positionLimit * 100) : 40
    stocks.value = (sr.data?.signals || []).slice(0, 20)
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.market-bar { display:flex; align-items:center; gap:10px; padding:10px 14px; border-radius:var(--radius); margin-bottom:14px; border:1px solid var(--border); font-size:13px; }
.market-bar .label { color:var(--text3); font-size:12px; }
</style>
