<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchBonds } from '../../api/bonds'
import { fetchIndicators } from '../../api/indicators'

const bonds = ref([])
const indicators = ref([])

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
const indicatorCarousel = ref(null)
const searchKeyword = ref('')
const selectedFilters = ref({
  bondTypes: ['국채'],
  maturities: [],
  yields: [],
  ratings: [],
  interestCycles: [],
})

const filterGroups = [
  { key: 'bondTypes', label: '채권 종류', options: ['국채', '회사채', '금융채'] },
  { key: 'maturities', label: '만기', options: ['1년 이하', '1~3년', '3~5년', '5~10년', '10년 이상'] },
  { key: 'yields', label: '수익률', options: ['3% 이상', '4% 이상', '5% 이상', '6% 이상'] },
  { key: 'ratings', label: '신용등급', options: ['AAA', 'AA', 'A', 'BBB'] },
  { key: 'interestCycles', label: '이자 지급 주기', options: ['3개월', '6개월', '12개월', '만기일시'] },
]

const homeIndicatorCards = computed(() => {
  if (!indicators.value.length) {
    return []
  }

  const treasury = indicators.value.find((indicator) => indicator.id === 'treasury-rate')
  const spread = indicators.value.find((indicator) => indicator.id === 'yield-spread')
  const credit = indicators.value.find((indicator) => indicator.id === 'credit-rating-yield')
  const deposit = indicators.value.find((indicator) => indicator.id === 'deposit-compare')
  const centralBank = indicators.value.find((indicator) => indicator.id === 'central-bank-rate')
  const centralRateByCountry = Object.fromEntries(
    (centralBank?.tableRows || []).map((row) => [row[0], row[1]]),
  )

  return [
    treasury && {
      ...treasury,
      title: '나라별 금리',
      variant: 'table',
      rows: (treasury?.treasuryRates || []).map((row) => [
        row.country,
        `${centralRateByCountry[row.country] || '-'} / ${formatRate(row.rate3y)} / ${formatRate(row.rate10y)}`,
      ]),
      caption: '기준금리 / 3Y / 10Y',
    },
    spread && {
      ...spread,
      title: '장단기 금리차',
      variant: 'table',
      rows: (spread?.tableRows || []).slice(0, 3).map((row) => [row[0], row[1]]),
      caption: '10년물 - 3년물',
    },
    credit && {
      ...credit,
      title: '신용 등급 금리',
      variant: 'table',
      rows: buildCreditSummaryRows(credit?.tableRows || [], ['국채', 'AAA', 'BBB']),
      caption: credit?.caption || '국채 기준',
    },
    deposit && {
      ...deposit,
      title: '예금 금리 비교',
      variant: 'table',
      rows: [...(deposit?.tableRows || [])]
        .sort((a, b) => parsePercent(b[3] || b[2]) - parsePercent(a[3] || a[2]))
        .slice(0, 3)
        .map((row) => [row[0], row[3] || row[2]]),
      caption: '예금 금리',
    },
].filter(Boolean)
})

function formatRate(value) {
  return Number.isFinite(value) ? `${value.toFixed(2)}%` : '-'
}

function parsePercent(value) {
  const number = Number(String(value ?? '').replace(/[^0-9.-]/g, ''))
  return Number.isFinite(number) ? number : -Infinity
}

function buildCreditSummaryRows(rows, labels) {
  return labels
    .map((label) => rows.find((row) => normalizeCreditLabel(row[0]) === label))
    .map((row) => row && [normalizeCreditLabel(row[0]), row[1]])
    .filter(Boolean)
}

function normalizeCreditLabel(value) {
  const label = String(value ?? '').trim()
  if (label === '국채') return '국채'
  if (label.startsWith('AAA')) return 'AAA'
  if (label.startsWith('BBB')) return 'BBB'
  return label.replace(/[+-]$/, '').replace(/\d+$/, '')
}

