<script setup>
const terms = [
  { term: 'YTM', desc: '현재 가격으로 매수해 만기까지 보유할 때 기대할 수 있는 연환산 수익률입니다.' },
  { term: 'CALL 옵션', desc: '발행사가 정해진 조건에 따라 만기 전 채권을 상환할 수 있는 권리입니다.' },
  { term: '듀레이션', desc: '금리 변화에 채권 가격이 얼마나 민감하게 움직이는지 보여주는 지표입니다.' },
]
</script>

<template>
  <section class="page content-page">
    <div class="dictionary-search">
      <input type="search" placeholder="궁금한 채권 용어를 검색하세요" />
    </div>
    <article v-for="term in terms" :key="term.term" class="term-card">
      <h2>{{ term.term }}</h2>
      <p>{{ term.desc }}</p>
    </article>
  </section>
</template>
