<script setup>
import { computed } from 'vue'
import { formatRateGap, getCountryTone, getSpreadState, parseRate, spreadBarStyle } from './indicatorUtils'

const props = defineProps({
  indicator: {
    type: Object,
    required: true,
  },
})

const spreadRows = computed(() =>
  (props.indicator.tableRows || []).map((row) => {
    const spread = parseRate(row[1])

    return {
      country: row[0],
      spread,
      value: formatRateGap(spread),
      state: getSpreadState(spread),
      tone: getCountryTone(row[0]),
    }
  }),
)

const currentValue = computed(() => {
  const korea = spreadRows.value.find((row) => row.country.includes('한국') || row.country.includes('대한민국'))
  return korea?.value ?? spreadRows.value[0]?.value ?? '-'
})
</script>

<template>
  <article class="indicator-section">
    <header class="indicator-header">
      <div>
        <p class="eyebrow">Indicator Report</p>
        <h2>장단기 금리차</h2>
      </div>
      <div class="current-value">
        <span>한국 기준</span>
        <strong>{{ currentValue }}</strong>
        <small>10년 금리 - 3년 금리</small>
      </div>
    </header>

    <section class="explanation">
      <h3>개념 설명</h3>
      <p>10년 금리에서 3년 금리를 뺀 값입니다. 값이 낮아질수록 장기와 단기 금리의 차이가 줄어드는 흐름으로 볼 수 있습니다.</p>
    </section>

    <section class="table-panel">
      <div class="panel-title">
        <h3>데이터 표</h3>
        <span>{{ spreadRows.length }}개 항목</span>
      </div>
      <table class="spread-table">
        <thead>
          <tr>
            <th>구분</th>
            <th>장단기 금리차</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in spreadRows" :key="row.country">
            <th scope="row">{{ row.country }}</th>
            <td>
              <strong :class="{ negative: row.spread < 0 }">{{ row.value }}</strong>
            </td>
            <td>
              <span class="state-pill" :class="{ negative: row.spread < 0, flat: row.spread >= 0 && row.spread <= 0.15 }">
                {{ row.state }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="summary-grid">
      <article v-for="row in spreadRows" :key="`${row.country}-summary`" :class="row.tone">
        <span>{{ row.country }}</span>
        <strong :class="{ negative: row.spread < 0 }">{{ row.value }}</strong>
        <small>{{ row.state }}</small>
      </article>
    </section>

    <section class="chart-panel">
      <div class="panel-title">
        <div>
          <h3>그래프</h3>
          <p>단위: %p, 가운데 0%p 기준</p>
        </div>
        <span>10년 금리 - 3년 금리</span>
      </div>

      <div class="spread-chart-grid">
        <article v-for="row in spreadRows" :key="`${row.country}-chart`" class="spread-card" :class="row.tone">
          <header>
            <strong>{{ row.country }}</strong>
            <span>{{ row.state }}</span>
          </header>
          <div class="spread-value">
            <strong :class="{ negative: row.spread < 0 }">{{ row.value }}</strong>
          </div>
          <div class="spread-scale" aria-hidden="true">
            <span>역전</span>
            <span>0%p</span>
            <span>정상</span>
          </div>
          <div class="spread-bar-track">
            <span class="spread-zero-line" aria-hidden="true"></span>
            <span class="spread-bar" :class="{ negative: row.spread < 0 }" :style="spreadBarStyle(row.spread)"></span>
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
.explanation {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
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
.summary-grid span,
.summary-grid small,
.spread-card header span {
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
.chart-panel {
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

.spread-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
}

.spread-table th,
.spread-table td {
  padding: 16px 18px;
  border: 1px solid var(--line);
  text-align: left;
}

.spread-table thead th {
  background: #eef5f8;
  color: var(--primary-dark);
}

.spread-table strong,
.summary-grid strong,
.spread-value strong {
  color: var(--primary-dark);
  font-size: 22px;
}

.spread-table strong.negative,
.summary-grid strong.negative,
.spread-value strong.negative {
  color: #b45309;
}

.state-pill {
  display: inline-flex;
  border-radius: 999px;
  padding: 7px 12px;
  color: #0f6f52;
  background: #e5f5ef;
  font-size: 12px;
  font-weight: 900;
}

.state-pill.flat {
  color: #1f6f78;
  background: #e8f2f6;
}

.state-pill.negative {
  color: #a15c12;
  background: #fff1dc;
}

.summary-grid,
.spread-chart-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.summary-grid article,
.spread-card {
  display: grid;
  gap: 8px;
  padding: 16px;
  border: 1px solid var(--line);
  border-left: 5px solid var(--primary);
  border-radius: 8px;
  background: white;
  box-shadow: var(--shadow);
}

.summary-grid article.us,
.spread-card.us {
  border-left-color: #1f6f78;
}

.summary-grid article.jp,
.spread-card.jp {
  border-left-color: #d98c31;
}

.summary-grid article.kr,
.spread-card.kr {
  border-left-color: #127c57;
}

.spread-card header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.spread-scale {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
}

.spread-scale span:nth-child(2) {
  text-align: center;
}

.spread-scale span:nth-child(3) {
  text-align: right;
}

.spread-bar-track {
  position: relative;
  height: 34px;
  border-radius: 999px;
  background: linear-gradient(90deg, #fff7ed 0 50%, #e5f5ef 50% 100%);
  box-shadow: inset 0 0 0 1px #d7e3ee;
}

.spread-zero-line {
  position: absolute;
  top: -7px;
  bottom: -7px;
  left: 50%;
  width: 2px;
  border-radius: 999px;
  background: #8fa5b8;
}

.spread-bar {
  position: absolute;
  top: 8px;
  bottom: 8px;
  min-width: 6px;
  border-radius: 999px;
  background: #127c57;
}

.spread-bar.negative {
  background: #d98c31;
}

@media (max-width: 960px) {
  .indicator-header,
  .summary-grid,
  .spread-chart-grid {
    grid-template-columns: 1fr;
  }

  .indicator-header {
    flex-direction: column;
  }
}
</style>
