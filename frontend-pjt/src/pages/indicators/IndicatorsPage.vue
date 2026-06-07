<script setup>
import { computed } from 'vue'
import { indicators } from '../../data/indicators'

const props = defineProps({
  selectedIndicatorId: {
    type: String,
    default: 'treasury-rate',
  },
})

const emit = defineEmits(['navigate'])

const activeIndicator = computed(() => {
  return indicators.find((indicator) => indicator.id === props.selectedIndicatorId) ?? indicators[0]
})

const barRows = computed(() => {
  const rows = activeIndicator.value.tableRows || []
  const bars = activeIndicator.value.bars || []

  return rows.map((row, index) => ({
    label: row[0],
    value: row[1],
    height: bars[index] || 42,
  }))
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
        v-for="indicator in indicators"
        :key="indicator.id"
        :class="{ active: activeIndicator.id === indicator.id }"
        type="button"
        @click="$emit('navigate', 'indicators', indicator.id)"
      >
        {{ indicator.shortTitle || indicator.title }}
      </button>
    </div>

    <article class="indicator-detail-card">
      <header class="indicator-detail-header">
        <div>
          <p class="eyebrow">Indicator Report</p>
          <h2>{{ activeIndicator.title }}</h2>
        </div>
        <div class="indicator-current-value">
          <span>현재 기준</span>
          <strong>{{ activeIndicator.value }}</strong>
          <small>{{ activeIndicator.caption }}</small>
        </div>
      </header>

      <section class="indicator-explanation">
        <h3>개념 설명</h3>
        <p>{{ activeIndicator.summary }}</p>
      </section>

      <section class="indicator-data-layout">
        <div class="indicator-table-panel">
          <div class="panel-title">
            <h3>데이터 표</h3>
            <span>{{ activeIndicator.tableRows.length }}개 항목</span>
          </div>
          <div class="indicator-table-wrap">
            <table class="indicator-data-table">
              <thead>
                <tr>
                  <th v-for="column in activeIndicator.tableColumns" :key="column">{{ column }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in activeIndicator.tableRows" :key="row.join('-')">
                  <td v-for="cell in row" :key="cell">{{ cell }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="indicator-chart-panel">
          <div class="panel-title">
            <h3>그래프</h3>
            <span>{{ activeIndicator.chartType }}</span>
          </div>

          <svg
            v-if="activeIndicator.chartType === 'line' || activeIndicator.chartType === 'curve'"
            viewBox="0 0 720 240"
            class="indicator-chart line-chart"
            aria-label="금리 추이 그래프"
          >
            <line x1="20" y1="190" x2="700" y2="190" />
            <line x1="20" y1="40" x2="20" y2="190" />
            <line x1="20" y1="140" x2="700" y2="140" />
            <line x1="20" y1="90" x2="700" y2="90" />
            <polyline :points="activeIndicator.chartPoints" />
            <circle
              v-for="point in activeIndicator.chartPoints.split(' ')"
              :key="point"
              :cx="point.split(',')[0]"
              :cy="point.split(',')[1]"
              r="5"
            />
          </svg>

          <div v-else class="indicator-chart bar-chart" aria-label="금리 비교 막대 그래프">
            <div v-for="row in barRows" :key="row.label" class="bar-item">
              <span :style="{ height: `${row.height}%` }"></span>
              <strong>{{ row.value }}</strong>
              <small>{{ row.label }}</small>
            </div>
          </div>
        </div>
      </section>

      <section class="indicator-insight">
        <h3>데이터 요약 및 설명</h3>
        <p>{{ activeIndicator.insight }}</p>
        <div class="indicator-stat-grid">
          <article v-for="stat in activeIndicator.stats" :key="stat.label">
            <span>{{ stat.label }}</span>
            <strong>{{ stat.value }}</strong>
          </article>
        </div>
      </section>
    </article>
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

.indicator-detail-card {
  display: grid;
  gap: 20px;
  padding: 26px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.indicator-detail-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: start;
}

.indicator-detail-header h2 {
  margin-bottom: 0;
  font-size: clamp(26px, 4vw, 38px);
}

.indicator-current-value {
  display: grid;
  min-width: 220px;
  gap: 4px;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
  text-align: right;
}

.indicator-current-value span,
.indicator-current-value small,
.panel-title span {
  color: var(--muted);
  font-size: 13px;
}

.indicator-current-value strong {
  color: var(--primary);
  font-size: 32px;
}

.indicator-explanation,
.indicator-insight,
.indicator-table-panel,
.indicator-chart-panel {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
}

.indicator-explanation,
.indicator-insight {
  padding: 20px;
}

.indicator-explanation h3,
.indicator-insight h3,
.panel-title h3 {
  margin-bottom: 8px;
  font-size: 18px;
}

.indicator-explanation p,
.indicator-insight p {
  margin-bottom: 0;
  line-height: 1.7;
}

.indicator-data-layout {
  display: grid;
  grid-template-columns: minmax(360px, 0.95fr) minmax(420px, 1.05fr);
  gap: 16px;
}

.indicator-table-panel,
.indicator-chart-panel {
  min-width: 0;
  padding: 18px;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.indicator-table-wrap {
  overflow-x: auto;
}

.indicator-data-table {
  width: 100%;
  min-width: 620px;
  border-collapse: collapse;
}

.indicator-data-table th,
.indicator-data-table td {
  padding: 13px 14px;
  border: 1px solid var(--line);
  text-align: left;
}

.indicator-data-table th {
  color: var(--text);
  background: #f5f8fb;
  font-size: 13px;
  font-weight: 900;
}

.indicator-data-table td {
  font-size: 14px;
}

.indicator-chart {
  width: 100%;
  min-height: 260px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fbfdff;
}

.line-chart line {
  stroke: #d8e1ea;
  stroke-width: 2;
}

.line-chart polyline {
  fill: none;
  stroke: var(--primary);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 6;
}

.line-chart circle {
  fill: white;
  stroke: var(--primary);
  stroke-width: 4;
}

.bar-chart {
  display: flex;
  align-items: end;
  justify-content: space-around;
  gap: 16px;
  padding: 24px 18px 18px;
}

.bar-item {
  display: grid;
  grid-template-rows: 1fr auto auto;
  gap: 8px;
  align-items: end;
  width: 100%;
  height: 220px;
  text-align: center;
}

.bar-item span {
  width: 100%;
  min-height: 18px;
  border-radius: 6px 6px 0 0;
  background: linear-gradient(180deg, var(--primary), var(--accent));
}

.bar-item strong {
  color: var(--primary-dark);
  font-size: 14px;
}

.bar-item small {
  color: var(--muted);
  font-weight: 800;
}

.indicator-stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.indicator-stat-grid article {
  display: grid;
  gap: 6px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.indicator-stat-grid span {
  color: var(--muted);
  font-size: 13px;
}

.indicator-stat-grid strong {
  color: var(--primary-dark);
  font-size: 22px;
}

@media (max-width: 960px) {
  .indicator-detail-header,
  .indicator-data-layout {
    grid-template-columns: 1fr;
  }

  .indicator-detail-header {
    flex-direction: column;
  }

  .indicator-current-value {
    width: 100%;
    text-align: left;
  }
}

@media (max-width: 640px) {
  .indicator-detail-card {
    padding: 18px;
  }

  .indicator-stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
