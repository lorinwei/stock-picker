<template>
  <div class="page picker-view">
    <div class="page-title fade-in fade-in-1">📊 AI选股池</div>
    <div class="picker-meta fade-in fade-in-1">
      <span>每日16:00更新</span>
      <span class="meta-count">{{ total }}只候选</span>
    </div>

    <!-- 筛选标签 -->
    <div class="filter-tags fade-in fade-in-1">
      <button
        v-for="cat in categories"
        :key="cat.value"
        class="filter-tag"
        :class="{ active: selectedCategory === cat.value }"
        @click="changeCategory(cat.value)"
      >{{ cat.label }}</button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>AI正在分析选股...</span>
    </div>

    <template v-else>
      <!-- 主推标的 -->
      <div class="section-title fade-in fade-in-2">🚀 主推标的</div>
      <div
        v-for="(s, i) in topStocks"
        :key="s.code"
        class="top-stock-card card card-glow fade-in"
        :class="'fade-in-' + (i + 3)"
      >
        <div class="tsc-header">
          <span class="tsc-rank">{{ i + 1 }}</span>
          <div class="tsc-name-group">
            <span class="tsc-name">{{ s.name }}</span>
            <span class="tsc-code">{{ s.code }}</span>
            <span class="tsc-industry">{{ s.industry }}</span>
            <span class="score-badge" :class="toScore(s.score) >= 55 ? 'gold' : ''">{{ toScore(s.score) }}</span>
          </div>
          <span class="tsc-change" :class="s.change >= 0 ? 'up' : 'down'">
            {{ s.change >= 0 ? '+' : '' }}{{ s.change }}%
          </span>
        </div>

        <div class="tsc-reason">
          <span class="reason-icon">🧠</span>
          <span>{{ s.reasons?.join(' · ') || 'AI综合评分推荐' }}</span>
        </div>

        <div class="tsc-price-info">
          <div class="pi-item">
            <span>买入区间</span>
            <span class="price">¥{{ s.buyRange || (s.price ? (s.price * 0.995).toFixed(2) + '~' + (s.price * 1.005).toFixed(2) : '—') }}</span>
          </div>
          <div class="pi-item">
            <span>目标价</span>
            <span class="price up">¥{{ s.target || '—' }}</span>
          </div>
          <div class="pi-item">
            <span>止损价</span>
            <span class="price down">¥{{ s.stopLoss || s.stop || '—' }}</span>
          </div>
          <div class="pi-item">
            <span>北向资金</span>
            <span class="price north">{{ s.north_money || s.flow?.netFlowRatio != null ? (s.flow.netFlowRatio > 0 ? '+' : '') + (s.flow.netFlowRatio ?? s.north_money) + '亿' : '—' }}</span>
          </div>
        </div>

        <div class="tsc-signals">
          <span v-for="sig in (s.signals || [])" :key="sig" class="tag" :class="sig === 'BUY' ? 'tag-green' : 'tag-blue'">{{ sig }}</span>
        </div>

        <button class="btn-primary" @click="handleFollow(s)">一键跟投</button>
      </div>

      <!-- 次选列表 -->
      <div class="section-title fade-in fade-in-4">📋 次选观察（{{ subStocks.length }}只）</div>
      <div class="stock-list">
        <div
          v-for="(s, i) in subStocks"
          :key="s.code"
          class="sub-stock-card card fade-in"
          :class="'fade-in-' + (i + 5)"
          @click="handleFollow(s)"
        >
          <div class="ssc-left">
            <div class="ssc-name">{{ s.name }} <span class="ssc-code">{{ s.code }}</span></div>
            <div class="ssc-reason">{{ s.reasons?.join(' · ') || '' }}</div>
            <div class="ssc-meta">
              <span>PE {{ s.pe }}</span>
              <span>ROE {{ s.roe }}%</span>
              <span class="north-tag">北向 +{{ s.north_money }}亿</span>
            </div>
          </div>
          <div class="ssc-right">
            <span class="score-badge" :class="(s.score?.total || s.score) >= 55 ? 'gold' : ''">{{ s.score?.total || s.score }}</span>
            <span class="ssc-change" :class="s.change >= 0 ? 'up' : 'down'">
              {{ s.change >= 0 ? '+' : '' }}{{ s.change }}%
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStockStore } from '@/stores/stock'

