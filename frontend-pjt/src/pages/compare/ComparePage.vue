<script setup>
import { computed } from 'vue'
import { bonds } from '../../data/bonds'

const props = defineProps({
  compareBonds: {
    type: Array,
    default: () => [],
  },
})

const displayedBonds = computed(() => {
  if (props.compareBonds.length === 2) {
    return props.compareBonds
  }

  return bonds.slice(0, 2)
})

const leftBond = computed(() => displayedBonds.value[0])
const rightBond = computed(() => displayedBonds.value[1])

const compareRows = computed(() => [
  ['채권 유형', leftBond.value.type, rightBond.value.type],
  ['매수수익률(YTM)', leftBond.value.buyYield, rightBond.value.buyYield],
  ['매도수익률', leftBond.value.sellYield, rightBond.value.sellYield],
  ['만기', leftBond.value.maturity, rightBond.value.maturity],
  ['잔존만기', `${leftBond.value.maturityYears}년`, `${rightBond.value.maturityYears}년`],
  ['신용등급', leftBond.value.rating, rightBond.value.rating],
  ['표면금리', leftBond.value.coupon, rightBond.value.coupon],
  ['듀레이션', leftBond.value.duration, rightBond.value.duration],
  ['이자 지급 주기', leftBond.value.interestCycle, rightBond.value.interestCycle],
  ['현재가', leftBond.value.price, rightBond.value.price],
  ['등락률', leftBond.value.change, rightBond.value.change],
  ['옵션', leftBond.value.option, rightBond.value.option],
  ['시장구분', leftBond.value.marketType, rightBond.value.marketType],
])

function isBetter(row) {
  if (row[0].includes('수익률') || row[0] === '표면금리') {
    return Number.parseFloat(row[1]) > Number.parseFloat(row[2]) ? 'left' : 'right'
  }

  if (row[0] === '잔존만기' || row[0] === '듀레이션') {
    return Number.parseFloat(row[1]) < Number.parseFloat(row[2]) ? 'left' : 'right'
  }

  return null
}
</script>

<template>
  <section class="page compare-page">
    <div class="page-heading compact">
      <p class="eyebrow">채권 비교</p>
      <h1>{{ leftBond.name }} vs {{ rightBond.name }}</h1>
      <p>선택한 두 채권의 수익률, 만기, 위험 지표를 나란히 비교합니다.</p>
    </div>

    <section class="compare-summary-grid">
      <article v-for="bond in displayedBonds" :key="bond.code" class="compare-summary-card">
        <span>{{ bond.code }}</span>
        <h2>{{ bond.name }}</h2>
        <div>
          <strong>{{ bond.buyYield }}</strong>
          <small>매수수익률</small>
        </div>
      </article>
    </section>

    <div class="compare-table professional-compare">
      <div class="compare-row header">
        <span>항목</span>
        <strong>{{ leftBond.name }}</strong>
        <strong>{{ rightBond.name }}</strong>
      </div>
      <div v-for="row in compareRows" :key="row[0]" class="compare-row">
        <span>{{ row[0] }}</span>
        <strong :class="{ better: isBetter(row) === 'left' }">{{ row[1] }}</strong>
        <strong :class="{ better: isBetter(row) === 'right' }">{{ row[2] }}</strong>
      </div>
    </div>
  </section>
</template>

<style scoped>
.compare-page {
  display: grid;
  gap: 20px;
}

.compare-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.compare-summary-card {
  display: grid;
  gap: 12px;
  padding: 22px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
  box-shadow: var(--shadow);
}

.compare-summary-card span,
.compare-summary-card small {
  color: var(--muted);
  font-size: 13px;
}

.compare-summary-card h2 {
  margin-bottom: 0;
  font-size: 20px;
}

.compare-summary-card div {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 12px;
}

.compare-summary-card strong {
  color: var(--primary);
  font-size: 30px;
}

.professional-compare {
  overflow: hidden;
}

.professional-compare .compare-row {
  grid-template-columns: 0.7fr 1fr 1fr;
}

@media (max-width: 760px) {
  .compare-summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
