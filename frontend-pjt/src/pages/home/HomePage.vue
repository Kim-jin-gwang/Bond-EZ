<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { fetchBonds, fetchFilterOptions, fetchCuratedBonds } from '../../api/bonds'
import { fetchIndicators } from '../../api/indicators'
import { createEmptyBondFilters } from '../../composables/useBondFilter'

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
  ...createEmptyBondFilters(),
})

const filterGroups = ref([
  {
    key: 'bondTypes',
    label: '채권 종류',
    options: [
      { value: '국채', label: '국채' },
      { value: '회사채', label: '회사채' },
      { value: '금융채', label: '금융채' },
    ],
  },
  {
    key: 'maturities',
    label: '만기',
    options: [
      { value: '1년 이하', label: '1년 이하' },
      { value: '1~3년', label: '1~3년' },
      { value: '3~5년', label: '3~5년' },
      { value: '5~10년', label: '5~10년' },
      { value: '10년 이상', label: '10년 이상' },
    ],
  },
  {
    key: 'couponRates',
    label: '표면금리',
  },
  {
    key: 'ratings',
    label: '신용등급',
    options: [
      { value: 'AAA', label: 'AAA' },
      { value: 'AA', label: 'AA' },
      { value: 'A', label: 'A' },
      { value: 'BBB', label: 'BBB' },
    ],
  },
  {
    key: 'interestCycles',
    label: '이자 지급 주기',
    options: [
      { value: '1개월', label: '1개월' },
      { value: '2개월', label: '2개월' },
      { value: '3개월', label: '3개월' },
      { value: '6개월', label: '6개월' },
      { value: '12개월', label: '12개월' },
      { value: '만기일시', label: '만기일시' },
    ],
  },
  {
    key: 'optionTypes',
    label: '옵션',
    options: [
      { value: 'CALL', label: 'CALL' },
      { value: 'PUT', label: 'PUT' },
      { value: '없음', label: '없음' },
    ],
  },
  {
    key: 'seniorities',
    label: '선후순위',
    options: [
      { value: '선순위', label: '선순위' },
      { value: '후순위', label: '후순위' },
    ],
  },
  {
    key: 'guaranteeStatuses',
    label: '보증 여부',
    options: [],
  },
])

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

const curatedBonds = ref([])

async function loadCuratedBonds() {
  try {
    const items = await fetchCuratedBonds()
    curatedBonds.value = items || []
  } catch (err) {
    console.error('Failed to load curated bonds:', err)
  }
}

watch(() => props.isLoggedIn, () => {
  loadCuratedBonds()
})

function cloneFilters() {
  return Object.fromEntries(
    Object.entries(selectedFilters.value).map(([key, values]) => [
      key,
      Array.isArray(values) ? [...values] : values,
    ]),
  )
}

function searchBonds() {
  emit('navigate', 'market', {
    source: 'search',
    keyword: searchKeyword.value.trim(),
    filters: cloneFilters(),
  })
}

