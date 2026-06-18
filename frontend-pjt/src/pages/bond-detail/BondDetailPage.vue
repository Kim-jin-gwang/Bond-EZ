<script setup>
import { computed, ref } from 'vue'
import { getSelectedBond } from '../../api/bonds'

const selectedBond = getSelectedBond()

const investmentAmount = ref(1000000)
const purchaseDate = ref('2026-06-14')
const purchasePrice = ref(selectedBond.priceValue)
const scenario = ref(selectedBond.optionType === 'CALL' ? 'call_1' : 'maturity')
const investorType = ref('개인')
const taxMode = ref('종합과세')

const taxRate = 0.154
const faceValuePerUnit = 10000

const investmentAmountText = computed({
  get() {
    return formatNumber(investmentAmount.value)
  },
  set(value) {
    investmentAmount.value = Number(String(value).replace(/[^0-9]/g, '')) || 0
  },
})

const normalizedPrice = computed(() => Number(purchasePrice.value) || selectedBond.priceValue)
const purchaseUnits = computed(() => Math.floor(Number(investmentAmount.value || 0) / normalizedPrice.value))
const investedPrincipal = computed(() => purchaseUnits.value * normalizedPrice.value)
const faceAmount = computed(() => purchaseUnits.value * faceValuePerUnit)
const paymentMonths = computed(() => Number(selectedBond.paymentCycleMonths) || 12)
const paymentsPerYear = computed(() => Math.max(1, 12 / paymentMonths.value))
const periodCoupon = computed(() => faceAmount.value * (selectedBond.couponRate / 100) / paymentsPerYear.value)
const scenarioDate = computed(() => {
  if (scenario.value === 'call_1' && selectedBond.optionExercise?.startDate1) {
    return selectedBond.optionExercise.startDate1
  }

  if (scenario.value === 'call_2' && selectedBond.optionExercise?.startDate2) {
    return selectedBond.optionExercise.startDate2
  }

  return selectedBond.maturityDate
})
const investmentDays = computed(() => daysBetween(purchaseDate.value, scenarioDate.value))
const investmentPeriodText = computed(() => formatPeriod(investmentDays.value))
const expectedPeriods = computed(() => Math.max(1, Math.ceil(investmentDays.value / 365 * paymentsPerYear.value)))
const totalGrossInterest = computed(() => periodCoupon.value * expectedPeriods.value)
const totalTax = computed(() => totalGrossInterest.value * taxRate)
const afterTaxInterest = computed(() => totalGrossInterest.value - totalTax.value)
const redemptionAmount = computed(() => faceAmount.value * parsePercent(selectedBond.maturityRedemptionRate))
const redemptionGain = computed(() => redemptionAmount.value - investedPrincipal.value)
const expectedProfit = computed(() => afterTaxInterest.value + redemptionGain.value)
const totalReceipts = computed(() => investedPrincipal.value + expectedProfit.value)
const afterTaxReturnRate = computed(() =>
  investedPrincipal.value ? (expectedProfit.value / investedPrincipal.value) * 100 : 0,
)

const scenarioOptions = computed(() => {
  const options = [{ value: 'maturity', label: '만기상환' }]

  if (selectedBond.optionExercise?.startDate1) {
    options.unshift({ value: 'call_1', label: 'CALL 1차' })
  }

  if (selectedBond.optionExercise?.startDate2) {
    options.unshift({ value: 'call_2', label: 'CALL 2차' })
  }

  return options
})

const summaryMetrics = computed(() => [
  { label: '매수수익률', value: selectedBond.buyYield },
  { label: '표면금리', value: selectedBond.coupon },
  { label: '신용등급', value: selectedBond.rating },
  { label: '다음 옵션일', value: selectedBond.optionExercise?.startDate1 || '-' },
])

