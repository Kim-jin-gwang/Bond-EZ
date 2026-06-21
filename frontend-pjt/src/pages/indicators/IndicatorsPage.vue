<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchIndicators } from '../../api/indicators'
import CreditRatingYieldSection from './sub/CreditRatingYield.vue'
import DepositCompareSection from './sub/DepositCompare.vue'
import GenericIndicatorSection from './sub/GenericIndicatorSection.vue'
import TreasuryRateSection from './sub/TreasuryRate.vue'
import YieldSpreadSection from './sub/YieldSpread.vue'

const indicators = ref([])

const props = defineProps({
  selectedIndicatorId: {
    type: String,
    default: 'treasury-rate',
  },
})

const emit = defineEmits(['navigate'])

const visibleIndicatorIds = ['treasury-rate', 'yield-spread', 'yield-curve', 'credit-rating-yield', 'deposit-compare']

const activeIndicator = computed(() =>
  indicators.value.find((indicator) => indicator.id === props.selectedIndicatorId) ?? indicators.value[0],
)

const visibleIndicators = computed(() =>
  visibleIndicatorIds
    .map((id) => indicators.value.find((indicator) => indicator.id === id))
    .filter(Boolean),
)

const centralBankIndicator = computed(() => indicators.value.find((indicator) => indicator.id === 'central-bank-rate'))
const treasuryIndicator = computed(() => indicators.value.find((indicator) => indicator.id === 'treasury-rate'))
const yieldSpreadIndicator = computed(() => indicators.value.find((indicator) => indicator.id === 'yield-spread'))

const sectionComponent = computed(() => {
  if (!activeIndicator.value) return null

  return {
    'treasury-rate': TreasuryRateSection,
    'yield-spread': YieldSpreadSection,
    'credit-rating-yield': CreditRatingYieldSection,
    'deposit-compare': DepositCompareSection,
  }[activeIndicator.value.id] || GenericIndicatorSection
})

function navigateToIndicator(indicatorId) {
  emit('navigate', 'indicators', indicatorId)
}

onMounted(async () => {
  indicators.value = await fetchIndicators()
})
</script>

<template>
  <section class="page indicators-detail-page">
    <div class="page-heading compact">
      <p class="eyebrow">Investment Indicators</p>
      <h1>투자 지표 상세 보기</h1>
      <p>금리와 채권 시장을 해석할 때 자주 확인하는 핵심 지표를 표와 그래프로 정리했습니다.</p>
    </div>

    <div class="indicator-nav" aria-label="투자 지표 선택">
      <button
        v-for="indicator in visibleIndicators"
        :key="indicator.id"
        :class="{ active: activeIndicator?.id === indicator.id }"
        type="button"
        @click="navigateToIndicator(indicator.id)"
      >
        {{ indicator.shortTitle || indicator.title }}
      </button>
    </div>

    <component
      :is="sectionComponent"
      v-if="activeIndicator && sectionComponent"
      :indicator="activeIndicator"
      :central-bank-indicator="centralBankIndicator"
      :treasury-indicator="treasuryIndicator"
      :yield-spread-indicator="yieldSpreadIndicator"
      @navigate-indicator="navigateToIndicator"
    />
  </section>
</template>

<style scoped>
.indicators-detail-page {
  display: grid;
  gap: 22px;
}

.indicator-nav {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.indicator-nav button {
  flex: 0 0 auto;
  min-height: 40px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 14px;
  color: var(--text);
  background: white;
  font-weight: 800;
}

.indicator-nav button.active {
  border-color: var(--primary);
  color: white;
  background: var(--primary);
}
</style>
