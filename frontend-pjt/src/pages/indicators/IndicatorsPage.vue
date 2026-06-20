<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchIndicators } from '../../api/indicators'

const indicators = ref([])

const props = defineProps({
  selectedIndicatorId: {
    type: String,
    default: 'treasury-rate',
  },
})

const emit = defineEmits(['navigate'])

const activeIndicator = computed(() => {
  return indicators.value.find((indicator) => indicator.id === props.selectedIndicatorId) ?? indicators.value[0]
})

const visibleIndicators = computed(() =>
  ['treasury-rate', 'yield-spread', 'yield-curve', 'credit-rating-yield', 'deposit-compare']
    .map((id) => indicators.value.find((indicator) => indicator.id === id))
    .filter(Boolean),
)
const treasuryIndicator = computed(() => indicators.value.find((indicator) => indicator.id === 'treasury-rate'))
const centralBankIndicator = computed(() => indicators.value.find((indicator) => indicator.id === 'central-bank-rate'))
const yieldSpreadIndicator = computed(() => indicators.value.find((indicator) => indicator.id === 'yield-spread'))
const isRateDashboard = computed(() =>
  activeIndicator.value?.id === 'treasury-rate' || activeIndicator.value?.id === 'central-bank-rate',
)

const creditRateView = ref('rates')
const creditBaseDate = ref('2024-10-16')

const gradedRateColumns = ['등급', '2021.12.31', '2022.12.30', '2023.12.29', '2024.10.02', '2024.10.08', '2024.10.16']
const gradedRateRows = [
  ['AAA', '2.30', '4.99', '3.68', '3.24', '3.37', '3.30'],
  ['AA+', '2.35', '5.11', '3.78', '3.30', '3.44', '3.38'],
  ['AA', '2.38', '5.14', '3.82', '3.33', '3.46', '3.40'],
  ['AA-', '2.41', '5.22', '3.89', '3.37', '3.50', '3.44'],
  ['A+', '2.57', '5.48', '4.54', '3.71', '3.86', '3.80'],
  ['A', '2.84', '5.74', '4.80', '3.97', '4.12', '4.06'],
  ['A-', '3.29', '6.18', '5.25', '4.40', '4.55', '4.49'],
  ['BBB+', '5.86', '8.73', '7.91', '6.82', '6.97', '6.91'],
  ['BBB', '6.91', '9.78', '8.95', '7.87', '8.02', '7.96'],
  ['BBB-', '8.28', '11.15', '10.32', '9.25', '9.40', '9.34'],
]

const spreadColumns = ['등급', '3월', '6월', '9월', '1년', '1년 6개월', '2년', '3년', '5년']
const spreadRows = [
  ['국고채', '3.07', '2.95', '2.94', '2.86', '2.92', '2.90', '2.88', '2.92'],
  ['AAA', '0.38', '0.45', '0.39', '0.38', '0.33', '0.37', '0.42', '0.42'],
  ['AA+', '0.40', '0.47', '0.41', '0.39', '0.35', '0.41', '0.50', '0.49'],
  ['AA', '0.41', '0.48', '0.43', '0.42', '0.39', '0.43', '0.52', '0.55'],
  ['AA-', '0.43', '0.51', '0.45', '0.44', '0.41', '0.47', '0.56', '0.65'],
  ['A+', '0.45', '0.58', '0.62', '0.68', '0.67', '0.72', '0.92', '1.38'],
  ['A', '0.55', '0.71', '0.79', '0.85', '0.83', '0.90', '1.18', '1.79'],
  ['A-', '0.78', '0.97', '1.05', '1.11', '1.13', '1.22', '1.61', '2.40'],
  ['BBB+', '1.23', '1.67', '2.06', '2.35', '2.76', '3.33', '4.03', '4.37'],
  ['BBB', '1.63', '2.20', '2.67', '3.05', '3.57', '4.28', '5.08', '5.41'],
  ['BBB-', '2.30', '3.01', '3.62', '4.04', '4.69', '5.45', '6.46', '6.85'],
]

const creditTableColumns = computed(() => creditRateView.value === 'rates' ? gradedRateColumns : spreadColumns)
const creditTableRows = computed(() => creditRateView.value === 'rates' ? gradedRateRows : spreadRows)

const barRows = computed(() => {
  const rows = activeIndicator.value?.tableRows || []
  const bars = activeIndicator.value?.bars || []

  return rows.map((row, index) => ({
    label: row[0],
    value: row[1],
    height: bars[index] || 42,
    description: row[row.length - 1],
  }))
})

const chartGuide = computed(() => activeIndicator.value?.chartGuide ?? {
  title: '그래프 읽는 법',
  unit: '단위: %',
  xAxis: '가로축은 비교 대상 또는 시간 흐름입니다.',
  yAxis: '세로축은 수치의 상대적인 크기를 나타냅니다.',
  reading: '표의 수치를 그래프로 시각화한 참고 자료입니다.',
  caution: '그래프는 단일 지표이므로 다른 조건과 함께 해석해야 합니다.',
})

const rateDashboardRows = computed(() => {
  const treasuryRows = treasuryIndicator.value?.treasuryRates || []
  const centralRows = (centralBankIndicator.value?.tableRows || []).map((row) => ({
    country: row[0],
    baseRate: parseRate(row[1]),
    rate3y: parseRate(row[2]),
    rate10y: parseRate(row[3]),
  }))
  const countries = [...new Set([
    ...treasuryRows.map((row) => row.country),
    ...centralRows.map((row) => row.country),
  ])]

  return countries.map((country) => {
    const treasury = treasuryRows.find((row) => row.country === country) || {}
    const central = centralRows.find((row) => row.country === country) || {}
    const rate3y = treasury.rate3y ?? central.rate3y
    const rate10y = treasury.rate10y ?? central.rate10y

    return {
      country,
      baseRate: central.baseRate,
      rate3y,
      rate10y,
      tone: getCountryTone(country),
    }
  })
})