const issueRows = computed(() => [
  ['표준코드', selectedBond.code, '단축코드', selectedBond.shortCode],
  ['종목명', selectedBond.name, '종목약명', selectedBond.shortName],
  ['발행기관', selectedBond.issuer, '산업', selectedBond.industry],
  ['채권종류', selectedBond.type, '선후순위', selectedBond.seniority],
  ['발행일', selectedBond.issueDate, '상장일', selectedBond.listingDate],
  ['만기일', selectedBond.maturityDate, '발행금액', `${selectedBond.issueAmount}원`],
  ['상환방법', selectedBond.redemptionMethod, '만기상환율', selectedBond.maturityRedemptionRate],
  ['대표주관회사', selectedBond.underwriter, '보증여부', selectedBond.guaranteeStatus],
])

const interestRows = computed(() => [
  ['이자방식', selectedBond.interestType, '이자지급방법', selectedBond.interestPaymentMethod],
  ['표면이율', selectedBond.coupon, '이자주기', selectedBond.interestCycle],
  ['지급단위월수', `${selectedBond.interestPaymentUnitMonths}개월`, '계산월수', `${selectedBond.interestCalculationMonths}개월`],
  ['선후급구분', selectedBond.interestPrePostType, '최초지급일', selectedBond.firstInterestPaymentDate],
  ['지급기준', selectedBond.interestPaymentBasis, '월말구분', selectedBond.interestMonthEndType],
])

const optionRows = computed(() => [
  ['옵션종류', selectedBond.option, '행사사유', selectedBond.optionExercise?.reason || '-'],
  ['1차 행사개시일', selectedBond.optionExercise?.startDate1 || '-', '1차 행사종료일', selectedBond.optionExercise?.endDate1 || '-'],
  ['2차 행사개시일', selectedBond.optionExercise?.startDate2 || '-', '2차 행사종료일', selectedBond.optionExercise?.endDate2 || '-'],
  ['특이상환조건', selectedBond.earlyRedemptionDescription || '-', '상환 시나리오', selectedScenarioLabel.value],
])

const marketRows = computed(() => [
  ['현재가', selectedBond.price, '대용가격', selectedBond.substitutePrice],
  ['매수수익률', selectedBond.buyYield, '매도수익률', selectedBond.sellYield],
  ['만기수익률', selectedBond.ytm, '듀레이션', selectedBond.duration],
  ['거래량', selectedBond.volume, '등락률', selectedBond.change],
])

const selectedScenarioLabel = computed(() =>
  scenarioOptions.value.find((item) => item.value === scenario.value)?.label || '만기상환',
)

const tradeSummaryRows = computed(() => [
  ['매수일자', purchaseDate.value, '매도일자', scenarioDate.value],
  ['매수수익률', selectedBond.buyYield, '매도수익률', scenario.value.startsWith('call') ? '0.0000%' : selectedBond.sellYield],
  ['매수수량', `${purchaseUnits.value.toLocaleString()}좌`, '매도수량', `${purchaseUnits.value.toLocaleString()}좌`],
  ['단가', normalizedPrice.value.toLocaleString(undefined, { minimumFractionDigits: 2 }), '상환단가', faceValuePerUnit.toLocaleString()],
  ['매수금액', formatCurrency(investedPrincipal.value), '상환금액', formatCurrency(redemptionAmount.value)],
  ['매수불가연동계수', '0.0000', '매도불가연동계수', '0.0000'],
])

const profitRows = computed(() => [
  ['만기상환금액', formatCurrency(redemptionAmount.value), '의제 세금', formatCurrency(0)],
  ['총과표', formatCurrency(totalGrossInterest.value), '원천징수금액', formatCurrency(totalTax.value)],
  ['보유기간과표', formatCurrency(totalGrossInterest.value), '세후순투자수익률', `${afterTaxReturnRate.value.toFixed(2)}%`],
  ['세후실수령액', formatCurrency(totalReceipts.value), '세전운용수익률', `${grossReturnRate.value.toFixed(2)}%`],
])

