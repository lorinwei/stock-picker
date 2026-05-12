<template>
  <div class="bottom-nav">
    <router-link
      v-for="tab in tabs"
      :key="tab.name"
      :to="tab.path"
      class="nav-item"
      :class="{ active: $route.path === tab.path }"
    >
      <span class="nav-icon">{{ tab.icon }}</span>
      <span class="nav-label">{{ tab.label }}</span>
    </router-link>
  </div>
</template>

<script setup lang="ts">
const tabs = [
  { name: 'home', path: '/', label: '首页', icon: '🏠' },
  { name: 'picker', path: '/picker', label: '选股', icon: '📊' },
  { name: 'backtest', path: '/backtest', label: '回测', icon: '📉' },
  { name: 'portfolio', path: '/portfolio', label: '持仓', icon: '💼' },
  { name: 'chat', path: '/chat', label: 'AI', icon: '💬' },
  { name: 'market', path: '/market', label: '行情', icon: '📈' }
]
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 70px;
  background: rgba(11, 14, 26, 0.9);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: stretch;
  z-index: 100;
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  text-decoration: none;
  color: var(--text-secondary);
  transition: all 0.2s ease;
  position: relative;
}

.nav-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 2px;
  background: var(--primary);
  border-radius: 0 0 2px 2px;
  transition: width 0.2s ease;
}

.nav-item.active {
  color: var(--primary);
}

.nav-item.active::before {
  width: 28px;
  box-shadow: 0 0 8px var(--primary-glow);
}

.nav-icon {
  font-size: 22px;
  transition: transform 0.2s ease;
  filter: drop-shadow(0 0 0px transparent);
}

.nav-item.active .nav-icon {
  transform: scale(1.1);
  filter: drop-shadow(0 0 6px var(--primary-glow));
}

.nav-label {
  font-size: 11px;
  font-weight: 500;
}
</style>