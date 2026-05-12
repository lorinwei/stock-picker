<template>
  <div class="page market-view">
    <div class="page-title fade-in fade-in-1">📈 今日行情</div>
    <div class="update-time fade-in fade-in-1">更新时间：{{ updateTime }}</div>

    <!-- 大盘指数 -->
    <div class="section-title fade-in fade-in-2">大盘指数</div>
    <div class="index-grid fade-in fade-in-2">
      <div
        v-for="idx in indices"
        :key="idx.name"
        class="index-card card"
        :class="idx.change >= 0 ? 'index-up' : 'index-down'"
      >
        <div class="idx-name">{{ idx.name }}</div>
        <div class="idx-value price">{{ idx.value.toLocaleString() }}</div>
        <div class="idx-change" :class="idx.change >= 0 ? 'up' : 'down'">
          {{ idx.change >= 0 ? '↑' : '↓' }} {{ Math.abs(idx.change).toFixed(2) }}%
        </div>
      </div>
    </div>

    <!-- 热门板块 -->
    <div class="section-title fade-in fade-in-3">热门板块</div>
    <div class="sector-list fade-in fade-in-3">
      <div
        v-for="(s, i) in sectors"
        :key="s.name"
        class="sector-item card"
        :class="'fade-in-' + (i + 4)"
      >
        <span class="sector-rank">{{ i + 1 }}</span>
        <span class="sector-name">{{ s.name }}</span>
        <div class="sector-right">
          <span class="sector-change" :class="s.change >= 0 ? 'up' : 'down'">
            {{ s.change >= 0 ? '+' : '' }}{{ s.change.toFixed(1) }}%
          </span>
          <span class="sector-emoji">{{ s.emoji }}</span>
        </div>
      </div>
    </div>

    <!-- 强势股 -->
    <div class="section-title fade-in fade-in-4">今日强势股 TOP10</div>
    <div class="hot-list fade-in fade-in-4">
      <div
        v-for="(s, i) in hotStocks"
        :key="s.code"
        class="hot-item"
      >
        <span class="hot-rank" :class="{ top3: i < 3 }">{{ i + 1 }}</span>
        <div class="hot-info">
          <span class="hot-name">{{ s.name }}</span>
          <span class="hot-code">{{ s.code }}</span>
        </div>
        <div class="hot-right">
          <span class="hot-change up">{{ s.change >= 0 ? '+' : '' }}{{ s.change.toFixed(1) }}%</span>
          <span class="hot-strength">强度 {{ s.strength }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const now = new Date()
const updateTime = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })

const indices = ref([
  { name: '沪深300', value: 3820.5, change: 0.82 },
  { name: '创业板指', value: 1568.3, change: 1.15 },
  { name: '上证指数', value: 3148.2, change: 0.56 }
])

const sectors = ref([
  { name: '新能源汽车', change: 2.3, emoji: '🚗' },
  { name: '白酒', change: 1.8, emoji: '🍶' },
  { name: '半导体', change: 1.2, emoji: '💡' },
  { name: '医疗', change: 0.7, emoji: '🏥' },
  { name: '房地产', change: -0.8, emoji: '🏠' }
])

const hotStocks = ref([
  { rank: 1, name: '比亚迪', code: '002594', change: 4.2, strength: 95 },
  { rank: 2, name: '宁德时代', code: '300750', change: 3.8, strength: 92 },
  { rank: 3, name: '招商银行', code: '600036', change: 2.1, strength: 88 },
  { rank: 4, name: '五粮液', code: '000858', change: 1.9, strength: 85 },
  { rank: 5, name: '隆基绿能', code: '601012', change: 1.6, strength: 82 },
  { rank: 6, name: '美的集团', code: '000333', change: 1.4, strength: 79 },
  { rank: 7, name: '海康威视', code: '002415', change: 1.2, strength: 76 },
  { rank: 8, name: '中国平安', code: '601318', change: 0.9, strength: 73 },
  { rank: 9, name: '恒瑞医药', code: '600276', change: 0.7, strength: 70 },
  { rank: 10, name: '贵州茅台', code: '600519', change: 1.4, strength: 88 }
])
</script>

<style scoped>
.update-time {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: -12px;
  margin-bottom: 16px;
}

.index-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.index-card {
  text-align: center;
  padding: 14px 10px;
}

.index-up { border-left: 3px solid var(--success); }
.index-down { border-left: 3px solid var(--danger); }

.idx-name {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.idx-value {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 4px;
}

.idx-change {
  font-size: 13px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.sector-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.sector-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
}

.sector-rank {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-dim);
  min-width: 18px;
}

.sector-name {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
}

.sector-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sector-change {
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.sector-emoji {
  font-size: 16px;
}

.hot-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.hot-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}

.hot-rank {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-dim);
  min-width: 20px;
  text-align: center;
}

.hot-rank.top3 {
  color: var(--accent);
  font-size: 16px;
}

.hot-info {
  flex: 1;
}

.hot-name {
  font-size: 14px;
  font-weight: 600;
  display: block;
}

.hot-code {
  font-size: 11px;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.hot-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.hot-change {
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.hot-strength {
  font-size: 11px;
  color: var(--text-secondary);
}
</style>