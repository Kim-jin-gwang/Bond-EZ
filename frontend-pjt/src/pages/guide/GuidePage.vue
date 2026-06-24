<script setup>
import WhatIsBond from './sub/WhatIsBond.vue'
import InvestmentRisk from './sub/InvestmentRisk.vue'
import InvestmentGuide from './sub/InvestmentGuide.vue'

const props = defineProps({
  currentSubPage: {
    type: String,
    default: 'what',
  },
})

const emit = defineEmits(['navigate'])

const tabs = [
  { id: 'what', label: '채권이란', component: WhatIsBond },
  { id: 'risk', label: '투자 위험', component: InvestmentRisk },
  { id: 'guide', label: '투자가이드', component: InvestmentGuide },
]

const subPages = {
  what: WhatIsBond,
  risk: InvestmentRisk,
  guide: InvestmentGuide,
}
</script>

<template>
  <section class="page content-page">
    <div class="tab-group guide-tabs" role="tablist">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="{ active: currentSubPage === tab.id }"
        type="button"
        role="tab"
        :aria-selected="currentSubPage === tab.id"
        @click="$emit('navigate', 'guide', tab.id)"
      >
        {{ tab.label }}
      </button>
    </div>

    <component :is="subPages[currentSubPage || 'what']" />
  </section>
</template>


<style scoped>
.description-content {
  margin-top: 24px;
  line-height: 1.8;
  color: var(--text);
}
.description-content p {
  margin-bottom: 12px;
}
</style>
