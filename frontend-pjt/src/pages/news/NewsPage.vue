<template>
  <section class="page content-page">
    <div class="page-heading compact">
      <p class="eyebrow">금리 뉴스</p>
      <h1>금리와 채권 시장 뉴스를 빠르게 훑어보세요</h1>
    </div>
    <div class="news-filter">
      <input type="date" />
      <select>
        <option>전체 출처</option>
        <option>한국은행</option>
        <option>금융투자협회</option>
      </select>
    </div>
    <article v-for="idx in 3" :key="idx" class="news-item">
      <div class="thumbnail"></div>
      <div>
        <h2>국고채 금리, 장기물 중심으로 소폭 상승</h2>
        <p>Bond Daily · 2026.05.22</p>
      </div>
    </article>
  </section>
</template>
