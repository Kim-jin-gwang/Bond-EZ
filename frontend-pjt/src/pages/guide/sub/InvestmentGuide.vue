<script setup>
import { ref } from 'vue'
import { guideContent } from '../../../data/guide/guide'

// 체크리스트 상태 관리 (사용자가 직접 클릭해볼 수 있도록 구현)
const checkedItems = ref(
  guideContent.checklist.reduce((acc, item) => {
    acc[item.id] = false
    return acc
  }, {})
)

const toggleItem = (id) => {
  checkedItems.value[id] = !checkedItems.value[id]
}
</script>

<template>
  <article class="guide-article">
    <div class="guide-header">
      <p class="eyebrow">{{ guideContent.eyebrow }}</p>
      <h1>{{ guideContent.title }}</h1>
      <p class="guide-intro">{{ guideContent.description }}</p>
    </div>

    <!-- 프로세스 타임라인 -->
    <div class="timeline-section">
      <h2 class="section-subtitle">성공 투자를 위한 4단계 프로세스</h2>
      <div class="timeline">
        <div v-for="(step, idx) in guideContent.steps" :key="idx" class="timeline-item">
          <div class="step-badge">{{ step.step }}</div>
          <div class="step-content">
            <h3>{{ step.title }}</h3>
            <p>{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 체크리스트 섹션 -->
    <div class="checklist-section">
      <h2 class="section-subtitle">투자 직전 필수 점검 항목</h2>
      <div class="checklist-card">
        <div
          v-for="item in guideContent.checklist"
          :key="item.id"
          :class="['checklist-item', { checked: checkedItems[item.id] }]"
          @click="toggleItem(item.id)"
        >
          <div class="checkbox-wrapper">
            <span class="custom-checkbox">
              <svg v-if="checkedItems[item.id]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </span>
          </div>
          <span class="checklist-text">{{ item.text }}</span>
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

.section-subtitle {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 24px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--surface-soft);
}

.timeline-section {
  margin-bottom: 48px;
}

.timeline {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 32px;
  padding-left: 20px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 36px;
  top: 10px;
  bottom: 10px;
  width: 2px;
  background: var(--line);
  z-index: 1;
}

.timeline-item {
  position: relative;
  display: flex;
  gap: 24px;
  z-index: 2;
}

.step-badge {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  box-shadow: 0 0 0 4px var(--surface-soft);
}

.step-content h3 {
  font-size: 17px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 8px 0;
}

.step-content p {
  font-size: 14.5px;
  line-height: 1.6;
  color: var(--muted);
  margin: 0;
}

.checklist-section {
  margin-bottom: 8px;
}

.checklist-card {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--bg);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checklist-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px;
  border-radius: 8px;
  background: var(--surface);
  border: 1px solid var(--line);
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
}

.checklist-item:hover {
  border-color: var(--primary);
  background: var(--surface-raised);
}

.checklist-item.checked {
  border-color: var(--primary);
  background: rgba(31, 111, 120, 0.03);
}

.checkbox-wrapper {
  margin-top: 2px;
}

.custom-checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid var(--line);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface);
  transition: all 0.2s ease;
}

.checklist-item:hover .custom-checkbox {
  border-color: var(--primary);
}

.checklist-item.checked .custom-checkbox {
  background: var(--primary);
  border-color: var(--primary);
}

.custom-checkbox svg {
  width: 14px;
  height: 14px;
  color: white;
}

.checklist-text {
  font-size: 15px;
  line-height: 1.5;
  color: var(--text);
  transition: color 0.2s ease;
}

.checklist-item.checked .checklist-text {
  color: var(--muted);
  text-decoration: line-through;
}

@media (max-width: 768px) {
  .guide-article {
    padding: 20px;
  }
  h1 {
    font-size: 22px;
  }
  .timeline::before {
    left: 20px;
  }
  .step-badge {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }
  .timeline {
    padding-left: 5px;
  }
  .checklist-text {
    font-size: 13.5px;
  }
}
</style>
