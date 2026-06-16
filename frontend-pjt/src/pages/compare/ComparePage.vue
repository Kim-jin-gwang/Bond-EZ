<script setup>
import { computed } from 'vue'
import { bonds } from '../../data/bonds'

const props = defineProps({
  compareBonds: {
    type: Array,
    default: () => [],
  },
})

const displayedBonds = computed(() => {
  if (props.compareBonds.length === 2) {
    return props.compareBonds
  }

  return bonds.slice(0, 2)
})

const leftBond = computed(() => displayedBonds.value[0])
const rightBond = computed(() => displayedBonds.value[1])

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

const quickJudgements = computed(() => [
  {
    label: '수익률 우위',
    value: pickHigher(leftBond.value.yieldValue, rightBond.value.yieldValue),
    helper: '매수수익률이 높은 채권',
    tone: 'return',
  },
  {
    label: '만기 부담 낮음',
    value: pickLower(leftBond.value.maturityYears, rightBond.value.maturityYears),
    helper: '잔존만기가 짧은 채권',
    tone: 'stability',
  },
  {
    label: '금리 민감도 낮음',
    value: pickLower(leftBond.value.durationValue, rightBond.value.durationValue),
    helper: '듀레이션이 짧아 가격 변동 부담이 낮은 채권',
    tone: 'risk',
  },
])

const gptSummary = computed(() => {
  const higherYieldBond = leftBond.value.yieldValue >= rightBond.value.yieldValue ? leftBond.value : rightBond.value
  const lowerDurationBond = leftBond.value.durationValue <= rightBond.value.durationValue ? leftBond.value : rightBond.value
  const saferRatingBond = getWinner(leftBond.value.rating, rightBond.value.rating, 'rating') === 'right'
    ? rightBond.value
    : leftBond.value
  const hasCallable = displayedBonds.value.filter((bond) => bond.optionType === 'CALL')

  return {
    headline: `두 채권은 수익률, 신용등급, 만기, 듀레이션, 옵션 조건에서 차이가 있으므로 투자 목적과 보유 기간에 맞춰 추가 확인이 필요합니다.`,
    bullets: [
      `수익률만 보면 ${higherYieldBond.shortName}의 매수수익률이 ${higherYieldBond.buyYield}로 더 높습니다. 다만 높은 수익률은 신용위험, 유동성, 옵션 조건과 함께 확인해야 합니다.`,
      `금리 민감도는 ${lowerDurationBond.shortName}의 듀레이션이 ${lowerDurationBond.duration}로 더 낮아 상대적으로 작게 나타납니다.`,
      `신용등급 기준으로는 ${saferRatingBond.shortName}이 더 높은 안정성 지표를 보입니다. 단, 신용등급은 원리금 상환을 보장하지 않습니다.`,
      hasCallable.length
        ? `${hasCallable.map((bond) => bond.shortName).join(', ')}은 CALL 옵션이 있으므로 행사 가능일, 조기상환 조건, 재투자 위험을 확인해야 합니다.`
        : '두 채권 모두 별도 CALL 옵션 항목은 확인되지 않습니다.',
    ],
    conclusion: '이 요약은 투자 권유나 매수 추천이 아니라 비교 데이터 해석을 돕기 위한 참고 정보입니다. 실제 투자 전에는 본인의 투자 목적, 위험 감수 성향, 보유 가능 기간, 세금 및 수수료를 함께 검토해야 합니다.',
  }
})

function row(label, key, compareType = null, suffix = '') {
  return {
    label,
    left: formatValue(leftBond.value[key], suffix),
    right: formatValue(rightBond.value[key], suffix),
    winner: getWinner(leftBond.value[key], rightBond.value[key], compareType),
  }
}

function customRow(label, getter) {
  return {
    label,
    left: getter(leftBond.value),
    right: getter(rightBond.value),
    winner: null,
  }
}

function formatValue(value, suffix = '') {
  if (value === null || value === undefined || value === '') {
    return '-'
  }

  return suffix ? `${value}${suffix}` : value
}

function getWinner(leftValue, rightValue, compareType) {
  if (!compareType) return null

  if (compareType === 'rating') {
    const order = ['국채', 'AAA', 'AA', 'A', 'BBB', 'BB', 'B']
    const leftIndex = order.findIndex((item) => String(leftValue).startsWith(item))
    const rightIndex = order.findIndex((item) => String(rightValue).startsWith(item))
    if (leftIndex === rightIndex) return null
    if (leftIndex === -1) return 'right'
    if (rightIndex === -1) return 'left'
    return leftIndex < rightIndex ? 'left' : 'right'
  }

  const leftNumber = toNumber(leftValue)
  const rightNumber = toNumber(rightValue)

  if (leftNumber === rightNumber) return null

  if (compareType.startsWith('higher')) {
    return leftNumber > rightNumber ? 'left' : 'right'
  }

  if (compareType.startsWith('lower')) {
    return leftNumber < rightNumber ? 'left' : 'right'
  }

  if (compareType === 'change') {
    return leftNumber > rightNumber ? 'left' : 'right'
  }

  return null
}

function toNumber(value) {
  return Number(String(value).replace(/[^0-9.-]/g, '')) || 0
}

function pickHigher(leftValue, rightValue) {
  if (leftValue === rightValue) return '동일'
  return leftValue > rightValue ? leftBond.value.shortName : rightBond.value.shortName
}

function pickLower(leftValue, rightValue) {
  if (leftValue === rightValue) return '동일'
  return leftValue < rightValue ? leftBond.value.shortName : rightBond.value.shortName
}
</script>