const curatedBonds = computed(() => {
  if (!props.isLoggedIn) {
    return bonds.value.slice(0, 4)
  }

  if (props.user.type === '안정추구형') {
    return bonds.value.filter((bond) => bond.type === '국채' || bond.ratingGroup === 'AAA').slice(0, 4)
  }

  if (props.user.type === '공격투자형') {
    return [...bonds.value].sort((a, b) => b.yieldValue - a.yieldValue).slice(0, 4)
  }

  return bonds.value.slice(0, 4)
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

function scrollIndicators(direction) {
  const carousel = indicatorCarousel.value

  if (!carousel) {
    return
  }

  const card = carousel.querySelector('.metric-card')
  const distance = card ? card.offsetWidth + 16 : 280

  carousel.scrollBy({
    left: direction * distance,
    behavior: 'smooth',
  })
}

onMounted(async () => {
  const [remoteBonds, remoteIndicators] = await Promise.all([
    fetchBonds(),
    fetchIndicators(),
  ])

  bonds.value = remoteBonds
  indicators.value = remoteIndicators
})
</script>

<template>
  <section class="page home-page">
    <section class="home-hero" aria-labelledby="home-title">
      <div class="hero-copy">
        <p class="eyebrow">BondEZ Market Desk</p>
        <h1 id="home-title">처음 보는 채권도, 투자 후보처럼 비교하세요.</h1>
        <p>
          금리 지표, 신용등급, 만기, 이자 주기까지 채권 투자 판단에 필요한 정보를
          한 화면에서 정리해 드립니다.
        </p>

        <div class="hero-actions">
          <button class="primary-action" type="button" @click="$emit('navigate', 'market')">
            채권 시세 보기
          </button>
          <button class="secondary-action" type="button" @click="$emit('navigate', 'guide', 'what')">
            채권 가이드
          </button>
        </div>
      </div>

    </section>

    <section class="quick-search-section">
      <div class="search-panel search-panel-elevated">
        <div class="search-panel-heading">
          <div>
            <p class="eyebrow">Bond Screener</p>
            <h2>조건으로 바로 찾기</h2>
          </div>
          <button class="text-action" type="button" @click="$emit('navigate', 'market')">전체 목록</button>
        </div>

        <div class="search-box">
          <span aria-hidden="true">⌕</span>
          <input v-model="searchKeyword" type="search" placeholder="채권명, ISIN, 테마를 검색하세요" />
          <button type="button" @click="searchBonds">검색</button>
        </div>

        <div class="tag-row" aria-label="인기 검색어">
          <button type="button" @click="searchKeyword = '국고채'">#국고채</button>
          <button type="button" @click="searchKeyword = '고수익'">#고수익</button>
          <button type="button" @click="searchKeyword = '안정형'">#안정형</button>
          <button type="button" @click="searchKeyword = '콜옵션'">#콜옵션</button>
        </div>

        <button class="accordion-trigger" type="button" @click="filtersOpen = !filtersOpen">
          상세 필터
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
      </div>
    </section>

    <section class="market-indicator-section">
      <div class="section-title">
        <div>
          <p class="eyebrow">Rates & Signals</p>
          <h2>투자 판단 지표</h2>
        </div>
        <button type="button" @click="$emit('navigate', 'indicators')">자세히 보기</button>
      </div>
      <div class="indicator-carousel-shell">
        <!--
        <button
          class="carousel-control prev"
          type="button"
          aria-label="이전 지표 보기"
          @click="scrollIndicators(-1)"
        >
          ‹
        </button>
        -->
        <section
          ref="indicatorCarousel"
          class="indicator-grid home-indicator-carousel"
          aria-label="투자 지표 요약"
        >
          <button
            v-for="indicator in homeIndicatorCards"
            :key="indicator.title"
            class="metric-card"
            type="button"
            @click="$emit('navigate', 'indicators', indicator.id)"
          >
            <span class="card-title">{{ indicator.title }}</span>
            <template v-if="indicator.variant === 'table'">
              <table class="mini-rate-table">
                <tbody>
                  <tr v-for="row in indicator.rows" :key="row[0]">
                    <th scope="row">{{ row[0] }}</th>
                    <td>{{ row[1] }}</td>
                  </tr>
                </tbody>
              </table>
              <span class="card-caption">{{ indicator.caption }}</span>
            </template>

            <template v-else>
              <strong>{{ indicator.value }}</strong>
              <span class="card-caption">{{ indicator.caption }}</span>
            </template>
          </button>
        </section>
        <!--
        <button
          class="carousel-control next"
          type="button"
          aria-label="다음 지표 보기"
          @click="scrollIndicators(1)"
        >
          ›
        </button>
        -->
      </div>
    </section>

    <section class="curation-section">
      <div class="section-title">
        <div>
          <p class="eyebrow">Curated Bonds</p>
          <h2 v-if="!isLoggedIn">초보 투자자가 먼저 볼 만한 채권</h2>
          <h2 v-else>
            <span class="user-highlight">{{ user.name }}</span> 님의
            <span class="type-highlight">{{ user.type }}</span> 성향 추천
          </h2>
        </div>
        <button type="button" @click="$emit('navigate', 'market')">전체 보기</button>
      </div>
      <div v-if="!isLoggedIn" class="guest-prompt">
        <p>로그인하면 투자 성향과 관심 조건에 맞춘 채권 후보를 더 정교하게 볼 수 있습니다.</p>
        <button class="btn-login-link" type="button" @click="$emit('navigate', 'profile')">로그인</button>
      </div>
      <div class="swipe-row">
        <article v-for="bond in curatedBonds" :key="bond.code" class="bond-card-mini">
          <div class="card-header">
            <span class="type-tag">{{ bond.type }}</span>
            <span class="rating-tag" :class="bond.ratingGroup">{{ bond.rating }}</span>
          </div>
          <h3>{{ bond.name }}</h3>
          <dl class="bond-meta">
            <div>
              <dt>만기</dt>
              <dd>{{ bond.maturity }}</dd>
            </div>
            <div>
              <dt>이자 주기</dt>
              <dd>{{ bond.interestCycle }}</dd>
            </div>
          </dl>
          <div class="card-footer">
            <div class="yield-info">
              <span class="label">매수수익률</span>
              <span class="value">{{ bond.buyYield }}</span>
            </div>
            <button class="btn-more" type="button" @click="$emit('navigate', 'detail', { bond })">상세</button>
          </div>
        </article>
      </div>
    </section>

    <section class="guide-strip">
      <div>
        <p class="eyebrow">Bond Basics</p>
        <h2>채권이 낯설다면, 개념부터 짧게 정리해 보세요.</h2>
      </div>
      <div class="guide-actions">
        <button type="button" @click="$emit('navigate', 'dictionary')">용어 사전</button>
        <button type="button" @click="$emit('navigate', 'guide', 'risk')">투자 위험 보기</button>
      </div>
    </section>
  </section>
</template>

<style scoped>
.home-page {
  display: grid;
  gap: 34px;
}

.home-page > * {
  width: 100%;
  max-width: 100%;
  min-width: 0;
}

.home-indicator-carousel {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.home-indicator-carousel::-webkit-scrollbar {
  display: none;
}

.indicator-carousel-shell {
  position: relative;
  display: block;
}

.carousel-control {
  display: grid;
  place-items: center;
  width: 28px;
  height: 190px;
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--primary-dark);
  background: white;
  box-shadow: 0 8px 20px rgba(23, 43, 59, 0.06);
  font-size: 24px;
  font-weight: 800;
  line-height: 1;
}

.carousel-control:hover {
  border-color: var(--primary);
  color: white;
  background: var(--primary);
}

.home-indicator-carousel .metric-card {
  width: 100%;
  min-height: 190px;
}

.mini-rate-table {
  width: 100%;
  min-width: 0;
  margin-top: 6px;
  border-collapse: collapse;
  background: white;
}

.mini-rate-table th,
.mini-rate-table td {
  padding: 9px 10px;
  border: 1px solid var(--line);
  font-size: 13px;
}

.mini-rate-table th {
  width: 52%;
  color: var(--text);
  background: #f8fafc;
  font-weight: 800;
}

.mini-rate-table td {
  color: var(--primary-dark);
  text-align: right;
  font-weight: 900;
  white-space: nowrap;
}

.home-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 28px;
  align-items: stretch;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 300px;
  padding: clamp(22px, 3.2vw, 36px);
  border: 1px solid rgba(31, 111, 120, 0.18);
  border-radius: 8px;
  background:
    radial-gradient(circle at 12% 18%, rgba(31, 111, 120, 0.16), transparent 26%),
    linear-gradient(135deg, #ffffff 0%, #f4f8fb 46%, #eef4f8 100%);
  box-shadow: 0 24px 70px rgba(23, 43, 59, 0.1);
}

.hero-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 1040px;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.hero-copy h1 {
  margin-bottom: 18px;
  color: #162330;
  font-size: clamp(32px, 4.2vw, 52px);
  line-height: 1.12;
  overflow-wrap: break-word;
  white-space: nowrap;
}

.hero-copy p:not(.eyebrow) {
  max-width: 980px;
  font-size: 18px;
  line-height: 1.7;
  white-space: nowrap;
}

.hero-actions,
.guide-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 22px;
}

.primary-action,
.secondary-action,
.guide-actions button,
.text-action {
  min-height: 44px;
  border-radius: 8px;
  padding: 0 18px;
  font-weight: 800;
}

.primary-action {
  border: 1px solid var(--primary);
  color: white;
  background: var(--primary);
}

.secondary-action,
.guide-actions button,
.text-action {
  border: 1px solid var(--line);
  color: var(--text);
  background: white;
}

.search-panel-heading {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.search-panel-elevated {
  margin-top: 0;
}

.search-panel-heading {
  margin-bottom: 16px;
}

.search-panel-heading h2 {
  margin: 0;
}

.text-action {
  min-height: 38px;
  padding: 0 14px;
}

.user-highlight {
  color: var(--primary);
}

.type-highlight {
  color: var(--accent);
}

.guest-prompt {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.guest-prompt p {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
}

.btn-login-link {
  min-height: 36px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 14px;
  background: white;
  font-size: 13px;
  font-weight: 800;
}

.bond-card-mini {
  display: flex;
  flex: 0 0 280px;
  flex-direction: column;
  gap: 14px;
  min-height: 230px;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
  box-shadow: var(--shadow);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.bond-card-mini:hover {
  transform: translateY(-4px);
  box-shadow: 0 18px 42px rgba(23, 43, 59, 0.12);
}

.card-header,
.card-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.type-tag,
.rating-tag {
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 800;
}

.type-tag {
  color: var(--muted);
  background: var(--surface-soft);
}

.rating-tag.AAA { color: #1f5f9f; background: #ebf3fb; }
.rating-tag.AA { color: #127c57; background: #e7f6f0; }
.rating-tag.A { color: #d98c31; background: #fff7ec; }

.bond-card-mini h3 {
  display: -webkit-box;
  min-height: 2.8em;
  margin: 0;
  overflow: hidden;
  font-size: 16px;
  font-weight: 800;
  line-height: 1.4;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.bond-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 0;
  padding: 12px;
  border-radius: 8px;
  background: var(--surface-soft);
}

.bond-meta dt,
.bond-meta dd {
  margin: 0;
}

.bond-meta dt,
.yield-info .label {
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
}

.bond-meta dd {
  margin-top: 4px;
  font-size: 13px;
  font-weight: 800;
}

.yield-info {
  display: flex;
  flex-direction: column;
}

.yield-info .value {
  color: var(--primary);
  font-size: 20px;
  font-weight: 900;
}

.btn-more {
  min-height: 36px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 12px;
  color: var(--text);
  background: transparent;
  font-size: 12px;
  font-weight: 800;
}

.guide-strip {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
  padding: 26px;
  border: 1px solid rgba(217, 140, 49, 0.28);
  border-radius: 8px;
  background: #fff9f0;
}

.guide-strip h2 {
  margin-bottom: 0;
}

@media (max-width: 960px) {
  .home-hero {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .home-indicator-carousel {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .guide-strip {
    display: grid;
    align-items: stretch;
  }
}

@media (max-width: 640px) {
  .home-page {
    gap: 24px;
  }

  .home-hero {
    padding: 20px;
  }

  .home-indicator-carousel {
    grid-template-columns: 1fr;
  }

  .hero-copy p:not(.eyebrow) {
    font-size: 16px;
    white-space: normal;
  }

  .hero-copy h1 {
    white-space: normal;
  }

  .hero-panel {
    padding: 16px;
  }

  .panel-header,
  .search-panel-heading,
  .guest-prompt,
  .card-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .hero-actions,
  .hero-actions button,
  .guide-actions,
  .guide-actions button {
    width: 100%;
  }
}
</style>
