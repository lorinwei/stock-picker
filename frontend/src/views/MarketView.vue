<template>
  <div class="page">
    <div v-if="loading" class="state-box"><div class="msg">加载中...</div></div>

    <div v-else class="card fade fade-1">
      <div class="card-header">主要指数</div>
      <div v-for="idx in indices" :key="idx.code" class="idx-row">
        <span class="name">{{ idx.name }}</span>
        <span class="val num">{{ idx.current?.toLocaleString() || '--' }}</span>
        <span class="chg" :class="(idx.changePct || 0) >= 0 ? 'up' : 'down'">
          {{ (idx.changePct || 0) >= 0 ? '+' : '' }}{{ (idx.changePct || 0).toFixed(2) }}%
        </span>
      </div>
    </div>

    <div class="card fade fade-2" style="margin-top:10px">
      <div class="card-header">行业涨跌榜</div>
      <div v-if="industries.length === 0" style="font-size:13px;color:var(--text3);padding:8px 0">数据加载中</div>
      <div v-for="ind in industries" :key="ind.板块名称" class="idx-row">
        <span class="name">{{ ind.板块名称 }}</span>
        <span class="chg" :class="(ind.涨跌幅 || 0) >= 0 ? 'up' : 'down'">
          {{ (ind.涨跌幅 || 0) >= 0 ? '+' : '' }}{{ (ind.涨跌幅 || 0).toFixed(2) }}%
        </span>
      </div>
    </div>

    <div class="card fade fade-3" style="margin-top:10px">
      <div class="card-header">市场状态</div>
      <div style="display:flex;gap:16px">
        <div><span style="color:var(--text3);font-size:12px">判断</span><br><span class="tag" :class="statusTag" style="margin-top:4px;font-size:13px">{{ statusText }}</span></div>
        <div><span style="color:var(--text3);font-size:12px">建议仓位</span><br><span style="font-size:18px;font-weight:700" class="num">≤ {{ posLimit }}%</span></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api'

const loading = ref(true)
const indices = ref<any[]>([])
const industries = ref<any[]>([])
const statusText = ref('--')
const statusTag = ref('tag-gold')
const posLimit = ref(40)

onMounted(async () => {
  try {
    const res: any = await api.get('/market/overview')
    const d = res.data || {}
    indices.value = d.indices || []
    industries.value = d.industries?.leaders || []
    statusText.value = d.marketStatus || '--'
    const st = d.marketStatus || ''
    statusTag.value = st === '牛市' ? 'tag-green' : st === '熊市' ? 'tag-red' : 'tag-gold'
    posLimit.value = d.positionLimit ? Math.round(d.positionLimit * 100) : 40
  } catch {}
  loading.value = false
})
</script>
