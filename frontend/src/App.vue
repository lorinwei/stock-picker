<template>
  <div id="app">
    <div class="topbar">
      <span class="title">STOCKMIND</span>
      <span class="badge">缠论量化</span>
    </div>
    <router-view />
    <div class="bottombar">
      <router-link v-for="t in tabs" :key="t.path" :to="t.path" class="nav-item" :class="{ active: $route.path === t.path }">
        <span class="icon" v-html="t.icon"></span>
        <span>{{ t.label }}</span>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
const tabs = [
  { path: '/', label: '首页', icon: '&#9654;' },
  { path: '/picker', label: '选股', icon: '&#9776;' },
  { path: '/portfolio', label: '持仓', icon: '&#9632;' },
  { path: '/market', label: '行情', icon: '&#9650;' },
  { path: '/chat', label: '问股', icon: '&#8251;' },
]
</script>

<style>
@import './style.css';
</style>
