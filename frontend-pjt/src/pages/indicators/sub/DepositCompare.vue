<script setup>
import { computed, ref } from 'vue'
import { parseRate } from './indicatorUtils'

const props = defineProps({
  indicator: {
    type: Object,
    required: true,
  },
})

const bankFilter = ref('all')
const sortMode = ref('prime-desc')

const depositRows = computed(() =>
  (props.indicator.tableRows || []).map((row, index) => ({
    bank: row[0],
    product: row[1],
    baseRate: parseRate(row[2]),
    primeRate: parseRate(row[3]),
    baseRateLabel: row[2],
    primeRateLabel: row[3],
    originalIndex: index,
  })),
)

const bankOptions = computed(() => ['all', ...new Set(depositRows.value.map((row) => row.bank).filter(Boolean))])

const filteredRows = computed(() => {
  const rows = bankFilter.value === 'all'
    ? [...depositRows.value]
    : depositRows.value.filter((row) => row.bank === bankFilter.value)
  const sortKey = sortMode.value === 'base-desc' ? 'baseRate' : 'primeRate'

  return rows
    .sort((a, b) => (Number.isFinite(b[sortKey]) ? b[sortKey] : -Infinity) - (Number.isFinite(a[sortKey]) ? a[sortKey] : -Infinity))
    .map((row, index) => ({ ...row, rank: index + 1 }))
})

const bestRow = computed(() =>
  [...depositRows.value].sort((a, b) => (b.primeRate ?? -Infinity) - (a.primeRate ?? -Infinity))[0],
)
</script>

<template>
  <article class="deposit-section">
    <header class="indicator-header">
      <div>
        <p class="eyebrow">Deposit Rates</p>
        <h2>예금 금리 비교</h2>
      </div>
      <div class="current-value">
        <span>우대금리 기준</span>
        <strong>{{ bestRow?.primeRateLabel ?? indicator.value }}</strong>
        <small>{{ bestRow ? `${bestRow.bank} · ${bestRow.product}` : indicator.caption }}</small>
      </div>
    </header>

    <section class="explanation">
      <h3>개념 설명</h3>
      <p>은행별 예금 상품의 기본금리와 우대금리를 비교합니다. 채권 수익률과 비교할 때 참고할 수 있는 기준 데이터입니다.</p>
    </section>

    <section class="filter-panel">
      <div>
        <strong>은행별 보기</strong>
        <div class="filter-chips">
          <button
            v-for="bank in bankOptions"
            :key="bank"
            :class="{ active: bankFilter === bank }"
            type="button"
            @click="bankFilter = bank"
          >
            {{ bank === 'all' ? '전체 은행' : bank }}
          </button>
        </div>
      </div>
      <div>
        <strong>정렬 기준</strong>
        <div class="filter-chips">
          <button :class="{ active: sortMode === 'prime-desc' }" type="button" @click="sortMode = 'prime-desc'">
            우대금리 높은 순
          </button>
          <button :class="{ active: sortMode === 'base-desc' }" type="button" @click="sortMode = 'base-desc'">
            기본금리 높은 순
          </button>
        </div>
      </div>
    </section>

    <section class="table-panel">
      <div class="panel-title">
        <div>
          <h3>예금 상품 목록</h3>
          <p>{{ bankFilter === 'all' ? '전체 은행' : bankFilter }} · {{ sortMode === 'prime-desc' ? '우대금리 높은 순' : '기본금리 높은 순' }}</p>
        </div>
        <span>{{ filteredRows.length }}개 항목</span>
      </div>
      <table class="deposit-table">
        <thead>
          <tr>
            <th>순위</th>
            <th>은행</th>
            <th>상품명</th>
            <th>기본금리</th>
            <th>우대금리</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in filteredRows" :key="`${row.bank}-${row.product}`">
            <td>{{ row.rank }}</td>
            <th scope="row">{{ row.bank }}</th>
            <td>{{ row.product }}</td>
            <td>{{ row.baseRateLabel }}</td>
            <td>
              <strong>{{ row.primeRateLabel }}</strong>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="reading-note">
      <h3>데이터 요약 및 설명</h3>
      <p>{{ indicator.insight }}</p>
    </section>
  </article>
</template>

<style scoped>
.deposit-section {
  display: grid;
  gap: 20px;
}

.indicator-header,
.explanation,
.filter-panel,
.table-panel,
.reading-note {
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
.panel-title p {
  color: var(--muted);
  font-size: 13px;
  font-weight: 800;
}

.current-value strong {
  color: var(--primary);
  font-size: 32px;
}

.explanation,
.filter-panel,
.table-panel,
.reading-note {
  padding: 18px;
}

.explanation h3,
.panel-title h3,
.reading-note h3 {
  margin-bottom: 8px;
  font-size: 18px;
}

.explanation p,
.reading-note p {
  margin: 0;
  line-height: 1.7;
}

.filter-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.6fr);
  gap: 16px;
}

.filter-panel > div {
  display: grid;
  gap: 10px;
}

.filter-panel strong {
  color: var(--primary-dark);
  font-size: 14px;
}

.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-chips button {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 8px 12px;
  color: var(--text);
  background: var(--surface-soft);
  font-size: 12px;
  font-weight: 900;
}

.filter-chips button.active {
  border-color: var(--primary-dark);
  color: white;
  background: var(--primary-dark);
}

.panel-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.deposit-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
}

.deposit-table th,
.deposit-table td {
  padding: 14px 16px;
  border: 1px solid var(--line);
  text-align: left;
  word-break: keep-all;
}

.deposit-table thead th {
  background: #eef5f8;
  color: var(--primary-dark);
}

.deposit-table strong {
  color: var(--primary);
}

@media (max-width: 960px) {
  .indicator-header,
  .filter-panel {
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}
</style>
