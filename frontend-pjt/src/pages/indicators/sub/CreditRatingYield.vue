<script setup>
import { computed, ref } from 'vue'
import { indicators } from '../../../data/indicators'

const activeRange = ref('3개월')
const ranges = ['1개월', '3개월', '1년']

const indicator = computed(() => indicators.find(i => i.id === 'credit-rating-yield'))
</script>

<template>
  <div class="indicator-content">
    <section class="insight-panel">
      <div>
        <p class="eyebrow">투자 지표 상세 보기</p>
        <h1>{{ indicator.title }}</h1>
        <p>{{ indicator.summary }}</p>
      </div>
      <div class="range-buttons">
        <button
          v-for="range in ranges"
          :key="range"
          :class="{ active: activeRange === range }"
          type="button"
          @click="activeRange = range"
        >
          {{ range }}
        </button>
      </div>
    </section>

    <section class="indicator-detail-grid">
      <article v-for="stat in indicator.stats" :key="stat.label">
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
      </article>
    </section>

    <svg viewBox="0 0 720 240" class="large-chart" :aria-label="`${indicator.title} 차트`">
      <polyline :points="indicator.chartPoints" />
      <line x1="20" y1="200" x2="700" y2="200" />
      <line x1="20" y1="40" x2="20" y2="200" />
    </svg>

    <p class="insight-text">{{ indicator.insight }}</p>
  </div>
</template>
