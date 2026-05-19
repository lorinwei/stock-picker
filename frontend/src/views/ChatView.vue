<template>
  <div class="page">
    <div class="card fade fade-1">
      <div class="card-header">智能问答</div>
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px">
        <span v-for="q in quick" :key="q" class="tag tag-blue" style="cursor:pointer;padding:4px 10px;font-size:12px" @click="ask(q)">{{ q }}</span>
      </div>
      <div ref="box" style="max-height:360px;overflow-y:auto;display:flex;flex-direction:column;gap:10px;margin-bottom:10px">
        <div v-for="(m,i) in msgs" :key="i" style="padding:10px 12px;border-radius:var(--radius2);font-size:13px;line-height:1.7;white-space:pre-wrap" :class="m.role === 'user' ? '' : 'bg'">
          <div style="font-size:11px;color:var(--text3);margin-bottom:4px">{{ m.role === 'user' ? '我' : 'StockMind' }}</div>
          {{ m.content }}
        </div>
        <div v-if="thinking" style="padding:10px 12px;border-radius:var(--radius2);font-size:13px;color:var(--text3)"><div style="font-size:11px;color:var(--text3);margin-bottom:4px">StockMind</div>分析中...</div>
      </div>
      <div style="display:flex;gap:8px">
        <input v-model="input" class="input" placeholder="输入股票代码或问题" @keyup.enter="ask(input)" style="flex:1;padding:8px 12px;border-radius:var(--radius2);border:1px solid var(--border);background:var(--bg2);color:var(--text);font-size:13px;outline:none">
        <button class="btn btn-primary btn-sm" @click="ask(input)">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import api from '@/api'

const input = ref('')
const msgs = ref<{role:string;content:string}[]>([])
const thinking = ref(false)
const box = ref<HTMLElement|null>(null)
const quick = ['诊断持仓', '市场概况', '缠论买点']

async function ask(q: string) {
  if (!q.trim()) return
  const text = q.trim()
  input.value = ''
  msgs.value.push({ role: 'user', content: text })
  thinking.value = true

  try {
    let reply = ''
    if (text.includes('诊断') || text.includes('持仓')) {
      const r: any = await api.get('/portfolio').catch(() => ({ data: { positions: [] } }))
      const pos = r.data?.positions || []
      reply = pos.length ? pos.map((p: any) => `${p.name}(${shortCode(p.code)}) 盈亏${p.profit_pct || 0}%`).join('\n') : '暂无持仓'
    } else if (text.includes('市场')) {
      const r: any = await api.get('/market/overview').catch(() => ({ data: {} }))
      const idx = r.data?.indices || []
      reply = idx.map((i: any) => `${i.name}: ${i.current} (${i.changePct >= 0 ? '+' : ''}${i.changePct}%)`).join('\n') || '暂无数据'
    } else if (text.includes('缠论') || text.includes('买点') || text.includes('选股')) {
      const r: any = await api.get('/picker/signals').catch(() => ({ data: { signals: [] } }))
      const sigs = r.data?.signals || []
      reply = sigs.length ? sigs.slice(0,5).map((s: any) => `#${s.rank} ${s.name}(${shortCode(s.code)}) 评分${s.score}`).join('\n') : '暂无缠论买点信号'
    } else if (/^\d{6}$/.test(text) || text.startsWith('sh') || text.startsWith('sz')) {
      const r: any = await api.get(`/stock/${text.replace(/[shsz]/g, '')}`).catch(() => ({ data: {} }))
      const d = r.data || {}
      reply = d.name ? `${d.name}\n现价: ¥${d.price}\nPE: ${d.pe || '--'} | ROE: ${d.roe || '--'}%` : '未找到该股票'
    } else {
      reply = '请尝试: 股票代码、诊断持仓、市场概况、缠论买点'
    }
    msgs.value.push({ role: 'assistant', content: reply })
  } catch { msgs.value.push({ role: 'assistant', content: '服务暂不可用' }) }

  thinking.value = false
  nextTick(() => box.value?.scrollTo({ top: box.value.scrollHeight, behavior: 'smooth' }))
}

function shortCode(c: string) { return (c || '').replace(/^[szsh]+/, '') }
</script>

<style scoped>
.bg { background: var(--surface2); }
.input:focus { border-color: var(--blue); }
</style>
