<script setup>
import { computed } from 'vue'
import { useTheme } from '../../composables/useTheme'
import { useAppStore } from '../../stores/app'


defineProps({
  activePage: {
    type: String,
    required: true,
  },
})

defineEmits(['navigate'])

const appStore = useAppStore()
const { isDark, toggleTheme } = useTheme()

const navItems = computed(() => [
  { id: 'market', label: '채권 시세' },
  { id: 'indicators', label: '투자 지표' },
  { id: 'news', label: '금리 뉴스' },
  { id: 'dictionary', label: '용어 사전' },
  { id: 'guide', label: '채권 가이드' },
  { id: 'profile', label: appStore.isLoggedIn ? '내정보' : '로그인' },
])

</script>

<template>
  <header class="gnb">
    <button class="brand" type="button" aria-label="홈으로 이동" @click="$emit('navigate', 'home')">
      <span class="brand-mark">B</span>
      <span>BondEZ</span>
    </button>

    <div class="nav-actions">
      <nav class="nav-links" aria-label="Global Navigation Bar">
        <button
          v-for="item in navItems"
          :key="item.id"
          class="nav-link"
          :class="{ active: activePage === item.id }"
          type="button"
          @click="$emit('navigate', item.id)"
        >
          {{ item.label }}
        </button>
      </nav>
      <button
        class="theme-toggle"
        type="button"
        :aria-label="isDark ? '라이트 모드로 전환' : '다크 모드로 전환'"
        :title="isDark ? '라이트 모드' : '다크 모드'"
        @click="toggleTheme"
      >
        <span aria-hidden="true">{{ isDark ? '☀' : '☾' }}</span>
      </button>
    </div>
  </header>
</template>
