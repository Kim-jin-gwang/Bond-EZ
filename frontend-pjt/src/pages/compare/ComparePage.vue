<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { fetchBondCompare } from '../../api/bonds'

const remoteCompareBonds = ref(null)
const activePerspectiveKey = ref('yield_maturity')
const route = useRoute()

const props = defineProps({
  compareBonds: {
    type: Array,
    default: () => [],
  },
})

const displayedBonds = computed(() => {
  if (remoteCompareBonds.value?.length === 2) {
    return remoteCompareBonds.value
  }

  if (props.compareBonds.length === 2) {
    return props.compareBonds
  }

  return []
})

const hasComparisonData = computed(() => displayedBonds.value.length === 2)
const leftBond = computed(() => displayedBonds.value[0] || {})
const rightBond = computed(() => displayedBonds.value[1] || {})
const compareTitle = computed(() => `${bondDisplayName(leftBond.value)} vs ${bondDisplayName(rightBond.value)}`)

const compareSections = computed(() => [
  {
    title: '기본 정보',
    caption: '종목 식별, 발행기관, 신용 구조',
    rows: [
      row('표준코드', 'code'),
      row('단축코드', 'shortCode'),
      row('종목약명', 'shortName'),
      row('발행기관', 'issuer'),
      row('산업', 'industry'),
      row('채권종류', 'type'),
      row('신용등급', 'rating', 'rating'),
      row('선후순위', 'seniority'),
      row('보증여부', 'guaranteeStatus'),
    ],
  },
  {
    title: '가격 및 수익률',
    caption: '현재가, 매수/매도 수익률, 듀레이션',
    rows: [
      row('현재가', 'price'),
      row('등락률', 'change', 'change'),
      row('대용가격', 'substitutePrice'),
      row('매수수익률', 'buyYield', 'higher'),
      row('매도수익률', 'sellYield', 'higher'),
      row('만기수익률(YTM)', 'ytm', 'higher'),
      row('듀레이션', 'duration', 'lower'),
      row('거래량', 'volume', 'higher-volume'),
    ],
  },
  {
    title: '발행 및 상환',
    caption: '발행일, 만기일, 상환 방식',
    rows: [
      row('발행일', 'issueDate'),
      row('상장일', 'listingDate'),
      row('만기일', 'maturityDate'),
      row('잔존만기', 'maturityYears', 'lower-year', '년'),
      row('발행금액', 'issueAmount'),
      row('대표주관회사', 'underwriter'),
      row('상환방법', 'redemptionMethod'),
      row('만기상환율', 'maturityRedemptionRate'),
      row('특이상환조건', 'earlyRedemptionDescription'),
    ],
  },
  {
    title: '이자 지급 조건',
    caption: '현금흐름 계산에 필요한 이자 규칙',
    rows: [
      row('이자방식', 'interestType'),
      row('표면금리', 'coupon', 'higher'),
      row('이자지급방법', 'interestPaymentMethod'),
      row('지급주기', 'interestCycle'),
      row('지급단위월수', 'interestPaymentUnitMonths', 'lower-month', '개월'),
      row('이자계산월수', 'interestCalculationMonths', 'lower-month', '개월'),
      row('선후급구분', 'interestPrePostType'),
      row('최초이자지급일', 'firstInterestPaymentDate'),
      row('이자지급기준', 'interestPaymentBasis'),
      row('월말구분', 'interestMonthEndType'),
    ],
  },
  {
    title: '옵션 행사 정보',
    caption: 'CALL/PUT 여부와 행사 가능일',
    rows: [
      row('옵션종류', 'option'),
      customRow('1차 행사개시일', (bond) => bond.optionExercise?.startDate1 || '-'),
      customRow('1차 행사종료일', (bond) => bond.optionExercise?.endDate1 || '-'),
      customRow('2차 행사개시일', (bond) => bond.optionExercise?.startDate2 || '-'),
      customRow('2차 행사종료일', (bond) => bond.optionExercise?.endDate2 || '-'),
      customRow('행사사유', (bond) => bond.optionExercise?.reason || '-'),
    ],
  },
])

