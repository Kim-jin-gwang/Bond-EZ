<script setup>
import { riskContent } from '../../../data/guide/risk'
</script>

<template>
  <article class="guide-article">
    <div class="guide-header">
      <p class="eyebrow">{{ riskContent.eyebrow }}</p>
      <h1>{{ riskContent.title }}</h1>
      <p class="guide-intro">{{ riskContent.description }}</p>
    </div>

    <!-- 3대 위험 카드 리스트 -->
    <div class="risks-container">
      <div v-for="(risk, idx) in riskContent.risks" :key="idx" class="risk-card">
        <div class="risk-card-header">
          <span class="risk-icon" aria-hidden="true">{{ risk.icon }}</span>
          <div class="risk-title-area">
            <h3>{{ risk.title }}</h3>
            <span :class="['risk-badge', risk.badgeClass]">{{ risk.badge }}</span>
          </div>
        </div>
        <div class="risk-card-body">
          <p class="risk-desc">{{ risk.desc }}</p>
          <div class="risk-solution">
            <strong>💡 대응 전략:</strong>
            <p>{{ risk.solution }}</p>
          </div>
        </div>
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

.risks-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

.risk-card {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--bg);
  overflow: hidden;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.risk-card:hover {
  border-color: var(--accent);
  box-shadow: 0 8px 24px rgba(217, 140, 49, 0.05);
}

.risk-card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}

.risk-icon {
  font-size: 28px;
}

.risk-title-area {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.risk-title-area h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  margin: 0;
}

.risk-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 20px;
}

.risk-high {
  background: rgba(192, 57, 43, 0.1);
  color: var(--danger);
  border: 1px solid rgba(192, 57, 43, 0.2);
}

.risk-medium {
  background: rgba(219, 140, 49, 0.1);
  color: var(--accent);
  border: 1px solid rgba(219, 140, 49, 0.2);
}

.risk-card-body {
  padding: 24px;
}

.risk-desc {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text);
  margin: 0 0 20px 0;
}

.risk-solution {
  background: var(--surface);
  border-left: 4px solid var(--primary);
  border-radius: 0 8px 8px 0;
  padding: 16px 20px;
}

.risk-solution strong {
  display: block;
  font-size: 14px;
  color: var(--primary);
  margin-bottom: 6px;
}

.risk-solution p {
  font-size: 14px;
  line-height: 1.6;
  color: var(--muted);
  margin: 0;
}

@media (max-width: 768px) {
  .guide-article {
    padding: 20px;
  }
  h1 {
    font-size: 22px;
  }
  .risk-card-header {
    padding: 16px;
  }
  .risk-card-body {
    padding: 16px;
  }
  .risk-title-area {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
}
</style>