const baseRateSummaryCards = computed(() =>
  rateDashboardRows.value.map((row) => ({
    country: row.country,
    value: formatRate(row.baseRate),
    caption: `3년 ${formatRate(row.rate3y)} · 10년 ${formatRate(row.rate10y)}`,
    tone: row.tone,
  })),
)

const rateSpreadSummaryCards = computed(() =>
  yieldSpreadRows.value.map((row) => ({
    country: row.country,
    value: row.value,
    state: row.state,
    tone: row.tone,
    isNegative: row.spread < 0,
  })),
)

const rateDashboardInterpretation = computed(() => {
  const rows = rateDashboardRows.value
  const korea = rows.find((row) => row.country.includes('한국') || row.country.includes('대한민국'))
  const us = rows.find((row) => row.country.includes('미국'))
  const japan = rows.find((row) => row.country.includes('일본'))
  const highestBaseRate = rows
    .filter((row) => Number.isFinite(row.baseRate))
    .sort((a, b) => b.baseRate - a.baseRate)[0]

  return [
    highestBaseRate
      ? `${highestBaseRate.country}의 기준금리가 가장 높아 통화정책이 상대적으로 긴축적인 상태로 보입니다.`
      : '기준금리 데이터가 충분하지 않아 국가 간 통화정책 강도를 비교하기 어렵습니다.',
    korea && us && Number.isFinite(korea.rate10y) && Number.isFinite(us.rate10y)
      ? `한국 10년 금리는 미국 10년 금리보다 ${Math.abs(us.rate10y - korea.rate10y).toFixed(2)}%p 낮아, 장기 금리 수준은 미국이 더 높게 형성되어 있습니다.`
      : '한국과 미국의 10년 금리 비교 데이터가 충분하지 않습니다.',
    japan && Number.isFinite(japan.baseRate) && Number.isFinite(japan.rate10y)
      ? '일본은 기준금리와 장기금리 모두 낮은 편이라, 다른 국가보다 완화적인 금리 환경으로 볼 수 있습니다.'
      : '일본 금리 데이터가 충분하지 않습니다.',
    '장단기 금리차는 아래 요약에서 빠르게 확인하고, 0%p 기준의 상세 해석은 장단기 금리차 페이지에서 확인할 수 있습니다.',
  ]
})

const rateDashboardValue = computed(() => {
  const korea = rateDashboardRows.value.find((row) => row.country.includes('한국') || row.country.includes('대한민국'))
  return formatRate(korea?.rate10y ?? rateDashboardRows.value[0]?.rate10y)
})

const yieldSpreadRows = computed(() => {
  const rows = yieldSpreadIndicator.value?.tableRows || []

  return rows.map((row) => {
    const spread = parseRate(row[1])

    return {
      country: row[0],
      spread,
      value: formatRateGap(spread),
      state: getSpreadState(spread),
      tone: getCountryTone(row[0]),
    }
  })
})

const yieldSpreadValue = computed(() => {
  const korea = yieldSpreadRows.value.find((row) => row.country.includes('한국') || row.country.includes('대한민국'))
  return korea?.value ?? yieldSpreadRows.value[0]?.value ?? '-'
})

const yieldSpreadInterpretation = computed(() => {
  const rows = yieldSpreadRows.value
  const positiveRows = rows.filter((row) => Number.isFinite(row.spread) && row.spread > 0)
  const negativeRows = rows.filter((row) => Number.isFinite(row.spread) && row.spread < 0)
  const widest = rows
    .filter((row) => Number.isFinite(row.spread))
    .sort((a, b) => Math.abs(b.spread) - Math.abs(a.spread))[0]

  return [
    positiveRows.length
      ? `${positiveRows.map((row) => row.country).join(', ')}은 10년 금리가 3년 금리보다 높아 일반적인 우상향 금리 구조로 보입니다.`
      : '10년 금리가 3년 금리보다 높은 국가가 없어 장단기 금리 구조가 평탄하거나 역전된 상태로 볼 수 있습니다.',
    negativeRows.length
      ? `${negativeRows.map((row) => row.country).join(', ')}은 장단기 금리차가 마이너스로, 단기 금리가 장기 금리보다 높은 역전 구간입니다.`
      : '현재 표시된 국가들은 장단기 금리차가 모두 플러스라 역전 구간은 보이지 않습니다.',
    widest
      ? `${widest.country}의 금리차가 ${widest.value}로 가장 크게 벌어져 있어, 다른 국가보다 장단기 금리 기울기가 더 뚜렷합니다.`
      : '금리차 데이터가 충분하지 않아 국가별 기울기 차이를 비교하기 어렵습니다.',
    '금리차가 0%p에 가까워질수록 장기와 단기 금리 차이가 작아진 것이며, 경기 기대나 통화정책 전망이 빠르게 바뀔 때 평탄화가 나타날 수 있습니다.',
  ]
})

const treasuryAxisTicks = [10, 5, 0]
const treasuryTerms = [
  { key: 'rate3y', label: '3년 금리' },
  { key: 'rate10y', label: '10년 금리' },
]

function formatRate(value) {
  return Number.isFinite(value) ? `${value.toFixed(2)}%` : '-'
}