const comparisonPerspectives = computed(() => [
  {
    key: 'yield_maturity',
    title: '금리와 만기',
    caption: '수익률 수치와 보유 기간을 각각 비교합니다.',
    metrics: [
      numericMetric('매수수익률', leftBond.value.buyYield, rightBond.value.buyYield, leftBond.value.yieldValue, rightBond.value.yieldValue, 'higher', '수치 높음', '수익률이 높다는 사실만으로 실제 수익을 보장하지 않습니다.'),
      numericMetric('만기수익률(YTM)', leftBond.value.ytm, rightBond.value.ytm, leftBond.value.ytmValue, rightBond.value.ytmValue, 'higher', '수치 높음', '현재 가격으로 만기 보유를 가정한 수치입니다.'),
      numericMetric('표면금리', leftBond.value.coupon, rightBond.value.coupon, leftBond.value.couponRate, rightBond.value.couponRate, 'higher', '수치 높음', '표면금리는 현재 매입가격을 반영한 수익률과 다릅니다.'),
      numericMetric('잔존만기', maturityLabel(leftBond.value), maturityLabel(rightBond.value), leftBond.value.maturityYears, rightBond.value.maturityYears, 'lower', '기간 짧음', '짧은 만기가 모든 투자 목적에 유리하다는 의미는 아닙니다.'),
    ],
  },
  {
    key: 'credit',
    title: '신용위험 구조',
    caption: '공시된 등급과 상환 순위, 보증 표시를 비교합니다.',
    metrics: [
      numericMetric('신용등급', leftBond.value.rating || '-', rightBond.value.rating || '-', ratingScore(leftBond.value.rating), ratingScore(rightBond.value.rating), 'higher', '등급 표기 높음', '신용등급은 원리금 상환을 보장하지 않습니다.'),
      numericMetric('선후순위', leftBond.value.seniority || '-', rightBond.value.seniority || '-', seniorityScore(leftBond.value.seniority), seniorityScore(rightBond.value.seniority), 'higher', '상환 순위 앞섬', '실제 변제 순위는 발행 조건과 투자설명서를 확인해야 합니다.'),
      numericMetric('보증여부', leftBond.value.guaranteeStatus || '-', rightBond.value.guaranteeStatus || '-', guaranteeScore(leftBond.value.guaranteeStatus), guaranteeScore(rightBond.value.guaranteeStatus), 'higher', '보증 표시 있음', '보증의 범위와 보증기관은 별도로 확인해야 합니다.'),
    ],
  },
  {
    key: 'liquidity_duration',
    title: '유동성과 민감도',
    caption: '관측 거래량과 금리 변화에 대한 가격 민감도를 비교합니다.',
    metrics: [
      numericMetric('거래량', leftBond.value.volume, rightBond.value.volume, leftBond.value.tradingVolume, rightBond.value.tradingVolume, 'higher', '관측 거래량 많음', '특정 시점의 거래량이며 향후 매매 가능성을 보장하지 않습니다.'),
      numericMetric('듀레이션', leftBond.value.duration, rightBond.value.duration, leftBond.value.durationValue, rightBond.value.durationValue, 'lower', '금리 민감도 낮음', '듀레이션이 낮다는 사실이 상품의 안정성을 의미하지 않습니다.'),
    ],
  },
  {
    key: 'options',
    title: '옵션과 상환',
    caption: '보유 기간에 영향을 줄 수 있는 CALL·PUT 표시를 구분합니다.',
    metrics: [
      booleanMetric('CALL 옵션', leftBond.value.option, rightBond.value.option, !hasOption(leftBond.value, 'CALL'), !hasOption(rightBond.value, 'CALL'), 'CALL 없음', 'CALL은 발행자가 조기상환할 수 있는 조건입니다.'),
      booleanMetric('PUT 옵션', leftBond.value.option, rightBond.value.option, hasOption(leftBond.value, 'PUT'), hasOption(rightBond.value, 'PUT'), 'PUT 있음', 'PUT은 조건에 따라 투자자가 상환을 요구할 수 있는 권리입니다.'),
    ],
  },
])

const activePerspective = computed(() => (
  comparisonPerspectives.value.find((perspective) => perspective.key === activePerspectiveKey.value)
  || comparisonPerspectives.value[0]
))

function row(label, key, compareType = null, suffix = '') {
  return {
    label,
    left: formatValue(leftBond.value[key], suffix),
    right: formatValue(rightBond.value[key], suffix),
  }
}

function customRow(label, getter) {
  return {
    label,
    left: getter(leftBond.value),
    right: getter(rightBond.value),
  }
}

function formatValue(value, suffix = '') {
  if (value === null || value === undefined || value === '') {
    return '-'
  }

  return suffix ? `${value}${suffix}` : value
}

function bondDisplayName(bond) {
  return bond?.shortName || bond?.name || bond?.code || '-'
}

