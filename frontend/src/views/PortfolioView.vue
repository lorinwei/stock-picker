<template>
  <div class="page portfolio-view">
    <div class="page-title fade-in fade-in-1">💼 我的持仓</div>

    <!-- 资产总览 -->
    <div class="asset-overview card card-glow fade-in fade-in-1">
      <div class="asset-left">
        <div class="asset-label">总资产</div>
        <div class="asset-value price">¥{{ totalAsset.toLocaleString() }}</div>
      </div>
      <div class="asset-right">
        <div class="asset-label">今日收益</div>
        <div class="asset-profit price" :class="todayProfit >= 0 ? 'up' : 'down'">
          {{ todayProfit >= 0 ? '+' : '' }}¥{{ todayProfit.toLocaleString() }}
        </div>
      </div>
    </div>

    <!-- 持仓列表 -->
    <div class="positions">
      <div
        v-for="(p, i) in positions"
        :key="p.code"
        class="position-card card fade-in"
        :class="'fade-in-' + (i + 2)"
      >
        <div class="pos-header">
          <div class="pos-name-row">
            <span class="pos-name">{{ p.name }}</span>
            <span class="pos-code price">{{ p.code }}</span>
          </div>
          <span class="status-tag" :class="p.statusClass">{{ p.statusLabel }}</span>
        </div>

        <div class="pos-price-row">
          <div class="price-item">
            <span class="p-label">买入价</span>
            <span class="p-val price">¥{{ p.buyPrice }}</span>
          </div>
          <div class="price-item">
            <span class="p-label">当前价</span>
            <span class="p-val price" :class="p.change >= 0 ? 'up' : 'down'">¥{{ p.currentPrice }}</span>
          </div>
          <div class="price-item">
            <span class="p-label">浮盈亏</span>
            <span class="p-val price" :class="p.profit >= 0 ? 'up' : 'down'">
              {{ p.profit >= 0 ? '+' : '' }}¥{{ p.profit.toLocaleString() }}
            </span>
          </div>
        </div>

        <div class="pos-meta">
          <span>持仓：{{ p.shares }}股</span>
          <span>持仓：{{ p.days }}天</span>
          <span>止损价：¥{{ p.stopPrice }}</span>
        </div>

        <!-- AI建议（如果有） -->
        <div v-if="p.aiAdvice" class="ai-advice" :class="p.statusClass">
          <span>⚠️ AI建议：</span>{{ p.aiAdvice }}
        </div>

        <div class="pos-actions">
          <button class="btn-secondary">查看详情</button>
          <button class="btn-secondary" :class="{ 'sell-btn': p.profit > 0 }">卖出</button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="positions.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <div class="empty-title">暂无持仓</div>
      <div class="empty-desc">去首页看看AI推荐，一键跟投开始赚钱</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const totalAsset = ref(102350)
const todayProfit = ref(1230)

const positions = ref([
  {
    name: '比亚迪', code: '002594',
    buyPrice: '238.5', currentPrice: '245.3',
    profit: 1360, profitRate: 2.85,
    change: 0.0285,
    shares: 200, days: 12,
    stopPrice: '219.4',
    statusLabel: '🟢 正常', statusClass: 'status-ok',
    aiAdvice: ''
  },
  {
    name: '宁德时代', code: '300750',
    buyPrice: '198.0', currentPrice: '185.3',
    profit: -3810, profitRate: -6.41,
    change: -0.0641,
    shares: 300, days: 8,
    stopPrice: '182.2',
    statusLabel: '🟡 接近止损', statusClass: 'status-warn',
    aiAdvice: '考虑减仓至50%，等待反弹确认'
  },
  {
    name: '贵州茅台', code: '600519',
    buyPrice: '1800.0', currentPrice: '1850.0',
    profit: 5000, profitRate: 1.39,
    change: 0.0139,
    shares: 100, days: 5,
    stopPrice: '1710.0',
    statusLabel: '🟢 正常', statusClass: 'status-ok',
    aiAdvice: ''
  }
])
</script>

<style scoped>
.asset-overview {
  display: flex;
  justify-content: space-between;
  padding: 20px;
  margin-bottom: 20px;
}

.asset-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.asset-value {
  font-size: 24px;
  font-weight: 800;
}

.asset-profit {
  font-size: 18px;
  font-weight: 700;
}

.positions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.position-card {
  padding: 16px;
}

.pos-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.pos-name {
  font-size: 17px;
  font-weight: 700;
}

.pos-code {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: 6px;
}

.status-tag {
  font-size: 12px;
  font-weight: 600;
}

.status-ok { color: var(--success); }
.status-warn { color: var(--accent); }
.status-danger { color: var(--danger); }

.pos-price-row {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
}

.price-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.p-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.p-val {
  font-size: 14px;
  font-weight: 700;
}

.pos-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.ai-advice {
  font-size: 13px;
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 12px;
  line-height: 1.5;
}

.ai-advice.status-ok {
  background: var(--success-bg);
  color: var(--success);
}

.ai-advice.status-warn {
  background: rgba(245, 158, 11, 0.1);
  color: var(--accent);
}

.ai-advice.status-danger {
  background: var(--danger-bg);
  color: var(--danger);
}

.pos-actions {
  display: flex;
  gap: 10px;
}

.pos-actions .btn-secondary {
  flex: 1;
}

.sell-btn {
  color: var(--danger);
  border-color: rgba(239, 68, 68, 0.3);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-secondary);
}
</style>