function clickHashtag(tag) {
  selectedFilters.value = createEmptyBondFilters()
  searchKeyword.value = ''

  if (tag === '국고채') {
    searchKeyword.value = '국고채'
  } else if (tag === '고수익') {
    selectedFilters.value.minCoupon = 4
  } else if (tag === '안정형') {
    selectedFilters.value.ratings = ['AAA', 'AA']
  } else if (tag === '콜옵션') {
    selectedFilters.value.optionTypes = ['CALL']
  } else if (tag === '월배당') {
    selectedFilters.value.interestCycles = ['1개월']
  } else if (tag === '단기채') {
    selectedFilters.value.maturities = ['1년 이하']
  } else if (tag === '회사채') {
    selectedFilters.value.bondTypes = ['일반회사채']
  }

  searchBonds()
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

function clearGroupFilter(key) {
  if (key === 'couponRates') {
    selectedFilters.value.minCoupon = ''
    selectedFilters.value.maxCoupon = ''
  } else {
    selectedFilters.value[key] = []
  }
}

async function loadFilterOptions() {
  try {
    const data = await fetchFilterOptions()
    if (!data) return

    const groups = JSON.parse(JSON.stringify(filterGroups.value))

    if (data.bond_types && data.bond_types.length) {
      const group = groups.find(g => g.key === 'bondTypes')
      if (group) {
        group.options = data.bond_types.map(t => ({
          value: t.bond_type,
          label: t.bond_type,
        }))
      }
    }

    if (data.credit_ratings && data.credit_ratings.length) {
      const group = groups.find(g => g.key === 'ratings')
      if (group) {
        const uniqueGroups = Array.from(
          new Set(
            data.credit_ratings.map(r => r.rating_name.replace(/[+-0-9]/g, '').trim())
          )
        ).filter(Boolean)
        
        group.options = uniqueGroups.map(name => ({
          value: name,
          label: name,
        }))
      }
    }

    if (data.seniorities && data.seniorities.length) {
      const group = groups.find(g => g.key === 'seniorities')
      if (group) {
        group.options = data.seniorities.map(s => ({
          value: s.seniority_name,
          label: s.seniority_name,
        }))
      }
    }

    if (data.guarantee_statuses && data.guarantee_statuses.length) {
      const group = groups.find(g => g.key === 'guaranteeStatuses')
      if (group) {
        group.options = data.guarantee_statuses.map(g => ({
          value: g.guarantee_status,
          label: g.guarantee_status,
        }))
      }
    }

    filterGroups.value = groups
  } catch (err) {
    console.error('Failed to load filter options:', err)
  }
}

onMounted(async () => {
  loadFilterOptions()
  const [remoteBonds, remoteIndicators] = await Promise.all([
    fetchBonds(),
    fetchIndicators(),
  ])

  bonds.value = remoteBonds.items || []
  indicators.value = remoteIndicators

  await loadCuratedBonds()
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
          <button type="button" @click="clickHashtag('국고채')">#국고채</button>
          <button type="button" @click="clickHashtag('고수익')">#고수익</button>
          <button type="button" @click="clickHashtag('안정형')">#안정형</button>
          <button type="button" @click="clickHashtag('콜옵션')">#콜옵션</button>
          <button type="button" @click="clickHashtag('월배당')">#월배당</button>
          <button type="button" @click="clickHashtag('단기채')">#단기채</button>
          <button type="button" @click="clickHashtag('회사채')">#회사채</button>
        </div>

        <button class="accordion-trigger" type="button" @click="filtersOpen = !filtersOpen">
          상세 필터
          <span>{{ filtersOpen ? '접기' : '펼치기' }}</span>
        </button>

        <div v-if="filtersOpen" class="filter-grid">
          <fieldset v-for="group in filterGroups" :key="group.key" class="filter-group">
            <legend>{{ group.label }}</legend>
            <template v-if="group.key === 'couponRates'">
              <div class="coupon-range-wrapper">
                <label class="filter-chip">
                  <input
                    type="checkbox"
                    :checked="selectedFilters.minCoupon === '' && selectedFilters.maxCoupon === ''"
                    @change="clearGroupFilter('couponRates')"
                  />
                  <span>전체</span>
                </label>
                <div class="coupon-range-inputs">
                  <input
                    type="number"
                    v-model.number="selectedFilters.minCoupon"
                    placeholder="최소 (%)"
                    step="0.1"
                    min="0"
                    class="coupon-input"
                  />
                  <span class="range-separator">~</span>
                  <input
                    type="number"
                    v-model.number="selectedFilters.maxCoupon"
                    placeholder="최대 (%)"
                    step="0.1"
                    min="0"
                    class="coupon-input"
                  />
                </div>
              </div>
            </template>
            <template v-else>
              <label class="filter-chip">
                <input
                  type="checkbox"
                  :checked="selectedFilters[group.key].length === 0"
                  @change="clearGroupFilter(group.key)"
                />
                <span>전체</span>
              </label>
              <label v-for="option in group.options" :key="option.value" class="filter-chip">
                <input v-model="selectedFilters[group.key]" type="checkbox" :value="option.value" />
                <span>{{ option.label }}</span>
              </label>
            </template>
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
          <h2 v-if="!isLoggedIn">관심있을만한 채권이에요</h2>
          <h2 v-else>
            <span class="user-highlight">{{ user.name }}</span>님이 관심있을만한 채권이에요
          </h2>
        </div>
        <button type="button" @click="$emit('navigate', 'market', { source: 'curated' })">전체 보기</button>
      </div>
      <div v-if="!isLoggedIn" class="guest-prompt">
        <p>로그인하면 투자 성향과 관심 조건에 맞춘 채권 후보를 더 정교하게 볼 수 있습니다.</p>
        <button class="btn-login-link" type="button" @click="$emit('navigate', 'profile')">로그인</button>
      </div>
      
      <div class="curated-list">
        <div v-if="curatedBonds.length === 0" class="empty-curated">
          추천 채권 데이터를 불러오고 있습니다.
        </div>
        <article v-else v-for="bond in curatedBonds.slice(0, 10)" :key="bond.code" class="curated-bond-item">
          <div class="bond-item-row" @click="$emit('navigate', 'detail', { bond })">
            <div class="bond-item-main">
              <div class="bond-item-meta">
                <span class="type-tag">{{ bond.type }}</span>
                <span class="rating-tag" :class="bond.ratingGroup">{{ bond.rating }}</span>
              </div>
              <strong class="bond-item-title">{{ bond.name }}</strong>
              <div class="bond-item-details">
                <span>만기: <strong>{{ bond.maturity }}</strong></span>
                <span>이자 주기: <strong>{{ bond.interestCycle }}</strong></span>
                <span>표면 금리: <strong>{{ bond.coupon }}</strong></span>
              </div>
            </div>
            <div class="bond-item-action">
              <div class="yield-badge">
                <span class="label">매수수익률</span>
                <span class="value">{{ bond.buyYield }}</span>
              </div>
              <button class="btn-more-detail" type="button">상세정보</button>
            </div>
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

.curated-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-curated {
  padding: 32px 0;
  text-align: center;
  color: var(--muted);
  font-size: 14px;
}

.curated-bond-item {
  border: 1px solid var(--line, #e2e8f0);
  border-radius: 8px;
  background: #fbfdff;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.curated-bond-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(23, 43, 59, 0.06);
  border-color: rgba(59, 130, 246, 0.3);
}

.bond-item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  gap: 20px;
  cursor: pointer;
}

.bond-item-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  flex: 1;
}

.bond-item-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.bond-item-meta .type-tag,
.bond-item-meta .rating-tag {
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
  font-weight: 800;
}

.bond-item-meta .type-tag {
  color: var(--muted);
  background: var(--surface-soft);
}

.bond-item-meta .rating-tag.AAA { color: #1f5f9f; background: #ebf3fb; }
.bond-item-meta .rating-tag.AA { color: #127c57; background: #e7f6f0; }
.bond-item-meta .rating-tag.A { color: #d98c31; background: #fff7ec; }
.bond-item-meta .rating-tag.BBB { color: #b42318; background: #fef2f2; }

.bond-item-title {
  font-size: 16px;
  font-weight: 800;
  color: var(--text, #1e293b);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bond-item-details {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 12px;
  color: var(--muted);
}

.bond-item-details span strong {
  color: var(--text);
}

.bond-item-action {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.bond-item-action .yield-badge {
  display: flex;
  flex-direction: column;
  text-align: right;
}

.bond-item-action .yield-badge .label {
  font-size: 11px;
  color: var(--muted);
}

.bond-item-action .yield-badge .value {
  font-size: 18px;
  font-weight: 900;
  color: var(--primary);
}

.btn-more-detail {
  min-height: 38px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 14px;
  color: var(--text);
  background: white;
  font-weight: 800;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn-more-detail:hover {
  border-color: var(--primary);
  color: var(--primary);
}

@media (max-width: 768px) {
  .bond-item-row {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .bond-item-action {
    justify-content: space-between;
    border-top: 1px solid var(--line);
    padding-top: 10px;
    width: 100%;
  }
  .bond-item-action .yield-badge {
    text-align: left;
  }
}
</style>
