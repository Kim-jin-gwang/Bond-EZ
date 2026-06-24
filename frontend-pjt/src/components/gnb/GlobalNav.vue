<script setup>
defineProps({
  activePage: {
    type: String,
    required: true,
  },
})

defineEmits(['navigate'])

const navItems = [
  { id: 'market', label: '채권 시세' },
  { id: 'indicators', label: '투자 지표' },
  { id: 'news', label: '금리 뉴스' },
  { id: 'dictionary', label: '용어 사전' },
  { id: 'guide', label: '채권 가이드' },
  { id: 'profile', label: '내정보' },
]
</script>

<template>
  <header class="gnb">
    <button class="brand" type="button" aria-label="홈으로 이동" @click="$emit('navigate', 'home')">
      <span class="brand-mark">B</span>
      <span>BondEZ</span>
    </button>

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
  </header>
</template>