function numericMetric(label, left, right, leftScore, rightScore, preference, resultLabel, note) {
  const leftAvailable = isComparable(left, leftScore)
  const rightAvailable = isComparable(right, rightScore)
  let outcome = 'insufficient'
  let result = '비교 정보 부족'

  if (leftAvailable && rightAvailable) {
    if (Number(leftScore) === Number(rightScore)) {
      outcome = 'same'
      result = '동일'
    } else {
      const leftMatches = preference === 'higher'
        ? Number(leftScore) > Number(rightScore)
        : Number(leftScore) < Number(rightScore)
      outcome = leftMatches ? 'left' : 'right'
      result = `${bondDisplayName(leftMatches ? leftBond.value : rightBond.value)} · ${resultLabel}`
    }
  }

  return { label, left, right, outcome, result, note }
}

function booleanMetric(label, left, right, leftMatches, rightMatches, resultLabel, note) {
  let outcome = 'same'
  let result = '동일'
  if (leftMatches !== rightMatches) {
    outcome = leftMatches ? 'left' : 'right'
    result = `${bondDisplayName(leftMatches ? leftBond.value : rightBond.value)} · ${resultLabel}`
  }
  return { label, left: left || '-', right: right || '-', outcome, result, note }
}

function isComparable(display, score) {
  const text = String(display ?? '')
  return score !== null
    && score !== undefined
    && Number.isFinite(Number(score))
    && !['', '-', '시세 없음', '정보 없음'].includes(text)
}

function maturityLabel(bond) {
  return bond.maturityDate ? `${bond.maturityYears}년` : '-'
}

function ratingScore(value) {
  const match = String(value || '').toUpperCase().match(/^(AAA|AA|A|BBB|BB|B|CCC|CC|C|D)([+-])?/)
  if (!match) return null
  const base = { AAA: 10, AA: 9, A: 8, BBB: 7, BB: 6, B: 5, CCC: 4, CC: 3, C: 2, D: 1 }[match[1]]
  const modifier = match[2] === '+' ? 0.2 : match[2] === '-' ? -0.2 : 0
  return base + modifier
}

function seniorityScore(value) {
  const text = String(value || '')
  if (text.includes('선순위')) return 3
  if (text.includes('중순위')) return 2
  if (text.includes('후순위')) return 1
  return null
}

function guaranteeScore(value) {
  const text = String(value || '')
  if (!text) return null
  if (text.includes('무보증')) return 0
  if (text.includes('보증')) return 1
  return null
}

function hasOption(bond, optionName) {
  return String(bond.optionType || bond.option || '').toUpperCase().includes(optionName)
}

onMounted(async () => {
  const queryIds = String(route.query.ids || '')
    .split(',')
    .map((id) => id.trim())
    .filter(Boolean)
  const ids = queryIds.length === 2 ? queryIds : props.compareBonds.map((bond) => bond.bondId).filter(Boolean)

  if (ids.length !== 2) {
    return
  }

  remoteCompareBonds.value = await fetchBondCompare(ids)
})
</script>