const bondConditionItems = computed(() => [
  { label: '매출일자', value: '0000/00/00' },
  { label: '발행일자', value: selectedBond.issueDate },
  { label: '만기일자', value: scenarioDate.value },
  { label: '신용등급', value: selectedBond.rating },
  { label: '이자지급유형', value: selectedBond.interestPaymentMethod },
  { label: '표면이율', value: selectedBond.coupon },
  { label: '할인율', value: '0.0000%' },
  { label: '만기보장수익률', value: selectedBond.ytm },
  { label: '원금상환율', value: selectedBond.maturityRedemptionRate },
])

const profitItems = computed(() => [
  { label: '만기상환금액', value: formatCurrency(redemptionAmount.value) },
  { label: '총과표', value: formatCurrency(totalGrossInterest.value) },
  { label: '보유기간과표', value: formatCurrency(totalGrossInterest.value) },
  { label: '세후실수령액', value: formatCurrency(totalReceipts.value), highlight: true },
  { label: '의제 세금', value: formatCurrency(0) },
  { label: '원천징수금액', value: formatCurrency(totalTax.value) },
  { label: '세후순투자수익률', value: `${afterTaxReturnRate.value.toFixed(2)}%`, highlight: true },
  { label: '세전운용수익률', value: `${grossReturnRate.value.toFixed(2)}%` },
])

const grossReturnRate = computed(() =>
  investedPrincipal.value ? ((totalGrossInterest.value + redemptionGain.value) / investedPrincipal.value) * 100 : 0,
)

const cashflowRows = computed(() => {
  const rows = []
  const start = new Date(purchaseDate.value)
  const end = new Date(scenarioDate.value)
  const firstPayDate = new Date(selectedBond.firstInterestPaymentDate)
  let cursor = firstPayDate > start ? firstPayDate : addMonths(start, paymentMonths.value)

  while (cursor <= end && rows.length < 12) {
    const periodStart = addMonths(cursor, -paymentMonths.value)
    const gross = periodCoupon.value
    const incomeTax = gross * 0.14
    const localTax = incomeTax * 0.1
    const specialTax = 0
    const net = gross - incomeTax - localTax - specialTax

    rows.push({
      startDate: toDateString(periodStart < start ? start : periodStart),
      endDate: toDateString(cursor),
      holdingType: '신보유',
      taxBaseTotal: formatNumber(gross),
      ownedTaxBase: formatNumber(gross),
      unownedTaxBase: '0',
      taxRate: '14.00',
      incomeTax: formatNumber(incomeTax),
      localTax: formatNumber(localTax),
      specialTax: '0',
      netAmount: formatNumber(net),
    })

    cursor = addMonths(cursor, paymentMonths.value)
  }

  return rows
})

function parsePercent(value) {
  return Number(String(value).replace('%', '')) / 100 || 1
}

function addMonths(date, months) {
  const next = new Date(date)
  next.setMonth(next.getMonth() + months)
  return next
}

function daysBetween(start, end) {
  const diff = new Date(end).getTime() - new Date(start).getTime()
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)))
}

function formatPeriod(days) {
  const years = Math.floor(days / 365)
  const months = Math.floor((days % 365) / 30)
  const restDays = (days % 365) % 30
  return `${days.toLocaleString()}일 (${years}년 ${months}월 ${restDays}일)`
}

function toDateString(date) {
  return date.toISOString().slice(0, 10)
}

function formatNumber(value) {
  return Math.round(value).toLocaleString()
}

function formatCurrency(value) {
  return `${formatNumber(value)}원`
}
</script>

