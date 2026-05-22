<script setup>
import { ref } from 'vue'
import { selectedBond } from '../../data/bonds'

const activeDetailTab = ref('core')
</script>

<template>
  <section class="page detail-page">
    <section class="detail-hero">
      <div>
        <p class="eyebrow">채권 세부 내용</p>
        <h1>{{ selectedBond.name }}</h1>
        <p>{{ selectedBond.code }} · {{ selectedBond.rating }} · {{ selectedBond.option }} 옵션</p>
      </div>
      <div class="hero-yield">
        <span>매수 수익률</span>
        <strong>{{ selectedBond.buyYield }}</strong>
      </div>
    </section>

    <div class="risk-tags">
      <span v-for="risk in selectedBond.riskTags" :key="risk">#{{ risk }}</span>
    </div>

    <div class="tab-group detail-tabs">
      <button :class="{ active: activeDetailTab === 'core' }" type="button" @click="activeDetailTab = 'core'">핵심</button>
      <button :class="{ active: activeDetailTab === 'all' }" type="button" @click="activeDetailTab = 'all'">전체 보기</button>
    </div>

    <section class="spec-grid">
      <article><span>수익률</span><strong>{{ selectedBond.buyYield }}</strong></article>
      <article><span>만기</span><strong>{{ selectedBond.maturity }}</strong></article>
      <article><span>신용등급</span><strong>{{ selectedBond.rating }}</strong></article>
      <article><span>세전/세후 수익률</span><strong>3.82% / 3.23%</strong></article>
      <article><span>이자 주기</span><strong>{{ selectedBond.interestCycle }}</strong></article>
      <article v-if="activeDetailTab === 'all'"><span>듀레이션</span><strong>{{ selectedBond.duration }}</strong></article>
      <article v-if="activeDetailTab === 'all'"><span>표면금리</span><strong>{{ selectedBond.coupon }}</strong></article>
      <article v-if="activeDetailTab === 'all'"><span>발행 코드</span><strong>{{ selectedBond.code }}</strong></article>
    </section>

    <section class="calculator">
      <h2>채권 수익 계산기</h2>
      <div class="calc-layout">
        <label><span>투자 금액</span><input value="10,000,000" /></label>
        <label><span>매수 가격</span><input value="10,185" /></label>
        <div class="calc-result">
          <span>예상 이자</span>
          <strong>205,000원</strong>
          <span>세후 최종 수익</span>
          <strong>323,000원</strong>
        </div>
      </div>
      <div class="profit-chart" aria-hidden="true">
        <span style="height: 30%"></span>
        <span style="height: 44%"></span>
        <span style="height: 62%"></span>
        <span style="height: 78%"></span>
      </div>
    </section>
  </section>
</template>
