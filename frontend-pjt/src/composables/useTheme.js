import { computed, ref } from 'vue'

const STORAGE_KEY = 'bondez-theme'
const theme = ref('light')
let initialized = false

export function initializeTheme() {
  if (initialized || typeof window === 'undefined') return

  const storedTheme = window.localStorage.getItem(STORAGE_KEY)
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  theme.value = storedTheme === 'dark' || storedTheme === 'light'
    ? storedTheme
    : systemPrefersDark ? 'dark' : 'light'
  applyTheme(theme.value)
  initialized = true
}

export function useTheme() {
  initializeTheme()

  const isDark = computed(() => theme.value === 'dark')

  function toggleTheme() {
    theme.value = isDark.value ? 'light' : 'dark'
    window.localStorage.setItem(STORAGE_KEY, theme.value)
    applyTheme(theme.value)
  }

  return { theme, isDark, toggleTheme }
}

function applyTheme(value) {
  document.documentElement.dataset.theme = value
  document.documentElement.style.colorScheme = value
}