<template>
  <section class="page detail-page erd-detail">
    <section class="detail-summary">
      <div class="summary-copy">
        <p class="eyebrow">Bond Detail</p>
        <h1>{{ selectedBond.name }}</h1>
        <p>{{ selectedBond.code }} · {{ selectedBond.shortCode }} · {{ selectedBond.issuer }} · {{ selectedBond.option }} 옵션</p>
      </div>

      <div class="summary-metrics">
        <article v-for="metric in summaryMetrics" :key="metric.label">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
        </article>
      </div>
    </section>

    <section class="detail-grid">
      <article class="info-panel wide">
        <div class="section-title compact-title">
          <div>
            <p class="eyebrow">Issue Information</p>
            <h2>발행 및 상환 정보</h2>
          </div>
        </div>
        <InfoTable :rows="issueRows" />
      </article>

      <article class="info-panel">
        <div class="section-title compact-title">
          <div>
            <p class="eyebrow">Interest Rule</p>
            <h2>이자 지급 상세 조건</h2>
          </div>
        </div>
        <InfoTable :rows="interestRows" />
      </article>

      <article class="info-panel">
        <div class="section-title compact-title">
          <div>
            <p class="eyebrow">Option Exercise</p>
            <h2>옵션 행사 가능일</h2>
          </div>
        </div>
        <InfoTable :rows="optionRows" />
      </article>

      <article class="info-panel wide">
        <div class="section-title compact-title">
          <div>
            <p class="eyebrow">Market Data</p>
            <h2>가격 및 수익률 기준 데이터</h2>
          </div>
        </div>
        <InfoTable :rows="marketRows" />
      </article>
    </section>

    <section class="cashflow-calculator">
      <header class="cashflow-header">
        <div>
          <p class="eyebrow">Expected Cashflow</p>
          <h2>채권 예상 현금흐름표</h2>
        </div>
        <div class="scenario-switch">
          <button
            v-for="item in scenarioOptions"
            :key="item.value"
            :class="{ active: scenario === item.value }"
            type="button"
            @click="scenario = item.value"
          >
            {{ item.label }}
          </button>
        </div>
      </header>

      <section class="cashflow-top">
        <form class="condition-panel">
          <h3>투자 조건</h3>
          <label>
            <span>투자수량 기준 금액</span>
            <input v-model="investmentAmountText" type="text" inputmode="numeric" />
          </label>
          <label>
            <span>매수일자</span>
            <input v-model="purchaseDate" type="date" />
          </label>
          <label>
            <span>매수단가</span>
            <input v-model.number="purchasePrice" type="number" min="1" step="0.01" />
          </label>
          <div class="condition-row">
            <label>
              <span>투자자구분</span>
              <select v-model="investorType">
                <option>개인</option>
                <option>법인</option>
              </select>
            </label>
            <label>
              <span>과세구분</span>
              <select v-model="taxMode">
                <option>종합과세</option>
                <option>분리과세</option>
                <option>비과세</option>
              </select>
            </label>
          </div>
        </form>

        <div class="cashflow-result-stack">
          <div class="bond-condition-panel">
            <h3>채권 조건</h3>
            <dl class="condition-matrix">
              <div v-for="item in bondConditionItems" :key="item.label">
                <dt>{{ item.label }}</dt>
                <dd>{{ item.value }}</dd>
              </div>
            </dl>
          </div>

          <div class="profit-panel">
            <div class="panel-heading-row">
              <h3>투자수익</h3>
              <strong class="period-chip">투자기간 {{ investmentPeriodText }}</strong>
            </div>
            <div class="profit-metric-grid">
              <article v-for="item in profitItems" :key="item.label" :class="{ highlight: item.highlight }">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section class="trade-panel">
        <h3>매수/매도상환내역</h3>
        <table>
          <tbody>
            <tr v-for="row in tradeSummaryRows" :key="row.join('-')">
              <th>{{ row[0] }}</th>
              <td>{{ row[1] }}</td>
              <th>{{ row[2] }}</th>
              <td>{{ row[3] }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="cashflow-detail-panel">
        <div class="cashflow-detail-title">
          <h3>과표구간별 세부 내역</h3>
          <span>단가 기준 계산 결과는 실제 매수/매도 수수료와 상이할 수 있습니다.</span>
        </div>
        <div class="cashflow-grid-wrap">
          <table class="cashflow-grid">
            <thead>
              <tr>
                <th colspan="2">과표구간</th>
                <th colspan="2">보유구분</th>
                <th rowspan="2">총과표</th>
                <th colspan="2">과표구분</th>
                <th rowspan="2">세율</th>
                <th colspan="3">세액</th>
                <th rowspan="2">실수령액</th>
              </tr>
              <tr>
                <th>시작일자</th>
                <th>종료일자</th>
                <th>보유</th>
                <th>미보유</th>
                <th>보유</th>
                <th>미보유</th>
                <th>소득세</th>
                <th>지방소득세</th>
                <th>농특세</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in cashflowRows" :key="`${row.startDate}-${row.endDate}`">
                <td>{{ row.startDate }}</td>
                <td>{{ row.endDate }}</td>
                <td>{{ row.holdingType }}</td>
                <td></td>
                <td>{{ row.taxBaseTotal }}</td>
                <td>{{ row.ownedTaxBase }}</td>
                <td>{{ row.unownedTaxBase }}</td>
                <td>{{ row.taxRate }}</td>
                <td>{{ row.incomeTax }}</td>
                <td>{{ row.localTax }}</td>
                <td>{{ row.specialTax }}</td>
                <td>{{ row.netAmount }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </section>
  </section>
</template>

<script>
export default {
  components: {
    InfoTable: {
      props: {
        rows: {
          type: Array,
          required: true,
        },
      },
      template: `
        <div class="info-table-wrap">
          <table class="info-table">
            <tbody>
              <tr v-for="row in rows" :key="row.join('-')">
                <th scope="row">{{ row[0] }}</th>
                <td>{{ row[1] }}</td>
                <th scope="row">{{ row[2] }}</th>
                <td>{{ row[3] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      `,
    },
  },
}
</script>

<style scoped>
.erd-detail {
  display: grid;
  gap: 22px;
}

.detail-summary,
.info-panel,
.cashflow-calculator {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.detail-summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 0.75fr);
  gap: 24px;
  align-items: stretch;
  padding: 26px;
  background:
    linear-gradient(135deg, rgba(31, 111, 120, 0.08), rgba(255, 255, 255, 0.86)),
    var(--surface);
}

.summary-copy h1 {
  margin-bottom: 10px;
  font-size: clamp(28px, 4vw, 40px);
}

.summary-copy p:not(.eyebrow) {
  margin-bottom: 0;
}

.summary-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.summary-metrics article {
  display: grid;
  gap: 8px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.78);
}

