<script setup>
import { computed } from 'vue'
import { barHeight, formatRate, getCountryTone, parseRate } from './indicatorUtils'

const props = defineProps({
  treasuryIndicator: {
    type: Object,
    default: null,
  },
  centralBankIndicator: {
    type: Object,
    default: null,
  },
  yieldSpreadIndicator: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['navigate-indicator'])

const rateRows = computed(() => {
  const treasuryRows = props.treasuryIndicator?.treasuryRates || []
  const centralRows = (props.centralBankIndicator?.tableRows || []).map((row) => ({
    country: row[0],
    baseRate: parseRate(row[1]),
    rate3y: parseRate(row[2]),
    rate10y: parseRate(row[3]),
  }))
  const countries = [...new Set([
    ...treasuryRows.map((row) => row.country),
    ...centralRows.map((row) => row.country),
  ])]

  return countries.map((country) => {
    const treasury = treasuryRows.find((row) => row.country === country) || {}
    const central = centralRows.find((row) => row.country === country) || {}

    return {
      country,
      baseRate: central.baseRate,
      rate3y: treasury.rate3y ?? central.rate3y,
      rate10y: treasury.rate10y ?? central.rate10y,
      tone: getCountryTone(country),
    }
  })
})

const spreadRows = computed(() =>
  (props.yieldSpreadIndicator?.tableRows || []).slice(0, 3).map((row) => ({
    country: row[0],
    value: row[1],
    tone: getCountryTone(row[0]),
  })),
)

const currentValue = computed(() => {
  const korea = rateRows.value.find((row) => row.country.includes('한국') || row.country.includes('대한민국'))
  return formatRate(korea?.rate10y ?? rateRows.value[0]?.rate10y)
})
</script>

<template>
  <article class="indicator-section">
    <header class="indicator-header">
      <div>
        <p class="eyebrow">Indicator Report</p>
        <h2>나라별 금리</h2>
      </div>
      <div class="current-value">
        <span>한국 10년물 기준</span>
        <strong>{{ currentValue }}</strong>
        <small>기준금리 / 3년 / 10년 금리 비교</small>
      </div>
    </header>

    <section class="explanation">
      <h3>개념 설명</h3>
      <p>국가별 기준금리와 3년, 10년 국채 금리를 함께 비교해 통화정책 수준과 장단기 금리 부담을 확인합니다.</p>
    </section>

    <section class="table-panel">
      <div class="panel-title">
        <h3>데이터 표</h3>
        <span>{{ rateRows.length }}개 항목</span>
      </div>
      <table class="rate-table">
        <thead>
          <tr>
            <th>구분</th>
            <th>기준금리</th>
            <th>3년 금리</th>
            <th>10년 금리</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rateRows" :key="row.country">
            <th scope="row">
              <span class="country-chip" :class="row.tone">{{ row.country }}</span>
            </th>
            <td>{{ formatRate(row.baseRate) }}</td>
            <td>{{ formatRate(row.rate3y) }}</td>
            <td>{{ formatRate(row.rate10y) }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section v-if="spreadRows.length" class="spread-summary">
      <div class="panel-title">
        <div>
          <h3>장단기 금리차 요약</h3>
          <p>10년 금리에서 3년 금리를 뺀 값입니다.</p>
        </div>
        <button type="button" @click="emit('navigate-indicator', 'yield-spread')">자세히 보기</button>
      </div>
      <div class="spread-grid">
        <article v-for="row in spreadRows" :key="`${row.country}-spread`" :class="row.tone">
          <span>{{ row.country }}</span>
          <strong>{{ row.value }}</strong>
        </article>
      </div>
    </section>

    <section class="chart-panel">
      <div class="panel-title">
        <div>
          <h3>그래프</h3>
          <p>단위: %, 세로축 0~10%</p>
        </div>
        <span>3년 / 10년 금리 비교</span>
      </div>

      <div class="chart-grid">
        <article v-for="row in rateRows" :key="`${row.country}-chart`" class="chart-card" :class="row.tone">
          <header>
            <strong>{{ row.country }}</strong>
          </header>
          <div class="bar-chart">
            <div class="value-row">
              <span>{{ formatRate(row.rate3y) }}</span>
              <span>{{ formatRate(row.rate10y) }}</span>
            </div>
            <div class="axis">
              <span>10%</span>
              <span>5%</span>
              <span>0%</span>
            </div>
            <div class="plot">
              <div class="grid-lines" aria-hidden="true">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <div class="bar-item">
                <span :style="{ height: barHeight(row.rate3y) }"></span>
              </div>
              <div class="bar-item">
                <span :style="{ height: barHeight(row.rate10y) }"></span>
              </div>
            </div>
            <div class="term-row">
              <span>3년</span>
              <span>10년</span>
            </div>
          </div>
        </article>
      </div>
    </section>
  </article>
</template>

<style scoped>
.indicator-section {
  display: grid;
  gap: 20px;
}

.indicator-header,
.table-panel,
.chart-panel,
.explanation,
.spread-summary {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.indicator-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: start;
  padding: 26px;
  background: var(--surface);
}

.indicator-header h2 {
  margin-bottom: 0;
  font-size: clamp(26px, 4vw, 38px);
}

.current-value {
  display: grid;
  min-width: 220px;
  gap: 4px;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
  text-align: right;
}

.current-value span,
.current-value small,
.panel-title span,
.panel-title p,
.spread-grid span {
  color: var(--muted);
  font-size: 13px;
  font-weight: 800;
}

.current-value strong {
  color: var(--primary);
  font-size: 32px;
}

.explanation,
.table-panel,
.chart-panel,
.spread-summary {
  padding: 18px;
}

.explanation h3,
.panel-title h3 {
  margin-bottom: 8px;
  font-size: 18px;
}

.explanation p {
  margin-bottom: 0;
  line-height: 1.7;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.panel-title button {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 9px 12px;
  color: var(--primary-dark);
  background: var(--surface-soft);
  font-size: 12px;
  font-weight: 900;
}

.rate-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
}

.rate-table th,
.rate-table td {
  padding: 16px 18px;
  border: 1px solid var(--line);
  text-align: left;
}

.rate-table thead th {
  background: #eef5f8;
  color: var(--primary-dark);
}

.country-chip {
  display: inline-flex;
  min-width: 54px;
  justify-content: center;
  border-radius: 999px;
  padding: 6px 10px;
  color: white;
  background: var(--primary);
  font-size: 13px;
  font-weight: 900;
}

.country-chip.us,
.chart-card.us .bar-item > span,
.spread-grid article.us {
  border-color: #1f6f78;
}

.country-chip.us {
  background: #1f6f78;
}

.country-chip.jp {
  background: #d98c31;
}

.country-chip.kr {
  background: #127c57;
}

.spread-grid,
.chart-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.spread-grid article,
.chart-card {
  display: grid;
  gap: 8px;
  padding: 16px;
  border: 1px solid var(--line);
  border-left: 5px solid var(--primary);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.spread-grid article.us,
.chart-card.us {
  border-left-color: #1f6f78;
}

.spread-grid article.jp,
.chart-card.jp {
  border-left-color: #d98c31;
}

.spread-grid article.kr,
.chart-card.kr {
  border-left-color: #127c57;
}

.spread-grid strong {
  color: var(--primary-dark);
  font-size: 24px;
}

.bar-chart {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  grid-template-rows: auto 180px auto;
  row-gap: 8px;
  gap: 10px;
  min-height: 238px;
}

.value-row,
.term-row {
  grid-column: 2;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 26px;
  padding: 0 24px;
  text-align: center;
}

.value-row span {
  color: var(--primary-dark);
  font-size: 13px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
}

.term-row span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
}

.axis {
  grid-column: 1;
  grid-row: 2;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 180px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  text-align: right;
}

.plot {
  grid-column: 2;
  grid-row: 2;
  position: relative;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 26px;
  align-items: end;
  height: 180px;
  padding: 0 24px;
  border-left: 2px solid #9fb2c3;
  border-bottom: 2px solid #9fb2c3;
}

.grid-lines {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  pointer-events: none;
}

.grid-lines span {
  border-top: 1px solid #d9e4ee;
}

.bar-item {
  z-index: 1;
  display: grid;
  align-items: end;
  height: 180px;
  text-align: center;
}

.bar-item > span {
  width: min(58px, 76%);
  min-height: 6px;
  border-radius: 6px 6px 0 0;
  justify-self: center;
  background: var(--primary);
}

@media (max-width: 960px) {
  .indicator-header,
  .spread-grid,
  .chart-grid {
    grid-template-columns: 1fr;
  }

  .indicator-header {
    flex-direction: column;
  }
}
</style>
