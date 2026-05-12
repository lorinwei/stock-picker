import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '今日信号' }
  },
  {
    path: '/picker',
    name: 'picker',
    component: () => import('@/views/PickerView.vue'),
    meta: { title: 'AI选股池' }
  },
  {
    path: '/portfolio',
    name: 'portfolio',
    component: () => import('@/views/PortfolioView.vue'),
    meta: { title: '我的持仓' }
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { title: 'AI问答' }
  },
  {
    path: '/market',
    name: 'market',
    component: () => import('@/views/MarketView.vue'),
    meta: { title: '今日行情' }
  },
  {
    path: '/backtest',
    name: 'backtest',
    component: () => import('@/views/Backtest.vue'),
    meta: { title: '策略回测' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || 'StockMind'} - StockMind`
  next()
})

export default router