<template>
  <section v-if="hasComparisonData" class="page compare-page">
    <div class="page-heading compact">
      <p class="eyebrow">채권 비교</p>
      <h1 class="compare-title">{{ compareTitle }}</h1>
      <p>현재 ERD 기준의 발행정보, 시장 데이터, 이자 조건, 옵션 행사 정보를 나란히 비교합니다.</p>
    </div>

    <section class="compare-summary-grid">
      <article v-for="bond in displayedBonds" :key="bond.code" class="compare-summary-card">
        <div>
          <span>{{ bond.code }} · {{ bond.shortCode }}</span>
          <h2>{{ bond.name }}</h2>
          <p>{{ bond.issuer }} · {{ bond.type }} · {{ bond.seniority }}</p>
        </div>
        <dl>
          <div>
            <dt>매수수익률</dt>
            <dd>{{ bond.buyYield }}</dd>
          </div>
          <div>
            <dt>신용등급</dt>
            <dd>{{ bond.rating }}</dd>
          </div>
          <div>
            <dt>옵션</dt>
            <dd>{{ bond.option }}</dd>
          </div>
        </dl>
      </article>
    </section>

    <section class="indicator-panel">
      <header>
        <div>
          <p class="eyebrow">At a Glance</p>
          <h2>관점별 핵심 비교</h2>
        </div>
        <span>지표별 비교</span>
      </header>
      <div class="perspective-tabs" role="tablist" aria-label="비교 관점">
        <button
          v-for="perspective in comparisonPerspectives"
          :key="perspective.key"
          type="button"
          role="tab"
          :aria-selected="activePerspective?.key === perspective.key"
          :class="{ active: activePerspective?.key === perspective.key }"
          @click="activePerspectiveKey = perspective.key"
        >
          {{ perspective.title }}
        </button>
      </div>
      <div v-if="activePerspective" class="perspective-content" role="tabpanel">
        <div class="perspective-heading">
          <h3>{{ activePerspective.title }}</h3>
          <p>{{ activePerspective.caption }}</p>
        </div>
        <div class="metric-list">
          <article v-for="metric in activePerspective.metrics" :key="metric.label" class="metric-row">
            <div class="metric-value left" :class="{ matched: metric.outcome === 'left', same: metric.outcome === 'same' }">
              <small>{{ bondDisplayName(leftBond) }}</small>
              <strong>{{ metric.left }}</strong>
              <span v-if="metric.outcome === 'left'">해당</span>
            </div>
            <div class="metric-result">
              <span>{{ metric.label }}</span>
              <strong :class="metric.outcome">{{ metric.result }}</strong>
              <small>{{ metric.note }}</small>
            </div>
            <div class="metric-value right" :class="{ matched: metric.outcome === 'right', same: metric.outcome === 'same' }">
              <small>{{ bondDisplayName(rightBond) }}</small>
              <strong>{{ metric.right }}</strong>
              <span v-if="metric.outcome === 'right'">해당</span>
            </div>
          </article>
        </div>
      </div>
      <div class="summary-conclusion">
        <strong>유의사항</strong>
        <p>강조 표시는 선택한 지표의 수치 차이만 나타내며 투자 권유, 상품의 우수성 또는 사용자 적합성을 의미하지 않습니다.</p>
      </div>
    </section>

    <div class="detail-heading">
      <p class="eyebrow">Full Data Comparison</p>
      <h2>상세 비교 데이터</h2>
      <p>확인할 항목만 펼쳐서 두 채권의 원본 데이터를 비교하세요.</p>
    </div>

    <details v-for="section in compareSections" :key="section.title" class="compare-section">
      <summary>
        <div>
          <p class="eyebrow">{{ section.caption }}</p>
          <h2>{{ section.title }}</h2>
        </div>
        <span class="section-toggle" aria-hidden="true"></span>
      </summary>

      <div class="compare-table professional-compare">
        <div class="compare-row header">
          <span>항목</span>
          <strong>{{ bondDisplayName(leftBond) }}</strong>
          <strong>{{ bondDisplayName(rightBond) }}</strong>
        </div>
        <div v-for="item in section.rows" :key="`${section.title}-${item.label}`" class="compare-row">
          <span>{{ item.label }}</span>
          <strong>{{ item.left }}</strong>
          <strong>{{ item.right }}</strong>
        </div>
      </div>
    </details>
  </section>
</template>

<style scoped>
.compare-page {
  display: grid;
  gap: 20px;
}

.compare-title {
  max-width: 100%;
  overflow: hidden;
  font-size: 34px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compare-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.compare-summary-card,
.indicator-panel,
.compare-section {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.compare-summary-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
  align-items: stretch;
  padding: 22px;
}

.compare-summary-card span,
.compare-summary-card p,
.compare-summary-card dt {
  color: var(--muted);
  font-size: 13px;
}

.compare-summary-card h2 {
  margin: 8px 0;
  font-size: 22px;
  line-height: 1.35;
  overflow-wrap: anywhere;
  word-break: keep-all;
}

.compare-summary-card p {
  margin: 0;
}

.compare-summary-card dl {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 0;
}

.compare-summary-card dl > div {
  min-width: 0;
  padding: 10px;
  border-radius: 8px;
  background: var(--surface-soft);
}

.compare-summary-card dt,
.compare-summary-card dd {
  margin: 0;
}

.compare-summary-card dd {
  margin-top: 4px;
  color: var(--primary-dark);
  font-size: 18px;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.indicator-panel {
  display: grid;
  gap: 18px;
  padding: 24px;
  border-left: 5px solid var(--primary);
}

.indicator-panel > header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
}

.indicator-panel > header h2,
.indicator-panel p {
  margin-bottom: 0;
}

.indicator-panel > header > span {
  border-radius: 4px;
  padding: 4px 8px;
  color: var(--primary);
  background: #e8f3f4;
  font-size: 12px;
  font-weight: 900;
}

.perspective-tabs {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--surface-soft);
}

