<template>
  <div class="page">
    <!-- 大盘 -->
    <div class="market-bar fade fade-1" :class="marketChg >= 0 ? '' : 'down'">
      <span class="label">沪深300</span>
      <span class="value num">{{ hs300 || '--' }}</span>
      <span class="chg" :class="marketChg >= 0 ? 'up' : 'down'">
        {{ marketChg >= 0 ? '+' : '' }}{{ marketChg }}%
      </span>
      <span class="status" :class="statusTag">{{ statusText }}</span>
    </div>

    <!-- 今日金股 -->
    <div v-if="mainStock.name" class="card fade fade-2">
      <div class="card-header">今日缠论信号</div>
      <div class="signal-card" style="margin:-6px -14px">
        <div class="top">
          <span class="rank">#1</span>
          <span class="name">{{ mainStock.name }}</span>
          <span class="code">{{ shortCode(mainStock.code) }}</span>
          <span class="score num" style="color:var(--gold);font-weight:700">{{ mainStock.score }}</span>
        </div>
        <span class="bp" :class="'bp-' + bpLevel(mainStock.buyPoint)">{{ bpLabel(mainStock.buyPoint) }}</span>
        <div class="meta" style="margin-top:6px">
          <span><span class="l">现价</span><span class="v num">¥{{ mainStock.price }}</span></span>
          <span><span class="l">止损</span><span class="v down num">¥{{ mainStock.stop }}</span></span>
          <span><span class="l">仓位</span><span class="v num" style="color:var(--gold)">{{ mainStock.pos }}%</span></span>
        </div>
        <div class="reasons" v-if="mainStock.reasons.length">
          <span v-for="r in mainStock.reasons.slice(0,2)">{{ r }}</span>
        </div>
      </div>
    </div>

    <!-- 无信号 -->
    <div v-else-if="!loading" class="card fade fade-2">
      <div class="card-header">今日缠论信号</div>
      <div class="state-box">
        <div class="msg">暂无符合条件的买点信号</div>
        <div class="sub">系统持续扫描中，有信号将立即显示</div>
      </div>
    </div>

    <!-- 次选 -->
    <div v-if="alts.length" class="card fade fade-3">
      <div class="card-header">备选标的</div>
      <div v-for="(s,i) in alts" :key="s.code" class="signal-card fade" style="border-bottom:1px solid var(--border);margin:0 -14px;padding:10px 14px">
        <div class="top" style="margin-bottom:4px">
          <span class="rank" style="font-size:12px">#{{i+2}}</span>
          <span class="name" style="font-size:14px">{{ s.name }}</span>
          <span class="code">{{ shortCode(s.code) }}</span>
          <span style="margin-left:auto;color:var(--gold);font-weight:600" class="num">{{ s.score }}</span>
        </div>
        <span class="bp" :class="'bp-' + bpLevel(s.buyPoint)" style="font-size:10px">{{ bpLabel(s.buyPoint) }}</span>
        <div v-if="s.reasons.length" class="reasons" style="margin-top:4px">
          <span v-for="r in s.reasons.slice(0,1)">{{ r }}</span>
        </div>
      </div>
    </div>

    <!-- loading -->
    <div v-if="loading" class="state-box"><div class="msg">加载中...</div></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api'

const loading = ref(true)
const marketChg = ref(0)
const hs300 = ref(null)
const statusText = ref('--')
const statusTag = ref('tag-blue')
const mainStock = ref<any>({})
const alts = ref<any[]>([])

function shortCode(c: string) { return (c || '').replace(/^[szsh]+/, '') }
function bpLevel(bp: string) { return { '1st_buy': '1', '2nd_buy': '2', '3rd_buy': '3' }[bp] || '0' }
function bpLabel(bp: string) { return { '1st_buy': '第一类买点', '2nd_buy': '第二类买点', '3rd_buy': '第三类买点' }[bp] || bp || '–' }

onMounted(async () => {
  try {
    const [mr, sr]: any = await Promise.all([
      api.get('/market/overview').catch(() => ({ data: {} })),
      api.get('/signals/today').catch(() => ({ data: {} })),
    ])
    const md = mr.data || {}
    const sd = sr.data || {}
    const idx = (md.indices || []).find((i: any) => i.code === 'sh000300')
    if (idx) {
      hs300.value = idx.current?.toLocaleString() || '--'
      marketChg.value = idx.changePct || 0
    }
    statusText.value = md.marketStatus || '震荡'
    const st = md.marketStatus || ''
    statusTag.value = st === '牛市' ? 'tag-green' : st === '熊市' ? 'tag-red' : 'tag-gold'

    const mp = sd.mainPick
    if (mp && mp.name) {
      mainStock.value = {
        name: mp.name, code: mp.code,
        score: mp.score || mp.chanScore || 0,
        price: mp.buyPrice || mp.price || 0,
        stop: mp.stopLoss || 0,
        pos: mp.positionRatio || 10,
        buyPoint: mp.buyPoint || '',
        reasons: Array.isArray(mp.reasons) ? mp.reasons : [],
      }
    }
    alts.value = (sd.alternatives || []).slice(0, 5).map((s: any) => ({
      name: s.name, code: s.code, score: s.score,
      buyPoint: s.buyPoint || '',
      reasons: Array.isArray(s.reasons) ? s.reasons : [],
      changePct: s.changePct || 0,
    }))
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.market-bar.down { border-color: var(--red-bg); }
</style>