const router = useRouter()
const stockStore = useStockStore()

const selectedCategory = ref('all')
const loading = ref(false)

const categories = [
  { label: '全部', value: 'all' },
  { label: '成长股', value: 'growth' },
  { label: '价值股', value: 'value' },
  { label: '北向加仓', value: 'north' },
  { label: '热门', value: 'hot' },
]

const toScore = (s) => typeof s === 'number' ? s : (s?.total ?? 0);

const pool = computed(() => stockStore.stockPool)
const total = computed(() => pool.value?.total || 0)
const topStocks = computed(() => (pool.value?.items || []).filter((s: any) => toScore(s.score) >= 55).slice(0, 3))
const subStocks = computed(() => (pool.value?.items || []).filter((s: any) => toScore(s.score) < 55))

async function loadPool() {
  loading.value = true
  try {
    await stockStore.fetchStockPool(selectedCategory.value)
  } finally {
    loading.value = false
  }
}

function changeCategory(cat: string) {
  selectedCategory.value = cat
  loadPool()
}

const handleFollow = (stock: any) => {
  router.push({ name: 'portfolio' })
}

onMounted(() => {
  loadPool()
})
</script>

<style scoped>
.picker-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: -12px;
  margin-bottom: 12px;
}

.meta-count { color: var(--primary); font-weight: 600; }

.filter-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.filter-tag {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  border-radius: 20px;
  padding: 4px 14px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.filter-tag.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 0;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.top-stock-card { margin-bottom: 14px; padding: 16px; }

.tsc-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 12px;
}

.tsc-rank {
  font-size: 20px; font-weight: 800; color: var(--accent); min-width: 24px;
}

.tsc-name-group {
  flex: 1; display: flex; align-items: center; gap: 8px;
}

.tsc-name { font-size: 17px; font-weight: 700; }
.tsc-code { font-size: 12px; color: var(--text-secondary); font-variant-numeric: tabular-nums; }
.tsc-industry { font-size: 11px; color: var(--text-dim); background: var(--bg-elevated); padding: 2px 6px; border-radius: 4px; }

.score-badge {
  background: rgba(59, 130, 246, 0.15);
  color: var(--primary);
  font-size: 13px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
}
.score-badge.gold {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff;
}

.tsc-change { font-size: 15px; font-weight: 700; font-variant-numeric: tabular-nums; }

.tsc-reason {
  font-size: 13px; color: var(--text-primary);
  background: var(--bg-elevated); padding: 10px 12px;
  border-radius: 8px; margin-bottom: 12px; line-height: 1.5;
  display: flex; gap: 6px;
}
.reason-icon { flex-shrink: 0; }

.tsc-price-info { display: flex; gap: 16px; margin-bottom: 12px; flex-wrap: wrap; }

.pi-item { display: flex; flex-direction: column; gap: 2px; }
.pi-item span:first-child { font-size: 11px; color: var(--text-secondary); }
.pi-item .price { font-size: 14px; font-weight: 700; font-variant-numeric: tabular-nums; }
.pi-item .price.up { color: var(--success); }
.pi-item .price.down { color: var(--danger); }
.pi-item .price.north { color: var(--accent); }

.tsc-signals { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.tag { font-size: 11px; padding: 2px 8px; border-radius: 4px; }
.tag-green { background: rgba(16, 185, 129, 0.15); color: var(--success); }
.tag-blue { background: rgba(59, 130, 246, 0.15); color: var(--primary); }

.stock-list { display: flex; flex-direction: column; gap: 8px; }

.sub-stock-card {
  display: flex; align-items: center; gap: 10px; padding: 14px; cursor: pointer;
}

.ssc-left { flex: 1; }
.ssc-name { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
.ssc-code { font-size: 12px; color: var(--text-secondary); margin-left: 6px; font-variant-numeric: tabular-nums; }
.ssc-reason { font-size: 12px; color: var(--text-secondary); line-height: 1.4; margin-bottom: 4px; }
.ssc-meta { display: flex; gap: 8px; font-size: 11px; color: var(--text-dim); }
.north-tag { color: var(--accent); }

.ssc-right { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
.ssc-change { font-size: 13px; font-weight: 700; font-variant-numeric: tabular-nums; }
</style>
