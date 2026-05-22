<script setup>
import { computed } from 'vue'
import { indicators } from '../../data/indicators'
import TreasuryRate from './sub/TreasuryRate.vue'
import CreditRatingYield from './sub/CreditRatingYield.vue'
import YieldSpread from './sub/YieldSpread.vue'
import DepositCompare from './sub/DepositCompare.vue'

const props = defineProps({
  selectedIndicatorId: {
    type: String,
    default: 'treasury-rate',
  },
})

const emit = defineEmits(['navigate'])

const subPages = {
  'treasury-rate': TreasuryRate,
  'credit-rating-yield': CreditRatingYield,
  'yield-spread': YieldSpread,
  'deposit-compare': DepositCompare,
}

const activeIndicator = computed(() => {
  return indicators.find((indicator) => indicator.id === props.selectedIndicatorId) ?? indicators[0]
})
</script>

<template>
  <section class="page">
    <div class="tab-group indicator-tabs">
      <button
        v-for="indicator in indicators"
        :key="indicator.id"
        :class="{ active: activeIndicator.id === indicator.id }"
        type="button"
        @click="$emit('navigate', 'indicators', indicator.id)"
      >
        {{ indicator.title }}
      </button>
    </div>

    <component :is="subPages[activeIndicator.id]" />
  </section>
</template>