.summary-metrics span,
.cashflow-detail-title span {
  color: var(--muted);
  font-size: 13px;
}

.summary-metrics strong {
  color: var(--primary-dark);
  font-size: 22px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.info-panel,
.cashflow-calculator {
  padding: 22px;
}

.info-panel.wide {
  grid-column: 1 / -1;
}

.compact-title {
  margin-bottom: 14px;
}

.compact-title h2 {
  margin-bottom: 0;
}

:deep(.info-table-wrap),
.cashflow-grid-wrap {
  overflow-x: auto;
}

:deep(.info-table),
.profit-panel table,
.trade-panel table,
.cashflow-grid {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

:deep(.info-table) {
  min-width: 760px;
}

:deep(.info-table th),
:deep(.info-table td),
.profit-panel th,
.profit-panel td,
.trade-panel th,
.trade-panel td,
.cashflow-grid th,
.cashflow-grid td {
  padding: 11px 12px;
  border: 1px solid var(--line);
  font-size: 13px;
}

:deep(.info-table th),
.profit-panel th,
.trade-panel th,
.cashflow-grid th {
  color: var(--text);
  background: #f5f8fb;
  font-weight: 900;
}

:deep(.info-table td),
.profit-panel td,
.trade-panel td,
.cashflow-grid td {
  color: var(--text);
  font-weight: 700;
}

.cashflow-header,
.cashflow-detail-title {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: end;
  margin-bottom: 16px;
}

.cashflow-header h2,
.cashflow-detail-title h3 {
  margin-bottom: 0;
}

.scenario-switch {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.scenario-switch button {
  min-height: 36px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 12px;
  color: var(--text);
  background: white;
  font-size: 13px;
  font-weight: 900;
}

.scenario-switch button.active {
  border-color: var(--primary);
  color: white;
  background: var(--primary);
}

.cashflow-top {
  display: grid;
  grid-template-columns: minmax(260px, 0.7fr) minmax(0, 1.9fr);
  gap: 14px;
  align-items: stretch;
}

.condition-panel,
.bond-condition-panel,
.profit-panel,
.trade-panel,
.cashflow-detail-panel {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fbfdff;
}

.condition-panel,
.bond-condition-panel,
.profit-panel,
.trade-panel,
.cashflow-detail-panel {
  padding: 16px;
}

.condition-panel {
  display: grid;
  gap: 12px;
  align-content: start;
}

.condition-panel h3,
.bond-condition-panel h3,
.profit-panel h3,
.trade-panel h3 {
  margin-bottom: 8px;
  font-size: 16px;
}

.cashflow-result-stack {
  display: grid;
  grid-template-rows: auto auto;
  gap: 14px;
  min-width: 0;
}

.condition-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.condition-matrix {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 0;
}

.condition-matrix div {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
}

.condition-matrix dt,
.condition-matrix dd {
  margin: 0;
  word-break: keep-all;
}

.condition-matrix dt {
  color: var(--muted);
  font-size: 13px;
  font-weight: 800;
}

.condition-matrix dd {
  color: var(--text);
  font-size: 14px;
  font-weight: 900;
}

.panel-heading-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 10px;
}

.period-chip {
  display: inline-flex;
  flex: 0 0 auto;
  border-radius: 6px;
  padding: 5px 9px;
  color: var(--primary-dark);
  background: #e8f3f4;
  font-size: 13px;
  font-weight: 900;
  white-space: nowrap;
}

.profit-metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.profit-metric-grid article {
  display: grid;
  gap: 6px;
  min-width: 0;
  padding: 13px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
}

.profit-metric-grid article.highlight {
  border-color: rgba(31, 111, 120, 0.38);
  background: #f4fafb;
}

.profit-metric-grid span {
  color: var(--muted);
  font-size: 13px;
  font-weight: 800;
  word-break: keep-all;
}

.profit-metric-grid strong {
  color: var(--text);
  font-size: 15px;
  font-weight: 900;
  white-space: nowrap;
}

.profit-metric-grid article.highlight strong {
  color: var(--primary-dark);
}

.trade-panel,
.cashflow-detail-panel {
  margin-top: 14px;
}

.cashflow-grid {
  min-width: 1120px;
}

.cashflow-grid thead tr:first-child th {
  color: white;
  background: #2d6fb7;
}

.cashflow-grid thead tr:first-child th:nth-child(n + 5) {
  background: #c93b3b;
}

.cashflow-grid td {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.cashflow-grid td:nth-child(-n + 4) {
  text-align: left;
}

@media (max-width: 1100px) {
  .cashflow-top,
  .detail-summary {
    grid-template-columns: 1fr;
  }

  .condition-matrix,
  .profit-metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 820px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .cashflow-header,
  .cashflow-detail-title {
    align-items: stretch;
    flex-direction: column;
  }
}

@media (max-width: 640px) {
  .summary-metrics,
  .condition-row,
  .condition-matrix,
  .profit-metric-grid {
    grid-template-columns: 1fr;
  }

  .panel-heading-row {
    align-items: start;
    flex-direction: column;
  }
}
</style>
