import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export interface AppSettings {
  theme: 'dark' | 'light'
  defaultIndicators: string[]
  autoRefresh: boolean
  refreshInterval: number // seconds
  signalThreshold: number
  language: 'zh-CN' | 'en-US'
}

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<AppSettings>({
    theme: 'dark',
    defaultIndicators: ['MA', 'MACD', 'RSI'],
    autoRefresh: true,
    refreshInterval: 60,
    signalThreshold: 70,
    language: 'zh-CN'
  })

  function updateSettings(newSettings: Partial<AppSettings>) {
    settings.value = { ...settings.value, ...newSettings }
    localStorage.setItem('stockmind-settings', JSON.stringify(settings.value))
  }

  function loadSettings() {
    const saved = localStorage.getItem('stockmind-settings')
    if (saved) {
      try {
        settings.value = { ...settings.value, ...JSON.parse(saved) }
      } catch (e) {
        console.error('Failed to load settings:', e)
      }
    }
  }

  // Auto-save on change
  watch(settings, (val) => {
    localStorage.setItem('stockmind-settings', JSON.stringify(val))
  }, { deep: true })

  return {
    settings,
    updateSettings,
    loadSettings
  }
})