function formatRateGap(value) {
  if (!Number.isFinite(value)) return '-'
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%p`
}

function parseRate(value) {
  const number = Number(String(value ?? '').replace(/[^0-9.-]/g, ''))
  return Number.isFinite(number) ? number : null
}

function treasuryBarHeight(rate) {
  return Number.isFinite(rate) ? `${Math.max(4, (rate / 10) * 100)}%` : '4%'
}

function getSpreadState(spread) {
  if (!Number.isFinite(spread)) return '데이터 없음'
  if (spread < 0) return '역전 구간'
  if (isFlatSpread(spread)) return '평탄 구간'
  return '정상 구간'
}

function isFlatSpread(spread) {
  return Number.isFinite(spread) && spread >= 0 && spread <= 0.15
}

function spreadBarStyle(spread) {
  if (!Number.isFinite(spread)) return {}

  const width = Math.min(50, (Math.abs(spread) / 1.5) * 50)
  return spread >= 0
    ? { left: '50%', width: `${width}%` }
    : { right: '50%', width: `${width}%` }
}

function getCountryTone(country) {
  if (country.includes('미국')) return 'us'
  if (country.includes('일본')) return 'jp'
  if (country.includes('한국') || country.includes('대한민국')) return 'kr'
  return 'default'
}

onMounted(async () => {
  indicators.value = await fetchIndicators()
})
</script>

<template>
  <section class="page indicators-detail-page">
    <div class="page-heading compact">
      <p class="eyebrow">Investment Indicators</p>
      <h1>투자 지표 상세 보기</h1>
      <p>금리와 채권 시장을 해석할 때 자주 확인하는 핵심 지표를 표와 그래프로 정리했습니다.</p>
    </div>

    <div class="indicator-nav" aria-label="투자 지표 선택">
      <button
        v-for="indicator in visibleIndicators"
        :key="indicator.id"
        :class="{ active: activeIndicator.id === indicator.id }"
        type="button"
        @click="$emit('navigate', 'indicators', indicator.id)"
      >
        {{ indicator.shortTitle || indicator.title }}
      </button>
    </div>

    <article v-if="activeIndicator && isRateDashboard" class="indicator-detail-card treasury-detail-card">
      <header class="indicator-detail-header">
        <div>
          <p class="eyebrow">Indicator Report</p>
          <h2>나라별 금리</h2>
        </div>
        <div class="indicator-current-value">
          <span>한국 10년물 기준</span>
          <strong>{{ rateDashboardValue }}</strong>
          <small>기준금리와 3년·10년 금리 수준 비교</small>
        </div>
      </header>

      <section class="indicator-explanation">
        <h3>개념 설명</h3>
        <p>국가별 기준금리와 3년·10년 국채 금리를 함께 비교해 통화정책 수준과 금리 수준 차이를 확인합니다.</p>
      </section>

      <section class="indicator-table-panel treasury-table-panel">
        <div class="panel-title">
          <h3>데이터 표</h3>
          <span>{{ rateDashboardRows.length }}개 항목</span>
        </div>
        <div class="indicator-table-wrap">
          <table class="indicator-data-table treasury-rate-table">
            <thead>
              <tr>
                <th>구분</th>
                <th>기준금리</th>
                <th>3년 금리</th>
                <th>10년 금리</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rateDashboardRows" :key="row.country">
                <th scope="row">
                  <span class="country-chip" :class="row.tone">{{ row.country }}</span>
                </th>
                <td>
                  <strong class="rate-cell">{{ formatRate(row.baseRate) }}</strong>
                </td>
                <td>
                  <strong class="rate-cell">{{ formatRate(row.rate3y) }}</strong>
                </td>
                <td>
                  <strong class="rate-cell">{{ formatRate(row.rate10y) }}</strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="base-rate-summary-grid" aria-label="기준금리 데이터 요약">
        <article v-for="card in baseRateSummaryCards" :key="`${card.country}-base-rate`" :class="card.tone">
          <span>{{ card.country }} 기준금리</span>
          <strong>{{ card.value }}</strong>
          <small>{{ card.caption }}</small>
        </article>
      </section>

      <section v-if="rateSpreadSummaryCards.length" class="rate-spread-summary-panel" aria-label="장단기 금리차 요약">
        <div class="panel-title">
          <div>
            <h3>장단기 금리차 요약</h3>
            <p>10년 금리에서 3년 금리를 뺀 값입니다. 상세 해석은 별도 페이지에서 확인합니다.</p>
          </div>
          <button type="button" @click="$emit('navigate', 'indicators', 'yield-spread')">자세히 보기</button>
        </div>
        <div class="rate-spread-summary-grid">
          <article
            v-for="card in rateSpreadSummaryCards"
            :key="`${card.country}-spread-quick`"
            :class="card.tone"
          >
            <span>{{ card.country }}</span>
            <strong :class="{ negative: card.isNegative }">{{ card.value }}</strong>
            <small :class="{ negative: card.isNegative }">{{ card.state }}</small>
          </article>
        </div>
      </section>

      <section class="indicator-chart-panel treasury-chart-panel">
        <div class="panel-title">
          <div>
            <h3>그래프 읽는 법</h3>
            <p>단위: %, 세로축 0~10%</p>
          </div>
          <span>국가별 3년·10년 금리 수준 비교</span>
        </div>

        <div class="treasury-chart-grid" aria-label="한국 미국 일본 3년 10년 금리 그래프">
          <article
            v-for="row in rateDashboardRows"
            :key="`${row.country}-chart`"
            class="treasury-chart-card"
            :class="row.tone"
          >
            <header>
              <strong>{{ row.country }}</strong>
            </header>

            <div class="treasury-bar-chart" :aria-label="`${row.country} 3년 10년 금리 막대 그래프`">
              <div class="treasury-value-row">
                <span v-for="term in treasuryTerms" :key="`${row.country}-${term.key}-value`">
                  {{ formatRate(row[term.key]) }}
                </span>
              </div>
              <div class="treasury-axis" aria-hidden="true">
                <span v-for="tick in treasuryAxisTicks" :key="tick">{{ tick }}%</span>
              </div>
              <div class="treasury-bar-plot">
                <div class="treasury-grid-lines" aria-hidden="true">
                  <span v-for="tick in treasuryAxisTicks" :key="`${row.country}-${tick}`"></span>
                </div>
                <div
                  v-for="term in treasuryTerms"
                  :key="`${row.country}-${term.key}`"
                  class="treasury-bar-item"
                >
                  <span :style="{ height: treasuryBarHeight(row[term.key]) }"></span>
                </div>
              </div>
              <div class="treasury-term-row">
                <span v-for="term in treasuryTerms" :key="`${row.country}-${term.key}-label`">{{ term.label }}</span>
              </div>
            </div>
          </article>
        </div>

        <section class="chart-reading-note treasury-reading-note">
          <h4>데이터 해석</h4>
          <ul>
            <li v-for="item in rateDashboardInterpretation" :key="item">{{ item }}</li>
          </ul>
        </section>
      </section>
    </article>

    <article v-else-if="activeIndicator && activeIndicator.id === 'yield-spread'" class="indicator-detail-card spread-detail-card">
      <header class="indicator-detail-header">
        <div>
          <p class="eyebrow">Indicator Report</p>
          <h2>장단기 금리차</h2>
        </div>
        <div class="indicator-current-value">
          <span>한국 기준</span>
          <strong>{{ yieldSpreadValue }}</strong>
          <small>10년 금리 - 3년 금리</small>
        </div>
      </header>

      <section class="indicator-explanation">
        <h3>개념 설명</h3>
        <p>10년 금리에서 3년 금리를 뺀 값입니다. 플러스면 장기 금리가 단기 금리보다 높고, 마이너스면 단기 금리가 장기 금리보다 높은 역전 구간으로 볼 수 있습니다.</p>
      </section>

      <section class="indicator-table-panel spread-table-panel">
        <div class="panel-title">
          <h3>데이터 표</h3>
          <span>{{ yieldSpreadRows.length }}개 항목</span>
        </div>
        <div class="indicator-table-wrap">
          <table class="indicator-data-table spread-data-table">
            <thead>
              <tr>
                <th>구분</th>
                <th>장단기 금리차</th>
                <th>상태</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in yieldSpreadRows" :key="`${row.country}-spread-table`">
                <th scope="row">
                  <span class="country-chip" :class="row.tone">{{ row.country }}</span>
                </th>
                <td>
                  <strong class="rate-cell spread-rate-cell" :class="{ negative: row.spread < 0 }">{{ row.value }}</strong>
                </td>
                <td>
                  <span class="spread-state-pill" :class="{ negative: row.spread < 0, flat: isFlatSpread(row.spread) }">
                    {{ row.state }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="spread-summary-grid" aria-label="장단기 금리차 요약">
        <article v-for="row in yieldSpreadRows" :key="`${row.country}-spread-summary`" :class="row.tone">
          <span>{{ row.country }}</span>
          <strong :class="{ negative: row.spread < 0 }">{{ row.value }}</strong>
          <small>{{ row.state }}</small>
        </article>
      </section>

      <section class="indicator-chart-panel spread-chart-panel">
        <div class="panel-title">
          <div>
            <h3>그래프 읽는 법</h3>
            <p>단위: %p, 가운데 0%p 기준</p>
          </div>
          <span>10년 금리 - 3년 금리</span>
        </div>

        <div class="spread-chart-grid" aria-label="국가별 장단기 금리차 그래프">
          <article
            v-for="row in yieldSpreadRows"
            :key="`${row.country}-spread-chart`"
            class="spread-chart-card"
            :class="row.tone"
          >
            <header>
              <strong>{{ row.country }}</strong>
              <span>{{ row.state }}</span>
            </header>
            <div class="spread-value-row">
              <strong :class="{ negative: row.spread < 0 }">{{ row.value }}</strong>
            </div>
            <div class="spread-scale" aria-hidden="true">
              <span>역전</span>
              <span>0%p</span>
              <span>정상</span>
            </div>
            <div class="spread-bar-track">
              <span class="spread-zero-line" aria-hidden="true"></span>
              <span
                class="spread-bar"
                :class="{ negative: row.spread < 0 }"
                :style="spreadBarStyle(row.spread)"
              ></span>
            </div>
          </article>
        </div>

        <section class="chart-reading-note spread-reading-note">
          <h4>데이터 해석</h4>
          <ul>
            <li v-for="item in yieldSpreadInterpretation" :key="item">{{ item }}</li>
          </ul>
        </section>
      </section>
    </article>

    <article v-else-if="activeIndicator && activeIndicator.id === 'credit-rating-yield'" class="credit-rate-board">
      <header class="credit-board-header">
        <div>
          <p class="eyebrow">Credit Rating Rates</p>
          <h2>금리 및 스프레드</h2>
          <p>신용등급별 회사채 금리와 국고채 대비 스프레드를 기준일별로 확인합니다.</p>
        </div>
      </header>

      <section class="credit-search-box" aria-label="기준일 검색">
        <label>
          <span>기준일자</span>
          <input v-model="creditBaseDate" type="date" />
        </label>
        <button type="button" aria-label="기준일 조회">조회</button>
      </section>

      <div class="credit-sub-tabs" aria-label="신용등급 금리 보기 방식">
        <button
          :class="{ active: creditRateView === 'rates' }"
          type="button"
          @click="creditRateView = 'rates'"
        >
          등급별 금리
        </button>
        <button
          :class="{ active: creditRateView === 'spreads' }"
          type="button"
          @click="creditRateView = 'spreads'"
        >
          등급별 스프레드
        </button>
      </div>

      <section class="credit-guide-grid" aria-label="신용등급 지표 해석 안내">
        <article>
          <strong>등급별 금리</strong>
          <p>같은 기준일에서 신용등급별 회사채 평균 금리를 비교합니다. 등급이 낮을수록 시장이 요구하는 위험 보상이 커질 수 있습니다.</p>
        </article>
        <article>
          <strong>등급별 스프레드</strong>
          <p>국고채 금리 대비 추가 수익률입니다. 스프레드가 커질수록 신용위험 프리미엄이 확대된 것으로 해석할 수 있습니다.</p>
        </article>
        <article>
          <strong>주의해서 볼 점</strong>
          <p>높은 금리는 높은 보상인 동시에 신용위험, 유동성위험, 등급 하락 가능성이 반영된 결과일 수 있습니다.</p>
        </article>
      </section>

      <div class="credit-table-wrap">
        <table class="credit-rate-table">
          <thead>
            <tr>
              <th v-for="column in creditTableColumns" :key="column">{{ column }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in creditTableRows" :key="row.join('-')">
              <th scope="row">{{ row[0] }}</th>
              <td v-for="cell in row.slice(1)" :key="cell">{{ cell }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <section class="credit-board-note">
        <h3>{{ creditRateView === 'rates' ? '등급별 금리 해석' : '등급별 스프레드 해석' }}</h3>
        <p v-if="creditRateView === 'rates'">
          등급이 낮아질수록 투자자가 요구하는 위험 보상이 커져 금리가 높아집니다. 같은 기준일 안에서도 AAA와 BBB 구간의 차이를 보면 신용위험 프리미엄을 빠르게 파악할 수 있습니다.
        </p>
        <p v-else>
          스프레드는 국고채 대비 추가 수익률입니다. 스프레드가 확대되면 시장이 신용위험을 더 크게 반영하고 있다는 뜻이므로, 수익률뿐 아니라 발행사 재무와 유동성도 함께 확인해야 합니다.
        </p>
      </section>
    </article>

    <article v-else-if="activeIndicator" class="indicator-detail-card">
      <header class="indicator-detail-header">
        <div>
          <p class="eyebrow">Indicator Report</p>
          <h2>{{ activeIndicator.title }}</h2>
        </div>
        <div class="indicator-current-value">
          <span>현재 기준</span>
          <strong>{{ activeIndicator.value }}</strong>
          <small>{{ activeIndicator.caption }}</small>
        </div>
      </header>

      <section class="indicator-explanation">
        <h3>개념 설명</h3>
        <p>{{ activeIndicator.summary }}</p>
      </section>

      <section class="indicator-data-layout">
        <div class="indicator-table-panel">
          <div class="panel-title">
            <h3>데이터 표</h3>
            <span>{{ activeIndicator.tableRows.length }}개 항목</span>
          </div>
          <div class="indicator-table-wrap">
            <table class="indicator-data-table">
              <thead>
                <tr>
                  <th v-for="column in activeIndicator.tableColumns" :key="column">{{ column }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in activeIndicator.tableRows" :key="row.join('-')">
                  <td v-for="cell in row" :key="cell">{{ cell }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="indicator-chart-panel">
          <div class="panel-title">
            <div>
              <h3>{{ chartGuide.title }}</h3>
              <p>{{ chartGuide.unit }}</p>
            </div>
            <span>{{ activeIndicator.chartType === 'bar' ? '막대 비교' : '흐름 비교' }}</span>
          </div>

          <section class="chart-guide" aria-label="그래프 해석 안내">
            <div>
              <strong>가로축</strong>
              <p>{{ chartGuide.xAxis }}</p>
            </div>
            <div>
              <strong>세로축</strong>
              <p>{{ chartGuide.yAxis }}</p>
            </div>
          </section>

          <div class="chart-frame">
            <div class="chart-y-axis" aria-hidden="true">
              <span>높음</span>
              <span>낮음</span>
            </div>

            <svg
              v-if="activeIndicator.chartType === 'line' || activeIndicator.chartType === 'curve'"
              viewBox="0 0 720 260"
              class="indicator-chart line-chart"
              :aria-label="`${activeIndicator.title} 흐름 그래프`"
            >
              <text x="20" y="26" class="axis-label">높음</text>
              <text x="20" y="238" class="axis-label">낮음</text>
              <line x1="20" y1="205" x2="700" y2="205" />
              <line x1="20" y1="44" x2="20" y2="205" />
              <line x1="20" y1="155" x2="700" y2="155" />
              <line x1="20" y1="100" x2="700" y2="100" />
              <polyline :points="activeIndicator.chartPoints" />
              <circle
                v-for="point in activeIndicator.chartPoints.split(' ')"
                :key="point"
                :cx="point.split(',')[0]"
                :cy="point.split(',')[1]"
                r="5"
              />
              <text x="20" y="246" class="axis-label">
                {{ activeIndicator.chartType === 'curve' ? '짧은 만기' : '과거' }}
              </text>
              <text x="620" y="246" class="axis-label">
                {{ activeIndicator.chartType === 'curve' ? '긴 만기' : '최근' }}
              </text>
            </svg>

            <div v-else class="indicator-chart bar-chart" :aria-label="`${activeIndicator.title} 막대 그래프`">
              <div v-for="row in barRows" :key="row.label" class="bar-item">
                <span :style="{ height: `${row.height}%` }"></span>
                <strong>{{ row.value }}</strong>
                <small>{{ row.label }}</small>
              </div>
            </div>
          </div>

          <div v-if="activeIndicator.chartType === 'bar'" class="bar-legend">
            <article v-for="row in barRows" :key="`${row.label}-legend`">
              <strong>{{ row.label }} {{ row.value }}</strong>
              <p>{{ row.description }}</p>
            </article>
          </div>

          <section class="chart-reading-note">
            <h4>이 그래프는 이렇게 봅니다</h4>
            <p>{{ chartGuide.reading }}</p>
            <h4>주의해서 볼 점</h4>
            <p>{{ chartGuide.caution }}</p>
          </section>
        </div>
      </section>

      <section class="indicator-insight">
        <h3>데이터 요약 및 설명</h3>
        <p>{{ activeIndicator.insight }}</p>
        <div class="indicator-stat-grid">
          <article v-for="stat in activeIndicator.stats" :key="stat.label">
            <span>{{ stat.label }}</span>
            <strong>{{ stat.value }}</strong>
          </article>
        </div>
      </section>
    </article>
  </section>
</template>

<style scoped>
.indicators-detail-page {
  display: grid;
  gap: 22px;
}

.indicator-nav {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.indicator-nav button {
  flex: 0 0 auto;
  min-height: 40px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 14px;
  color: var(--text);
  background: white;
  font-weight: 800;
}

.indicator-nav button.active {
  border-color: var(--primary);
  color: white;
  background: var(--primary);
}

.credit-rate-board {
  display: grid;
  gap: 20px;
}

.credit-guide-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.credit-guide-grid article {
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
}

.credit-guide-grid strong {
  color: var(--primary-dark);
  font-size: 14px;
}

.credit-guide-grid p {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
}

.credit-board-header h2 {
  margin-bottom: 8px;
  font-size: clamp(28px, 4vw, 40px);
}

.credit-board-header p:not(.eyebrow) {
  margin-bottom: 0;
}

.credit-search-box,
.credit-sub-tabs,
.credit-table-wrap,
.credit-board-note {
  border: 1px solid var(--line);
  background: white;
}

.credit-search-box {
  display: flex;
  gap: 18px;
  align-items: end;
  padding: 20px;
  box-shadow: inset 0 -5px 0 #e2e5e9;
}

.credit-search-box label {
  display: flex;
  grid-template-columns: none;
  gap: 12px;
  align-items: center;
  color: var(--text);
  font-size: 18px;
  font-weight: 900;
}

.credit-search-box input {
  width: 150px;
  border-radius: 0;
  font-weight: 800;
}

.credit-search-box button {
  min-width: 94px;
  min-height: 42px;
  border: 0;
  color: white;
  background: #0097dc;
  font-size: 0;
}

.credit-search-box button::before {
  content: "⌕";
  font-size: 28px;
  font-weight: 900;
}

.credit-sub-tabs {
  display: flex;
  margin-top: 2px;
}

.credit-sub-tabs button {
  min-width: 140px;
  min-height: 58px;
  border: 0;
  border-right: 1px solid var(--line);
  color: var(--text);
  background: #f6f6f6;
  font-size: 17px;
  font-weight: 900;
}

.credit-sub-tabs button.active {
  color: white;
  background: #0067c5;
}

.credit-table-wrap {
  overflow-x: auto;
  border-top: 3px solid #0067c5;
}

.credit-rate-table {
  width: 100%;
  min-width: 0;
  table-layout: fixed;
  border-collapse: collapse;
  background: white;
}

.credit-rate-table th,
.credit-rate-table td {
  height: 58px;
  padding: 13px 10px;
  border: 1px solid #d7dce2;
  text-align: center;
  word-break: keep-all;
}

.credit-rate-table thead th {
  background: #f8f8f8;
  color: #111827;
  font-size: 15px;
  font-weight: 900;
}

.credit-rate-table tbody th {
  color: #005bbb;
  background: white;
  font-weight: 900;
}

.credit-rate-table td {
  font-variant-numeric: tabular-nums;
}

.credit-board-note {
  padding: 20px;
}

.credit-board-note h3 {
  margin-bottom: 8px;
  font-size: 18px;
}

.credit-board-note p {
  margin-bottom: 0;
  line-height: 1.7;
}

.indicator-detail-card {
  display: grid;
  gap: 20px;
  padding: 26px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.treasury-detail-card {
  background: transparent;
  box-shadow: none;
}

.treasury-table-panel,
.treasury-chart-panel {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
  box-shadow: var(--shadow);
}

.treasury-table-panel {
  padding: 18px;
}

.treasury-chart-panel {
  display: grid;
  gap: 12px;
  padding: 18px;
}

.base-rate-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.base-rate-summary-grid article {
  display: grid;
  gap: 6px;
  padding: 18px;
  border: 1px solid var(--line);
  border-left: 5px solid var(--primary);
  border-radius: 8px;
  background: white;
  box-shadow: var(--shadow);
}

.base-rate-summary-grid article.us {
  border-left-color: #1f6f78;
}

.base-rate-summary-grid article.jp {
  border-left-color: #d98c31;
}

.base-rate-summary-grid article.kr {
  border-left-color: #127c57;
}

.base-rate-summary-grid span,
.base-rate-summary-grid small {
  color: var(--muted);
  font-size: 13px;
  font-weight: 800;
}

.base-rate-summary-grid strong {
  color: var(--primary-dark);
  font-size: 28px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
}

.rate-spread-summary-panel {
  display: grid;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
  box-shadow: var(--shadow);
}

.rate-spread-summary-panel .panel-title {
  align-items: center;
}

.rate-spread-summary-panel .panel-title button {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 9px 12px;
  color: var(--primary-dark);
  background: #f8fbfd;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
}

.rate-spread-summary-panel .panel-title button:hover {
  border-color: var(--primary);
  color: white;
  background: var(--primary);
}

.rate-spread-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.rate-spread-summary-grid article {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 12px 14px;
  border: 1px solid #dce7ef;
  border-radius: 8px;
  background: #fbfdff;
}

.rate-spread-summary-grid article.us {
  border-left: 4px solid #1f6f78;
}

.rate-spread-summary-grid article.jp {
  border-left: 4px solid #d98c31;
}

.rate-spread-summary-grid article.kr {
  border-left: 4px solid #127c57;
}

.rate-spread-summary-grid span {
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
}

.rate-spread-summary-grid strong {
  color: var(--primary-dark);
  font-size: 18px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.rate-spread-summary-grid strong.negative {
  color: #b45309;
}

.rate-spread-summary-grid small {
  justify-self: end;
  border-radius: 999px;
  padding: 5px 9px;
  color: #0f6f52;
  background: #e5f5ef;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
}

.rate-spread-summary-grid small.negative {
  color: #a15c12;
  background: #fff1dc;
}

.indicator-detail-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: start;
}

.indicator-detail-header h2 {
  margin-bottom: 0;
  font-size: clamp(26px, 4vw, 38px);
}

.indicator-current-value {
  display: grid;
  min-width: 220px;
  gap: 4px;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
  text-align: right;
}

.indicator-current-value span,
.indicator-current-value small,
.panel-title span {
  color: var(--muted);
  font-size: 13px;
}

.indicator-current-value strong {
  color: var(--primary);
  font-size: 32px;
}

.indicator-explanation,
.indicator-insight,
.indicator-table-panel,
.indicator-chart-panel {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
}

.indicator-explanation,
.indicator-insight {
  padding: 20px;
}

.indicator-explanation h3,
.indicator-insight h3,
.panel-title h3 {
  margin-bottom: 8px;
  font-size: 18px;
}

.indicator-explanation p,
.indicator-insight p {
  margin-bottom: 0;
  line-height: 1.7;
}

.indicator-data-layout {
  display: grid;
  grid-template-columns: minmax(520px, 0.95fr) minmax(520px, 1.05fr);
  gap: 16px;
}

.indicator-table-panel,
.indicator-chart-panel {
  min-width: 0;
  padding: 18px;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.panel-title p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 13px;
  font-weight: 700;
}

.chart-guide {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.chart-guide div,
.chart-reading-note,
.bar-legend article {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.chart-guide div {
  padding: 12px;
}

.chart-guide strong,
.chart-reading-note h4,
.bar-legend strong {
  color: var(--primary-dark);
  font-size: 13px;
  font-weight: 900;
}

.chart-guide p,
.chart-reading-note p,
.bar-legend p {
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.55;
}

.chart-frame {
  position: relative;
}

.chart-y-axis {
  position: absolute;
  z-index: 1;
  top: 16px;
  bottom: 18px;
  left: 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: var(--muted);
  font-size: 11px;
  font-weight: 800;
  pointer-events: none;
}

.indicator-table-wrap {
  overflow-x: visible;
}

.indicator-data-table {
  width: 100%;
  min-width: 0;
  table-layout: fixed;
  border-collapse: collapse;
}

.indicator-data-table th,
.indicator-data-table td {
  padding: 13px 14px;
  border: 1px solid var(--line);
  text-align: left;
  word-break: keep-all;
}

.indicator-data-table th {
  color: var(--text);
  background: #f5f8fb;
  font-size: 13px;
  font-weight: 900;
}

.indicator-data-table td {
  font-size: 14px;
}

.treasury-rate-table {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
}

.treasury-rate-table th,
.treasury-rate-table td {
  padding: 18px 20px;
  vertical-align: middle;
}

.treasury-rate-table thead th {
  background: #eef5f8;
  color: var(--primary-dark);
  font-size: 13px;
}

.treasury-rate-table tbody tr:nth-child(even) {
  background: #fbfdff;
}

.treasury-rate-table tbody tr:hover {
  background: #f3faf9;
}

.country-chip {
  display: inline-flex;
  min-width: 54px;
  justify-content: center;
  border-radius: 999px;
  padding: 6px 10px;
  color: white;
  background: var(--primary);
  font-size: 13px;
  font-weight: 900;
}

.country-chip.us {
  background: #1f6f78;
}

.country-chip.jp {
  background: #d98c31;
}

.country-chip.kr {
  background: #127c57;
}

.rate-cell {
  display: block;
  color: var(--primary-dark);
  font-size: 22px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
}

.treasury-rate-table small {
  display: block;
  margin-top: 4px;
  color: var(--muted);
  font-size: 11px;
  font-weight: 800;
}

.indicator-chart {
  width: 100%;
  min-height: 260px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fbfdff;
}

.axis-label {
  fill: var(--muted);
  font-size: 13px;
  font-weight: 800;
}

.line-chart line {
  stroke: #d8e1ea;
  stroke-width: 2;
}

.line-chart polyline {
  fill: none;
  stroke: var(--primary);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 6;
}

.line-chart circle {
  fill: white;
  stroke: var(--primary);
  stroke-width: 4;
}

.bar-chart {
  display: flex;
  align-items: end;
  justify-content: space-around;
  gap: 16px;
  padding: 30px 18px 18px 44px;
}

.bar-item {
  display: grid;
  grid-template-rows: 1fr auto auto;
  gap: 8px;
  align-items: end;
  width: 100%;
  height: 220px;
  text-align: center;
}

.bar-item span {
  width: 100%;
  min-height: 18px;
  border-radius: 6px 6px 0 0;
  background: linear-gradient(180deg, var(--primary), var(--accent));
}

.bar-item strong {
  color: var(--primary-dark);
  font-size: 14px;
}

.bar-item small {
  color: var(--muted);
  font-weight: 800;
}

.bar-legend {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.bar-legend article {
  padding: 12px;
}

.chart-reading-note {
  display: grid;
  gap: 8px;
  margin-top: 12px;
  padding: 14px;
  background: white;
}

.chart-reading-note h4,
.chart-reading-note p {
  margin: 0;
}

.chart-reading-note ul {
  display: grid;
  gap: 8px;
  margin: 0;
  padding-left: 18px;
}

.chart-reading-note li {
  color: var(--text);
  font-size: 14px;
  line-height: 1.65;
  word-break: keep-all;
}

.treasury-chart-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.treasury-chart-card {
  display: grid;
  gap: 10px;
  min-width: 0;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fbfdff;
}

.treasury-chart-card header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.treasury-chart-card header strong {
  color: var(--primary-dark);
  font-size: 16px;
}

.treasury-chart-card header span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  text-align: right;
}

.treasury-bar-chart {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  grid-template-rows: auto 180px auto;
  column-gap: 10px;
  row-gap: 8px;
  min-height: 238px;
}

.treasury-value-row,
.treasury-term-row {
  grid-column: 2;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 28px;
  padding: 0 28px;
  text-align: center;
}

.treasury-value-row span {
  color: var(--primary-dark);
  font-size: 13px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
}

.treasury-term-row span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
}

.treasury-axis {
  grid-column: 1;
  grid-row: 2;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 180px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  text-align: right;
}

.treasury-bar-plot {
  grid-column: 2;
  grid-row: 2;
  position: relative;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 28px;
  align-items: end;
  height: 180px;
  padding: 0 28px;
  border-left: 2px solid #9fb2c3;
  border-bottom: 2px solid #9fb2c3;
}

.treasury-grid-lines {
  position: absolute;
  inset: 0 0 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  pointer-events: none;
}

.treasury-grid-lines span {
  display: block;
  width: 100%;
  border-top: 1px solid #d9e4ee;
}

.treasury-bar-item {
  position: relative;
  z-index: 1;
  display: grid;
  align-items: end;
  height: 180px;
  text-align: center;
}

.treasury-bar-item > span {
  width: min(58px, 76%);
  min-height: 6px;
  border-radius: 6px 6px 0 0;
  justify-self: center;
  background: var(--primary);
}

.treasury-chart-card.us .treasury-bar-item > span {
  background: #1f6f78;
}

.treasury-chart-card.jp .treasury-bar-item > span {
  background: #d98c31;
}

.treasury-chart-card.kr .treasury-bar-item > span {
  background: #127c57;
}

.treasury-bar-item small {
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
}

.treasury-reading-note {
  margin-top: 0;
}

.spread-detail-card {
  gap: 16px;
}

.spread-table-panel,
.spread-chart-panel {
  width: 100%;
}

.spread-data-table {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
}

.spread-data-table th,
.spread-data-table td {
  padding: 18px 20px;
  vertical-align: middle;
}

.spread-data-table thead th {
  background: #eef5f8;
  color: var(--primary-dark);
}

.spread-data-table tbody tr:nth-child(even) {
  background: #fbfdff;
}

.spread-rate-cell.negative,
.spread-summary-grid strong.negative,
.spread-value-row strong.negative {
  color: #b45309;
}

.spread-state-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 86px;
  border-radius: 999px;
  padding: 7px 12px;
  color: #0f6f52;
  background: #e5f5ef;
  font-size: 12px;
  font-weight: 900;
}

.spread-state-pill.flat {
  color: #1f6f78;
  background: #e8f2f6;
}

.spread-state-pill.negative {
  color: #a15c12;
  background: #fff1dc;
}

.spread-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.spread-summary-grid article {
  display: grid;
  gap: 6px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fbfdff;
}

.spread-summary-grid article.us {
  border-top: 4px solid #1f6f78;
}

.spread-summary-grid article.jp {
  border-top: 4px solid #d98c31;
}

.spread-summary-grid article.kr {
  border-top: 4px solid #127c57;
}

.spread-summary-grid span,
.spread-summary-grid small {
  color: var(--muted);
  font-size: 13px;
  font-weight: 800;
}

.spread-summary-grid strong {
  color: var(--primary-dark);
  font-size: 28px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
}

.spread-chart-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.spread-chart-card {
  display: grid;
  gap: 14px;
  min-width: 0;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fbfdff;
}

.spread-chart-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.spread-chart-card header strong {
  color: var(--primary-dark);
  font-size: 16px;
}

.spread-chart-card header span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
}

.spread-value-row {
  color: var(--primary-dark);
  font-size: 22px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
}

.spread-scale {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
}

.spread-scale span:nth-child(2) {
  text-align: center;
}

.spread-scale span:nth-child(3) {
  text-align: right;
}

.spread-bar-track {
  position: relative;
  height: 34px;
  border-radius: 999px;
  background:
    linear-gradient(90deg, #fff7ed 0 50%, #e5f5ef 50% 100%);
  box-shadow: inset 0 0 0 1px #d7e3ee;
}

.spread-zero-line {
  position: absolute;
  top: -7px;
  bottom: -7px;
  left: 50%;
  width: 2px;
  border-radius: 999px;
  background: #8fa5b8;
}

.spread-bar {
  position: absolute;
  top: 8px;
  bottom: 8px;
  min-width: 6px;
  border-radius: 999px;
  background: #127c57;
}

.spread-bar.negative {
  background: #d98c31;
}

.spread-chart-card.us .spread-bar {
  background: #1f6f78;
}

.spread-chart-card.jp .spread-bar {
  background: #d98c31;
}

.spread-chart-card.kr .spread-bar {
  background: #127c57;
}

.spread-reading-note {
  margin-top: 0;
}

.indicator-stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.indicator-stat-grid article {
  display: grid;
  gap: 6px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.indicator-stat-grid span {
  color: var(--muted);
  font-size: 13px;
}

.indicator-stat-grid strong {
  color: var(--primary-dark);
  font-size: 22px;
}

@media (max-width: 960px) {
  .indicator-detail-header,
  .indicator-data-layout,
  .credit-guide-grid,
  .treasury-chart-grid,
  .base-rate-summary-grid,
  .rate-spread-summary-grid,
  .spread-summary-grid,
  .spread-chart-grid {
    grid-template-columns: 1fr;
  }

  .indicator-detail-header {
    flex-direction: column;
  }

  .indicator-current-value {
    width: 100%;
    text-align: left;
  }
}

@media (max-width: 640px) {
  .indicator-detail-card {
    padding: 18px;
  }

  .chart-guide,
  .bar-legend {
    grid-template-columns: 1fr;
  }

  .indicator-stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
