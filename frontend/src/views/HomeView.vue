<template>
  <div class="page home-view">
    <!-- 顶部大盘温度计 -->
    <div class="market-temp fade-in fade-in-1" :class="marketUp ? 'market-up' : 'market-down'">
      <div class="temp-left">
        <span class="temp-label">大盘</span>
        <span class="temp-name">沪深300</span>
      </div>
      <div class="temp-right">
        <span class="temp-index">{{ hs300.current ? hs300.current.toLocaleString() : '—' }}</span>
        <span class="temp-change" :class="hs300.change > 0 ? 'up' : 'down'">
          {{ hs300.change > 0 ? '↑' : '↓' }}
          {{ Math.abs(hs300.change || 0).toFixed(2) }}%
        </span>
      </div>
    </div>

    <!-- AI推荐卡片 -->
    <div class="ai-signal-card card card-glow fade-in fade-in-2">
      <div class="signal-header">
        <span class="signal-icon">🚀</span>
        <span class="signal-title">今日AI推荐</span>
        <span class="signal-time">{{ today }}</span>
      </div>

      <div class="signal-stock">
        <div class="stock-main">
          <div class="stock-name-row">
            <span class="stock-name">{{ mainSignal.name }}</span>
            <span class="stock-code">{{ mainSignal.code }}</span>
            <span class="score-badge">{{ mainSignal.score }}</span>
          </div>
          <div class="stock-price-row">
            <span class="price-label">买入价</span>
            <span class="price-val">¥{{ mainSignal.price }}</span>
            <span class="price-label">目标价</span>
            <span class="price-val up">¥{{ mainSignal.target }}</span>
            <span class="price-label">止损</span>
            <span class="price-val down">¥{{ mainSignal.stop }}</span>
          </div>
          <div class="stock-position">
            <span class="pos-label">建议仓位</span>
            <span class="pos-val">{{ mainSignal.position }}%</span>
          </div>
        </div>
      </div>

      <div class="ai-reason">
        <div class="reason-label">
          <span>🧠</span>
          <span>AI理由</span>
        </div>
        <p class="reason-text">{{ mainSignal.reason }}</p>
      </div>

      <button class="btn-primary" @click="handleFollow(mainSignal)">
        一键跟投
      </button>

      <div class="signal-stats">
        <span class="stat-item">✅ 历史胜率 {{ mainSignal.winRate }}%</span>
        <span class="stat-item">👥 {{ (mainSignal.followers || 0).toLocaleString() }}人跟投</span>
      </div>
    </div>

    <!-- 次选标的 -->
    <div class="section-title fade-in fade-in-3">📊 次选标的</div>
    <div class="stock-list">
      <div
        v-for="(stock, i) in subSignals"
        :key="stock.code"
        class="stock-sub-card card fade-in"
        :class="'fade-in-' + (i + 4)"
        @click="handleFollow(stock)"
      >
        <div class="sub-rank">{{ i + 2 }}</div>
        <div class="sub-info">
          <div class="sub-name">{{ stock.name }} <span class="sub-code">{{ stock.code }}</span></div>
          <div class="sub-reason">{{ stock.reason }}</div>
        </div>
        <div class="sub-score">
          <span class="score-badge">{{ stock.score }}</span>
          <span class="sub-change" :class="stock.change > 0 ? 'up' : 'down'">
            {{ stock.change > 0 ? '+' : '' }}{{ stock.change }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStockStore } from '@/stores/stock'

const router = useRouter()
const stockStore = useStockStore()

const today = new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })

// 大盘数据（太子院）
const hs300 = computed(() => {
  const overview = stockStore.marketOverview || {}
  const indices = overview.indices || []
  return indices.find((i: any) => i.code === 'sh000300') || { current: null, change: 0, changePct: 0 }
})
const marketUp = computed(() => hs300.value.changePct >= 0)

// AI信号（尚书省 + 中书省）
const mainPick = computed(() => stockStore.todaySignals?.mainPick || null)
const alternatives = computed(() => stockStore.todaySignals?.alternatives || [])
const stats = computed(() => stockStore.todaySignals?.stats || { winRate: 0, followerCount: 0 })

// 适配器：API字段 → 模板字段
const mainSignal = computed(() => {
  const pick = mainPick.value
  if (!pick) return {}
  return {
    name: pick.name || '—',
    code: pick.code || '—',
    score: pick.score ?? 0,
    price: pick.buyPrice ?? pick.price ?? 0,
    target: pick.targetPrice ?? 0,
    stop: pick.stopLoss ?? 0,
    position: pick.positionRatio ?? 10,
    reason: Array.isArray(pick.reasons) ? pick.reasons.join(' · ') : (pick.reasons || ''),
    winRate: stats.value?.winRate ?? 0,
    followers: stats.value?.followerCount ?? 0,
  }
})

const subSignals = computed(() => {
  return alternatives.value.map((s: any) => ({
    name: s.name || '—',
    code: s.code || '—',
    score: s.score ?? 0,
    reason: Array.isArray(s.reasons) ? s.reasons.join(' · ') : (s.reasons || ''),
    change: s.change ?? 0,
    price: s.price ?? 0,
    target: s.target ?? 0,
    stop: s.stop ?? 0,
    buyRange: s.buyRange || '',
  }))
})

const handleFollow = (stock: any) => {
  router.push({ name: 'portfolio' })
}

onMounted(async () => {
  await Promise.all([
    stockStore.fetchMarketOverview(),
    stockStore.fetchTodaySignals()
  ])
})
</script>

<style scoped>
.market-temp {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 16px;
  font-size: 14px;
}

.market-up {
  background: var(--success-bg);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.market-down {
  background: var(--danger-bg);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.temp-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.temp-label {
  color: var(--text-secondary);
}

.temp-name {
  color: var(--text-primary);
  font-weight: 600;
}

.temp-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.temp-index {
  font-size: 16px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.temp-change {
  font-size: 14px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.signal-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.signal-icon {
  font-size: 20px;
}

.signal-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.signal-time {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: auto;
}

.stock-main {
  margin-bottom: 14px;
}

.stock-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.stock-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.stock-code {
  font-size: 12px;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.stock-price-row {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.price-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.price-val {
  font-size: 15px;
  font-weight: 700;
  margin-right: 10px;
  font-variant-numeric: tabular-nums;
}

.stock-position {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pos-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.pos-val {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary);
  background: rgba(59, 130, 246, 0.1);
  padding: 2px 8px;
  border-radius: 6px;
}

.ai-reason {
  background: var(--bg-elevated);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 14px;
}

.reason-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.reason-text {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.6;
}

.signal-stats {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 12px;
}

.stat-item {
  font-size: 12px;
  color: var(--text-secondary);
}

.stock-sub-card {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 14px;
}

.sub-rank {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-dim);
  min-width: 24px;
}

.sub-info {
  flex: 1;
}

.sub-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.sub-code {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: 6px;
  font-variant-numeric: tabular-nums;
}

.sub-reason {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.sub-score {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.sub-change {
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
</style>