.perspective-tabs button {
  min-width: 0;
  min-height: 42px;
  padding: 8px 10px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

.perspective-tabs button:hover {
  color: var(--primary-dark);
}

.perspective-tabs button.active {
  color: var(--primary-dark);
  background: var(--surface);
  box-shadow: 0 1px 4px rgba(23, 43, 59, 0.12);
}

.perspective-content {
  display: grid;
  gap: 14px;
}

.perspective-heading h3 {
  margin: 0 0 4px;
  font-size: 18px;
}

.perspective-heading p {
  color: var(--muted);
  font-size: 13px;
}

.metric-list {
  display: grid;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 6px;
}

.metric-row {
  display: grid;
  grid-template-areas: "left result right";
  grid-template-columns: minmax(0, 1fr) minmax(220px, 0.85fr) minmax(0, 1fr);
  min-height: 116px;
  background: var(--surface);
}

.metric-row + .metric-row {
  border-top: 1px solid var(--line);
}

.metric-value,
.metric-result {
  min-width: 0;
  padding: 18px;
}

.metric-value {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 7px;
  transition: background 0.2s ease;
}

.metric-value.left {
  grid-area: left;
  align-items: flex-start;
  border-right: 1px solid var(--line);
}

.metric-value.right {
  grid-area: right;
  align-items: flex-end;
  border-left: 1px solid var(--line);
  text-align: right;
}

.metric-value small {
  max-width: 100%;
  overflow: hidden;
  color: var(--muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metric-value strong {
  max-width: 100%;
  color: var(--text);
  font-size: 21px;
  overflow-wrap: anywhere;
}

.metric-value > span {
  border-radius: 4px;
  padding: 2px 6px;
  color: var(--good);
  background: #dff3e8;
  font-size: 11px;
  font-weight: 900;
}

.metric-value.matched {
  background: color-mix(in srgb, var(--good) 12%, var(--surface));
  box-shadow: inset 0 0 0 2px #6bb78e;
}

.metric-value.matched strong {
  color: var(--good);
}

.metric-result {
  grid-area: result;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 6px;
  text-align: center;
  background: var(--surface-soft);
}

.metric-result > span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.metric-result > strong {
  color: var(--good);
  font-size: 14px;
  line-height: 1.4;
  word-break: keep-all;
}

.metric-result > strong.same,
.metric-result > strong.insufficient {
  color: var(--primary-dark);
}

.metric-result > small {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.45;
  word-break: keep-all;
}

.summary-conclusion {
  display: grid;
  gap: 6px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
}

.summary-conclusion strong {
  color: var(--primary-dark);
}

.summary-conclusion p {
  color: var(--muted);
  font-size: 13px;
  line-height: 1.65;
}

.detail-heading {
  margin-top: 12px;
}

.detail-heading h2 {
  margin: 4px 0 6px;
  font-size: 22px;
}

.detail-heading p:last-child {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
}

.compare-section {
  overflow: hidden;
}

.compare-section > summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  min-height: 72px;
  padding: 14px 20px;
  cursor: pointer;
  list-style: none;
}

.compare-section > summary::-webkit-details-marker {
  display: none;
}

.compare-section[open] > summary {
  border-bottom: 1px solid var(--line);
}

.compare-section > summary:hover {
  background: var(--surface-soft);
}

.section-toggle {
  width: 10px;
  height: 10px;
  flex: 0 0 10px;
  border-right: 2px solid var(--muted);
  border-bottom: 2px solid var(--muted);
  transform: rotate(45deg) translate(-2px, -2px);
  transition: transform 0.2s ease;
}

.compare-section[open] .section-toggle {
  transform: rotate(225deg) translate(-2px, -2px);
}

.compare-section h2 {
  font-size: 18px;
  margin-bottom: 0;
}

.professional-compare {
  overflow: hidden;
  border: 0;
  border-radius: 0;
  box-shadow: none;
}

.professional-compare .compare-row {
  grid-template-columns: minmax(120px, 0.7fr) minmax(0, 1fr) minmax(0, 1fr);
  min-height: 54px;
  align-items: center;
}

.compare-row span,
.compare-row strong {
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: keep-all;
}

.compare-row strong {
  font-size: 14px;
}

.compare-row.header strong {
  color: var(--primary-dark);
}

@media (max-width: 920px) {
  .compare-summary-grid,
  .compare-summary-card {
    grid-template-columns: 1fr;
  }

  .compare-summary-card dl {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .compare-title {
    font-size: 28px;
    white-space: normal;
  }

  .compare-summary-card dl {
    grid-template-columns: 1fr;
  }

  .indicator-panel {
    padding: 18px;
  }

  .perspective-tabs {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .metric-row {
    grid-template-areas:
      "result result"
      "left right";
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .metric-result {
    border-bottom: 1px solid var(--line);
  }

  .metric-value.left,
  .metric-value.right {
    min-height: 100px;
    border-left: 0;
    border-right: 0;
  }

  .metric-value.left {
    border-right: 1px solid var(--line);
  }

  .professional-compare .compare-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .compare-row.header {
    display: none;
  }
}
</style>
