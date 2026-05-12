import { defineConfig, presetUno, presetAttributify, presetIcons } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify(),
    presetIcons({
      scale: 1.2,
      extraProperties: {
        'display': 'inline-block',
        'vertical-align': 'middle',
      },
    }),
  ],
  theme: {
    colors: {
      primary: '#18a058',
      danger: '#d03050',
      dark: {
        bg: '#0d1117',
        card: '#161b22',
        border: '#30363d',
        text: '#c9d1d9',
        muted: '#8b949e',
      },
      accent: {
        cyan: '#00d4ff',
        green: '#00ff88',
        red: '#ff4757',
        yellow: '#ffd93d',
      }
    }
  },
  shortcuts: {
    'card-base': 'bg-dark-card border border-dark-border rounded-lg p-4',
    'text-gradient': 'bg-gradient-to-r from-accent-cyan to-accent-green bg-clip-text text-transparent',
    'btn-primary': 'bg-primary hover:bg-primary/80 text-white px-4 py-2 rounded transition',
    'signal-buy': 'text-accent-green bg-accent-green/10 border border-accent-green/30 px-2 py-0.5 rounded text-xs',
    'signal-sell': 'text-accent-red bg-accent-red/10 border border-accent-red/30 px-2 py-0.5 rounded text-xs',
  }
})