<template>
  <section class="page compare-page">
    <div class="page-heading compact">
      <p class="eyebrow">채권 비교</p>
      <h1 class="compare-title">{{ leftBond.shortName }} vs {{ rightBond.shortName }}</h1>
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

    <section class="judgement-grid">
      <article v-for="item in quickJudgements" :key="item.label" :class="item.tone">
        <span class="winner-label">우위</span>
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.helper }}</small>
      </article>
    </section>

    <section class="gpt-summary-panel">
      <header>
        <div>
          <p class="eyebrow">AI Compare Summary</p>
          <h2>비교 요약</h2>
        </div>
        <span>참고용</span>
      </header>
      <p class="summary-headline">{{ gptSummary.headline }}</p>
      <ul>
        <li v-for="item in gptSummary.bullets" :key="item">{{ item }}</li>
      </ul>
      <div class="summary-conclusion">
        <strong>유의사항</strong>
        <p>{{ gptSummary.conclusion }}</p>
      </div>
    </section>

    <section v-for="section in compareSections" :key="section.title" class="compare-section">
      <header>
        <div>
          <p class="eyebrow">{{ section.caption }}</p>
          <h2>{{ section.title }}</h2>
        </div>
      </header>

      <div class="compare-table professional-compare">
        <div class="compare-row header">
          <span>항목</span>
          <strong>{{ leftBond.shortName }}</strong>
          <strong>{{ rightBond.shortName }}</strong>
        </div>
        <div v-for="item in section.rows" :key="`${section.title}-${item.label}`" class="compare-row">
          <span>{{ item.label }}</span>
          <strong :class="{ better: item.winner === 'left' }">{{ item.left }}</strong>
          <strong :class="{ better: item.winner === 'right' }">{{ item.right }}</strong>
        </div>
      </div>
    </section>
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
  font-size: clamp(30px, 3.4vw, 46px);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compare-summary-grid,
.judgement-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.compare-summary-card,
.judgement-grid article,
.gpt-summary-panel,
.compare-section {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
  box-shadow: var(--shadow);
}

.compare-summary-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: end;
  padding: 22px;
}

.compare-summary-card span,
.compare-summary-card p,
.compare-summary-card dt,
.judgement-grid span,
.judgement-grid small {
  color: var(--muted);
  font-size: 13px;
}

.compare-summary-card h2 {
  margin: 8px 0;
  font-size: 22px;
}

.compare-summary-card p {
  margin: 0;
}

.compare-summary-card dl {
  display: grid;
  grid-template-columns: repeat(3, minmax(86px, 1fr));
  gap: 10px;
  margin: 0;
}

.compare-summary-card dt,
.compare-summary-card dd {
  margin: 0;
}

.compare-summary-card dd {
  margin-top: 4px;
  color: var(--primary-dark);
  font-size: 22px;
  font-weight: 900;
}

.judgement-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.judgement-grid article {
  position: relative;
  display: grid;
  gap: 6px;
  overflow: hidden;
  padding: 18px;
}

.judgement-grid article::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 5px;
  background: var(--primary);
}

.judgement-grid article.return::before {
  background: var(--good);
}

.judgement-grid article.stability::before {
  background: var(--primary);
}

.judgement-grid article.risk::before {
  background: var(--accent);
}

.winner-label {
  width: fit-content;
  border-radius: 4px;
  padding: 3px 7px;
  color: white !important;
  background: var(--primary);
  font-size: 11px !important;
  font-weight: 900;
}

.judgement-grid article.return .winner-label {
  background: var(--good);
}

.judgement-grid article.risk .winner-label {
  background: var(--accent);
}

.judgement-grid strong {
  color: var(--primary-dark);
  font-size: 24px;
}

.gpt-summary-panel {
  display: grid;
  gap: 14px;
  padding: 22px;
  border-left: 5px solid var(--primary);
}

.gpt-summary-panel header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
}

.gpt-summary-panel header h2,
.gpt-summary-panel p,
.gpt-summary-panel ul {
  margin-bottom: 0;
}

.gpt-summary-panel header > span {
  border-radius: 4px;
  padding: 4px 8px;
  color: var(--primary);
  background: #e8f3f4;
  font-size: 12px;
  font-weight: 900;
}

.summary-headline {
  color: var(--text);
  font-size: 18px;
  font-weight: 900;
  line-height: 1.55;
}

.gpt-summary-panel ul {
  display: grid;
  gap: 8px;
  padding-left: 20px;
}

.gpt-summary-panel li {
  color: var(--text);
  line-height: 1.6;
  word-break: keep-all;
}

.summary-conclusion {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border: 1px solid #d7e7e9;
  border-radius: 8px;
  background: #f4fafb;
}

.summary-conclusion strong {
  color: var(--primary-dark);
}

.summary-conclusion p {
  line-height: 1.65;
}

.compare-section {
  overflow: hidden;
}

.compare-section header {
  padding: 20px 22px 14px;
  border-bottom: 1px solid var(--line);
}

.compare-section h2 {
  margin-bottom: 0;
}

.professional-compare {
  overflow: hidden;
  border: 0;
  border-radius: 0;
  box-shadow: none;
}

.professional-compare .compare-row {
  grid-template-columns: 0.7fr 1fr 1fr;
  min-height: 54px;
  align-items: center;
}

.compare-row span,
.compare-row strong {
  word-break: keep-all;
}

.compare-row strong {
  font-size: 14px;
}

.compare-row.header strong {
  color: var(--primary-dark);
}

.better {
  display: inline-flex;
  width: fit-content;
  border-radius: 6px;
  padding: 4px 8px;
  color: var(--good);
  background: #e7f6f0;
}

@media (max-width: 920px) {
  .compare-summary-grid,
  .judgement-grid,
  .compare-summary-card {
    grid-template-columns: 1fr;
  }

  .compare-summary-card dl {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .professional-compare .compare-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .compare-row.header {
    display: none;
  }
}
</style>
