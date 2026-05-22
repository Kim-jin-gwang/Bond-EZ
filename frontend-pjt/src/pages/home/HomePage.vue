<script setup>
import { computed, ref } from 'vue'
import { indicators } from '../../data/indicators'
import { bonds } from '../../data/bonds'

const props = defineProps({
  isLoggedIn: {
    type: Boolean,
    default: false,
  },
  user: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['navigate'])

const filtersOpen = ref(false)
const searchKeyword = ref('')
const selectedFilters = ref({
  bondTypes: ['국채'],
  maturities: [],
  yields: [],
  ratings: [],
  interestCycles: [],
})

const filterGroups = [
  {
    key: 'bondTypes',
    label: '채권 종류',
    options: ['국채', '회사채', '금융채'],
  },
  {
    key: 'maturities',
    label: '만기',
    options: ['1년 이하', '1~3년', '3~5년', '5~10년', '10년 이상'],
  },
  {
    key: 'yields',
    label: '수익률',
    options: ['3% 이상', '4% 이상', '5% 이상', '6% 이상'],
  },
  {
    key: 'ratings',
    label: '신용등급',
    options: ['AAA', 'AA', 'A', 'BBB'],
  },
  {
    key: 'interestCycles',
    label: '이자 지급 주기',
    options: ['3개월', '6개월', '12개월', '만기일시'],
  },
]

// 개인화 큐레이션 데이터 (Mock)
const curatedBonds = computed(() => {
  if (!props.isLoggedIn) {
    // 게스트에게는 거래량 많은 순 등으로 보여줌 (여기서는 상위 3개)
    return bonds.slice(0, 3)
  }

  if (props.user.type === '안정추구형') {
    // 안정형: 국채 및 AAA 등급 금융채
    return bonds.filter(b => b.type === '국채' || b.ratingGroup === 'AAA').slice(0, 3)
  } else if (props.user.type === '적극투자형') {
    // 적극형: 수익률 높은 회사채 및 금융채
    return [...bonds].sort((a, b) => b.yieldValue - a.yieldValue).slice(0, 3)
  }

  return bonds.slice(0, 3)
})

function cloneFilters() {
  return Object.fromEntries(
    Object.entries(selectedFilters.value).map(([key, values]) => [key, [...values]]),
  )
}

function searchBonds() {
  emit('navigate', 'market', {
    source: 'search',
    keyword: searchKeyword.value.trim(),
    filters: cloneFilters(),
  })
}
</script>

<template>
  <section class="page home-page">
    <div class="page-heading">
      <p class="eyebrow">채권이지 대시보드</p>
      <h1>어려운 채권 투자,</h1>
      <h1>이제 쉽게 비교하고 확인하세요</h1>
      <p>금리 흐름, 채권 정보 요약, 신용 등급, 옵션 일정 등 투자 판단에 필요한 정보를 한눈에 정리해 빠르게 보여드립니다.</p>
    </div>

    <section class="market-indicator-section">
      <div class="section-title">
        <h2>실시간 시장 지표</h2>
        <button type="button" @click="$emit('navigate', 'indicators')">상세 보기</button>
      </div>
      <section class="indicator-grid" aria-label="투자 지표 대시보드">
        <button
          v-for="indicator in indicators"
          :key="indicator.title"
          class="metric-card"
          type="button"
          @click="$emit('navigate', 'indicators', indicator.id)"
        >
          <span class="card-title">{{ indicator.title }}</span>
          <strong>{{ indicator.value }}</strong>
          <span class="card-caption">{{ indicator.caption }}</span>

          <svg v-if="indicator.type === 'line'" viewBox="0 0 150 58" class="sparkline" aria-hidden="true">
            <polyline points="4,34 28,30 52,33 76,28 100,26 124,31 146,24" />
          </svg>
          <div v-else-if="indicator.type === 'bar'" class="mini-bars" aria-hidden="true">
            <span v-for="bar in indicator.bars" :key="bar" :style="{ height: `${bar}%` }"></span>
          </div>
          <div v-else class="gauge" aria-hidden="true">
            <span></span>
          </div>
        </button>
      </section>
    </section>

    <section class="search-panel">
      <div class="search-box">
        <span aria-hidden="true">⌕</span>
        <input v-model="searchKeyword" type="search" placeholder="궁금한 채권명, ISIN, 테마를 검색하세요" />
        <button type="button" @click="searchBonds">검색</button>
      </div>

      <div class="tag-row" aria-label="인기 검색어">
        <button type="button">#국고채</button>
        <button type="button">#고수익</button>
        <button type="button">#안전제일</button>
        <button type="button">#콜옵션</button>
      </div>

      <button class="accordion-trigger" type="button" @click="filtersOpen = !filtersOpen">
        검색 필터
        <span>{{ filtersOpen ? '접기' : '펼치기' }}</span>
      </button>

      <div v-if="filtersOpen" class="filter-grid">
        <fieldset v-for="group in filterGroups" :key="group.key" class="filter-group">
          <legend>{{ group.label }}</legend>
          <label v-for="option in group.options" :key="option" class="filter-chip">
            <input v-model="selectedFilters[group.key]" type="checkbox" :value="option" />
            <span>{{ option }}</span>
          </label>
        </fieldset>
      </div>
    </section>

    <section class="curation-section">
      <div class="section-title">
        <h2 v-if="!isLoggedIn">채권이지의 투자 성향 필터 기반 검색 결과</h2>
        <h2 v-else>
          <span class="user-highlight">{{ user.name }}</span> 님과 같은
          <span class="type-highlight">{{ user.type }}</span> 투자자들이 많이 본 정보
        </h2>
        <button type="button" @click="$emit('navigate', 'market')">전체 보기</button>
      </div>
      <div v-if="!isLoggedIn" class="guest-prompt">
        <p>로그인하시면 나의 투자 성향에 맞춘 채권 정보를 확인하실 수 있습니다.</p>
        <button class="btn-login-link" type="button" @click="$emit('navigate', 'profile')">로그인하러 가기</button>
      </div>
      <div class="swipe-row">
        <article v-for="bond in curatedBonds" :key="bond.code" class="bond-card-mini">
          <div class="card-header">
            <span class="type-tag">{{ bond.type }}</span>
            <span class="rating-tag" :class="bond.ratingGroup">{{ bond.rating }}</span>
          </div>
          <h3>{{ bond.name }}</h3>
          <div class="card-footer">
            <div class="yield-info">
              <span class="label">수수료차감전 수익률</span>
              <span class="value">{{ bond.buyYield }}</span>
            </div>
            <button class="btn-more" type="button" @click="$emit('navigate', 'detail')">상세보기</button>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>

<style scoped>
.user-highlight {
  color: var(--primary);
}
.type-highlight {
  color: var(--accent);
}
.guest-prompt {
  background: var(--surface-soft);
  padding: 16px 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.guest-prompt p {
  font-size: 14px;
  color: var(--muted);
  margin: 0;
}
.btn-login-link {
  background: white;
  border: 1px solid var(--line);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
}

.bond-card-mini {
  flex: 0 0 280px;
  background: white;
  padding: 20px;
  border-radius: 16px;
  border: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  transition: transform 0.2s, box-shadow 0.2s;
}

.bond-card-mini:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type-tag {
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  background: var(--surface-soft);
  padding: 2px 8px;
  border-radius: 4px;
}

.rating-tag {
  font-size: 11px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 4px;
}

.rating-tag.AAA { color: #1f5f9f; background: #ebf3fb; }
.rating-tag.AA { color: #127c57; background: #e7f6f0; }
.rating-tag.A { color: #d98c31; background: #fff7ec; }

.bond-card-mini h3 {
  font-size: 16px;
  font-weight: 700;
  line-height: 1.4;
  margin: 0;
  height: 2.8em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-top: auto;
}

.yield-info {
  display: flex;
  flex-direction: column;
}

.yield-info .label {
  font-size: 11px;
  color: var(--muted);
}

.yield-info .value {
  font-size: 18px;
  font-weight: 800;
  color: var(--primary);
}

.btn-more {
  background: transparent;
  border: 1px solid var(--line);
  font-size: 12px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 8px;
  color: var(--text);
}
</style>
