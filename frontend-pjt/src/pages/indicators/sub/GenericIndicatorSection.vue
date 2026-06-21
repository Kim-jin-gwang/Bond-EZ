<script setup>
import { computed } from 'vue'
import IndicatorTable from './IndicatorTable.vue'

const props = defineProps({
  indicator: {
    type: Object,
    required: true,
  },
})

const barRows = computed(() => {
  const rows = props.indicator.tableRows || []
  const bars = props.indicator.bars || []

  return rows.map((row, index) => ({
    label: row[0],
    value: row[1],
    height: bars[index] || 42,
    description: row[row.length - 1],
  }))
})
</script>

<template>
  <article class="indicator-detail-card">
    <header class="indicator-detail-header">
      <div>
        <p class="eyebrow">Indicator Report</p>
        <h2>{{ indicator.title }}</h2>
      </div>
      <div class="indicator-current-value">
        <span>현재 기준</span>
        <strong>{{ indicator.value }}</strong>
        <small>{{ indicator.caption }}</small>
      </div>
    </header>

    <section class="indicator-explanation">
      <h3>개념 설명</h3>
      <p>{{ indicator.summary }}</p>
    </section>

    <section class="indicator-data-layout">
      <div class="indicator-panel">
        <div class="panel-title">
          <h3>데이터 표</h3>
          <span>{{ indicator.tableRows?.length || 0 }}개 항목</span>
        </div>
        <IndicatorTable :columns="indicator.tableColumns" :rows="indicator.tableRows" />
      </div>

      <div class="indicator-panel">
        <div class="panel-title">
          <h3>그래프</h3>
          <span>{{ indicator.chartType === 'bar' ? '막대 비교' : '흐름 비교' }}</span>
        </div>

        <svg
          v-if="indicator.chartType === 'line' || indicator.chartType === 'curve'"
          viewBox="0 0 720 260"
          class="indicator-chart line-chart"
          :aria-label="`${indicator.title} 그래프`"
        >
          <line x1="20" y1="205" x2="700" y2="205" />
          <line x1="20" y1="44" x2="20" y2="205" />
          <line x1="20" y1="155" x2="700" y2="155" />
          <line x1="20" y1="100" x2="700" y2="100" />
          <polyline :points="indicator.chartPoints" />
          <circle
            v-for="point in indicator.chartPoints.split(' ')"
            :key="point"
            :cx="point.split(',')[0]"
            :cy="point.split(',')[1]"
            r="5"
          />
        </svg>

        <div v-else class="indicator-chart bar-chart" :aria-label="`${indicator.title} 막대 그래프`">
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
      <p>{{ indicator.insight }}</p>
    </section>
  </article>
</template>

<style scoped>
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
.indicator-panel {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
}

.indicator-explanation,
.indicator-insight,
.indicator-panel {
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
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
  gap: 16px;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
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
  padding: 30px 18px 18px;
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

@media (max-width: 960px) {
  .indicator-detail-header,
  .indicator-data-layout {
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .indicator-current-value {
    width: 100%;
    text-align: left;
  }
}
</style>
