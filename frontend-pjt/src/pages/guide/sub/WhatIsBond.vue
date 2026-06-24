<script setup>
import { whatContent } from '../../../data/guide/what'
</script>

<template>
  <article class="guide-article">
    <div class="guide-header">
      <p class="eyebrow">{{ whatContent.eyebrow }}</p>
      <h1>{{ whatContent.title }}</h1>
      <p class="guide-intro">{{ whatContent.definition }}</p>
    </div>

    <!-- 핵심 요소 그리드 -->
    <div class="features-section">
      <h2 class="section-subtitle">채권의 4대 핵심 구성 요소</h2>
      <div class="features-grid">
        <div v-for="(feat, idx) in whatContent.features" :key="idx" class="feature-card">
          <div class="feat-icon" aria-hidden="true">{{ feat.icon }}</div>
          <div class="feat-info">
            <h3>{{ feat.title }}</h3>
            <p>{{ feat.desc }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 예금 vs 채권 비교 테이블 -->
    <div class="comparison-section">
      <h2 class="section-subtitle">{{ whatContent.comparison.title }}</h2>
      <div class="table-wrapper">
        <table class="comparison-table">
          <thead>
            <tr>
              <th v-for="(header, idx) in whatContent.comparison.headers" :key="idx">
                {{ header }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, rIdx) in whatContent.comparison.rows" :key="rIdx">
              <td class="col-label">{{ row[0] }}</td>
              <td>{{ row[1] }}</td>
              <td class="highlight-col">{{ row[2] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </article>
</template>

<style scoped>
.guide-article {
  padding: 32px;
  border-radius: 12px;
  background: var(--surface);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}

.guide-header {
  margin-bottom: 40px;
}

.eyebrow {
  color: var(--primary);
  font-weight: 700;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 8px 0;
}

h1 {
  font-size: 26px;
  font-weight: 800;
  color: var(--text);
  margin: 0 0 16px 0;
  line-height: 1.35;
}

.guide-intro {
  font-size: 16px;
  line-height: 1.7;
  color: var(--muted);
  margin: 0;
}

.section-subtitle {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 20px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--surface-soft);
}

.features-section {
  margin-bottom: 48px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr); /* 2x2 배치 고정 */
  gap: 20px;
}

.feature-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  background: var(--bg);
  border: 1px solid var(--line);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(23, 43, 59, 0.06);
  border-color: var(--primary);
}

.feat-icon {
  font-size: 32px;
  display: flex;
  align-items: flex-start;
  margin-top: 2px;
}

.feat-info h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 8px 0;
}

.feat-info p {
  font-size: 14px;
  line-height: 1.6;
  color: var(--muted);
  margin: 0;
}

.comparison-section {
  margin-bottom: 8px;
}

.table-wrapper {
  border-radius: 12px;
  border: 1px solid var(--line);
  overflow: hidden; /* 가로 스크롤 제거 */
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 15px;
  table-layout: fixed; /* 테이블 고정 레이아웃으로 스크롤바 억제 및 너비 확장 */
}

.comparison-table th {
  background: var(--surface-soft);
  color: var(--text);
  font-weight: 700;
  padding: 16px 20px;
  border-bottom: 1px solid var(--line);
}

.comparison-table td {
  padding: 16px 20px;
  border-bottom: 1px solid var(--line);
  color: var(--muted);
  line-height: 1.6;
  word-break: keep-all;
  overflow-wrap: break-word;
}

.comparison-table tr:last-child td {
  border-bottom: none;
}

/* 첫 번째 열: 비교 항목 */
.comparison-table th:nth-child(1),
.comparison-table td:nth-child(1) {
  width: 20%;
  font-weight: 600;
  color: var(--text) !important;
  background: #fbfcfd;
}

/* 두 번째 열: 은행 예금 */
.comparison-table th:nth-child(2),
.comparison-table td:nth-child(2) {
  width: 40%;
}

/* 세 번째 열: 채권 투자 */
.comparison-table th:nth-child(3),
.comparison-table td:nth-child(3) {
  width: 40%;
  color: var(--primary) !important;
  font-weight: 600;
  background: rgba(31, 111, 120, 0.02);
}

@media (max-width: 768px) {
  .guide-article {
    padding: 20px;
  }
  h1 {
    font-size: 22px;
  }
  .features-grid {
    grid-template-columns: 1fr; /* 모바일에서는 1열로 떨어짐 */
    gap: 16px;
  }
  .comparison-table {
    font-size: 13px;
  }
  .comparison-table th, .comparison-table td {
    padding: 12px 10px; /* 패딩을 줄여 스크롤바 없이 꽉 차게 보이도록 함 */
  }
}
</style>
