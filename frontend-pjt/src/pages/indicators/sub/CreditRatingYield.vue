<script setup>
import IndicatorTable from './IndicatorTable.vue'

defineProps({
  indicator: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <article class="credit-rate-board">
    <header class="credit-board-header">
      <div>
        <p class="eyebrow">Credit Rating Rates</p>
        <h2>신용등급별 금리</h2>
        <p>DB의 채권 발행 조건을 기준으로 신용등급별 평균 표면금리를 비교합니다.</p>
      </div>
    </header>

    <section class="credit-guide-grid" aria-label="신용등급 지표 해석 안내">
      <article>
        <strong>등급별 평균 금리</strong>
        <p>신용등급별 채권의 표면금리 평균을 비교합니다. 등급이 낮을수록 발행 시 요구 금리가 높아질 수 있습니다.</p>
      </article>
      <article>
        <strong>채권 수</strong>
        <p>평균 금리 계산에 포함된 채권 수입니다. 표본 수가 적은 등급은 해석에 주의가 필요합니다.</p>
      </article>
      <article>
        <strong>주의해서 볼 점</strong>
        <p>높은 금리는 높은 보상일 수도 있지만 신용위험, 유동성위험, 발행사 이슈가 반영된 결과일 수 있습니다.</p>
      </article>
    </section>

    <section class="credit-table-wrap">
      <IndicatorTable :columns="indicator.tableColumns" :rows="indicator.tableRows" />
    </section>

    <section class="credit-board-note">
      <h3>등급별 금리 해석</h3>
      <p>{{ indicator.insight }}</p>
    </section>
  </article>
</template>

<style scoped>
.credit-rate-board {
  display: grid;
  gap: 20px;
}

.credit-board-header h2 {
  margin-bottom: 8px;
  font-size: clamp(28px, 4vw, 40px);
}

.credit-board-header p:not(.eyebrow) {
  margin-bottom: 0;
}

.credit-guide-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.credit-guide-grid article,
.credit-table-wrap,
.credit-board-note {
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
  box-shadow: var(--shadow);
}

.credit-guide-grid strong {
  color: var(--primary-dark);
  font-size: 14px;
}

.credit-guide-grid p,
.credit-board-note p {
  margin: 8px 0 0;
  color: var(--muted);
  line-height: 1.6;
}

.credit-board-note h3 {
  margin-bottom: 8px;
  font-size: 18px;
}

@media (max-width: 960px) {
  .credit-guide-grid {
    grid-template-columns: 1fr;
  }
}
</style>
