<script setup>
import { computed, ref } from 'vue'
import { selectedBond } from '../../data/bonds'

const investmentAmount = ref(10000000)
const purchaseDate = ref('2026-06-07')
const purchasePrice = ref(Number(selectedBond.price.replaceAll(',', '')))
const holdingToMaturity = ref(true)

const taxRate = 0.154
const faceValuePerUnit = 10000

const couponRate = computed(() => Number.parseFloat(selectedBond.coupon) / 100)
const buyYieldRate = computed(() => selectedBond.yieldValue / 100)
const paymentMonths = computed(() => Number.parseInt(selectedBond.interestCycle, 10) || 12)
const paymentsPerYear = computed(() => Math.max(1, 12 / paymentMonths.value))
const yearsToMaturity = computed(() => selectedBond.maturityYears)
const purchaseUnits = computed(() => Math.floor(investmentAmount.value / purchasePrice.value))
const investedPrincipal = computed(() => purchaseUnits.value * purchasePrice.value)
const faceAmount = computed(() => purchaseUnits.value * faceValuePerUnit)
const annualCoupon = computed(() => faceAmount.value * couponRate.value)
const periodCoupon = computed(() => annualCoupon.value / paymentsPerYear.value)
const totalPayments = computed(() => Math.round(yearsToMaturity.value * paymentsPerYear.value))
const grossInterest = computed(() => periodCoupon.value * totalPayments.value)
const taxAmount = computed(() => grossInterest.value * taxRate)
const afterTaxInterest = computed(() => grossInterest.value - taxAmount.value)
const redemptionGain = computed(() => faceAmount.value - investedPrincipal.value)
const maturityProfit = computed(() => afterTaxInterest.value + redemptionGain.value)
const maturityReturn = computed(() =>
  investedPrincipal.value ? (maturityProfit.value / investedPrincipal.value) * 100 : 0,
)

const summaryMetrics = computed(() => [
  { label: '매수수익률(YTM)', value: selectedBond.buyYield },
  { label: '만기', value: selectedBond.maturity },
  { label: '신용등급', value: selectedBond.rating },
  { label: '세후 예상 수익', value: formatCurrency(afterTaxInterest.value) },
])

const detailRows = computed(() => [
  ['종목명', selectedBond.name, '표준코드', selectedBond.code],
  ['채권유형', selectedBond.type, '시장구분', selectedBond.marketType],
  ['신용등급', selectedBond.rating, '등급그룹', selectedBond.ratingGroup],
  ['매수수익률', selectedBond.buyYield, '매도수익률', selectedBond.sellYield],
  ['현재 가격', selectedBond.price, '가격 변동', selectedBond.change],
  ['표면금리', selectedBond.coupon, '듀레이션', selectedBond.duration],
  ['만기일', selectedBond.maturity, '잔존만기', `${selectedBond.maturityYears}년`],
  ['이자 지급 주기', selectedBond.interestCycle, '옵션', selectedBond.option],
  ['거래량', selectedBond.volume, 'ISIN', selectedBond.code],
])

const riskSummary = computed(() => [
  {
    title: '신용 위험',
    level: selectedBond.ratingGroup === 'AAA' ? '낮음' : '보통',
    description: `${selectedBond.rating} 등급 기준의 발행사 상환 능력을 확인하세요.`,
  },
  {
    title: '유동성 위험',
    level: selectedBond.volume.includes('억') ? '보통' : '주의',
    description: '거래량이 적으면 원하는 가격에 중도 매도하기 어려울 수 있습니다.',
  },
  {
    title: '금리 변동 위험',
    level: Number.parseFloat(selectedBond.duration) >= 6 ? '주의' : '보통',
    description: '듀레이션이 길수록 금리 변화에 따른 가격 변동이 커집니다.',
  },
  {
    title: '조기상환 위험',
    level: selectedBond.option === 'CALL' ? '확인 필요' : '낮음',
    description: selectedBond.option === 'CALL'
      ? '콜옵션 행사 시 예상보다 빨리 상환될 수 있습니다.'
      : '특별한 조기상환 옵션이 없는 구조입니다.',
  },
])

const resultRows = computed(() => [
  ['매수 가능 수량', `${purchaseUnits.value.toLocaleString()}좌`],
  ['실제 투자 금액', formatCurrency(investedPrincipal.value)],
  ['연 예상 이자', formatCurrency(annualCoupon.value)],
  ['총 예상 이자', formatCurrency(grossInterest.value)],
  ['예상 세금', formatCurrency(taxAmount.value)],
  ['세후 이자 수익', formatCurrency(afterTaxInterest.value)],
  ['만기 상환 차익', formatCurrency(redemptionGain.value)],
  ['만기 총 수익', formatCurrency(maturityProfit.value)],
  ['만기 수익률', `${maturityReturn.value.toFixed(2)}%`],
])

const cashflowRows = computed(() => {
  const rows = []
  const start = new Date(purchaseDate.value)
  const maxRows = Math.min(totalPayments.value, 8)

  for (let index = 1; index <= maxRows; index += 1) {
    const date = new Date(start)
    date.setMonth(date.getMonth() + paymentMonths.value * index)
    rows.push({
      round: `${index}회차`,
      date: date.toISOString().slice(0, 10),
      gross: formatCurrency(periodCoupon.value),
      tax: formatCurrency(periodCoupon.value * taxRate),
      net: formatCurrency(periodCoupon.value * (1 - taxRate)),
    })
  }

  return rows
})

function formatCurrency(value) {
  return `${Math.round(value).toLocaleString()}원`
}
</script>

<template>
  <section class="page detail-page professional-detail">
    <section class="detail-summary">
      <div class="summary-copy">
        <p class="eyebrow">Bond Detail</p>
        <h1>{{ selectedBond.name }}</h1>
        <p>{{ selectedBond.code }} · {{ selectedBond.type }} · {{ selectedBond.rating }} · {{ selectedBond.option }} 옵션</p>
      </div>

      <div class="summary-metrics">
        <article v-for="metric in summaryMetrics" :key="metric.label">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
        </article>
      </div>
    </section>

    <section class="risk-summary-panel">
      <div class="section-title compact-title">
        <div>
          <p class="eyebrow">Risk Overview</p>
          <h2>채권 정보와 리스크 요약</h2>
        </div>
      </div>
      <div class="risk-summary-grid">
        <article v-for="risk in riskSummary" :key="risk.title" class="risk-summary-card">
          <div>
            <span>{{ risk.title }}</span>
            <strong>{{ risk.level }}</strong>
          </div>
          <p>{{ risk.description }}</p>
        </article>
      </div>
      <div class="risk-tags">
        <span v-for="risk in selectedBond.riskTags" :key="risk">#{{ risk }}</span>
      </div>
    </section>

    <section class="bond-info-panel">
      <div class="section-title compact-title">
        <div>
          <p class="eyebrow">Issue Information</p>
          <h2>채권 상세 정보</h2>
        </div>
      </div>

      <div class="bond-info-table-wrap">
        <table class="bond-info-table">
          <tbody>
            <tr v-for="row in detailRows" :key="row.join('-')">
              <th scope="row">{{ row[0] }}</th>
              <td>{{ row[1] }}</td>
              <th scope="row">{{ row[2] }}</th>
              <td>{{ row[3] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="bond-calculator-panel">
      <div class="section-title compact-title">
        <div>
          <p class="eyebrow">Bond Profit Calculator</p>
          <h2>채권 수익 계산기</h2>
        </div>
      </div>

      <div class="calculator-layout">
        <form class="calculator-form">
          <label>
            <span>투자 금액</span>
            <input v-model.number="investmentAmount" type="number" min="0" step="100000" />
          </label>
          <label>
            <span>매수 시작일</span>
            <input v-model="purchaseDate" type="date" />
          </label>
          <label>
            <span>매수 가격</span>
            <input v-model.number="purchasePrice" type="number" min="1" step="1" />
          </label>
          <label class="checkbox-label">
            <input v-model="holdingToMaturity" type="checkbox" />
            <span>만기까지 보유</span>
          </label>
        </form>

        <div class="calculator-result-table-wrap">
          <table class="calculator-result-table">
            <tbody>
              <tr v-for="row in resultRows" :key="row[0]">
                <th scope="row">{{ row[0] }}</th>
                <td>{{ row[1] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="cashflow-table-wrap">
        <h3>이자 지급 기간별 예상 수익</h3>
        <table class="cashflow-table">
          <thead>
            <tr>
              <th>회차</th>
              <th>예상 지급일</th>
              <th>세전 이자</th>
              <th>예상 세금</th>
              <th>세후 이자</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in cashflowRows" :key="row.round">
              <td>{{ row.round }}</td>
              <td>{{ row.date }}</td>
              <td>{{ row.gross }}</td>
              <td>{{ row.tax }}</td>
              <td>{{ row.net }}</td>
            </tr>
          </tbody>
        </table>
        <p class="table-note">
          계산 결과는 표면금리와 단순 세율을 기준으로 한 예시이며, 실제 거래 수수료와 과세 기준에 따라 달라질 수 있습니다.
        </p>
      </div>
    </section>
  </section>
</template>

<style scoped>
.professional-detail {
  display: grid;
  gap: 22px;
}

.detail-summary,
.risk-summary-panel,
.bond-info-panel,
.bond-calculator-panel {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.detail-summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(420px, 0.9fr);
  gap: 24px;
  align-items: stretch;
  padding: 26px;
  background:
    linear-gradient(135deg, rgba(31, 111, 120, 0.08), rgba(255, 255, 255, 0.82)),
    var(--surface);
}

.summary-copy h1 {
  margin-bottom: 10px;
  font-size: clamp(28px, 4vw, 42px);
}

.summary-copy p:not(.eyebrow) {
  margin-bottom: 0;
}

.summary-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.summary-metrics article,
.risk-summary-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.78);
}

.summary-metrics article {
  display: grid;
  gap: 8px;
  padding: 18px;
}

.summary-metrics span,
.risk-summary-card span,
.table-note {
  color: var(--muted);
  font-size: 13px;
}

.summary-metrics strong {
  color: var(--primary-dark);
  font-size: 24px;
}

.risk-summary-panel,
.bond-info-panel,
.bond-calculator-panel {
  padding: 22px;
}

.compact-title {
  margin-bottom: 16px;
}

.compact-title h2 {
  margin-bottom: 0;
}

.risk-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.risk-summary-card {
  padding: 16px;
}

.risk-summary-card div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 10px;
}

.risk-summary-card strong {
  color: var(--primary);
  font-size: 15px;
}

.risk-summary-card p {
  margin-bottom: 0;
  font-size: 13px;
  line-height: 1.55;
}

.bond-info-table-wrap,
.calculator-result-table-wrap,
.cashflow-table-wrap {
  overflow-x: auto;
}

.bond-info-table,
.calculator-result-table,
.cashflow-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
  background: white;
}

.bond-info-table th,
.bond-info-table td,
.calculator-result-table th,
.calculator-result-table td,
.cashflow-table th,
.cashflow-table td {
  padding: 14px 16px;
  border: 1px solid var(--line);
}

.bond-info-table th,
.calculator-result-table th,
.cashflow-table th {
  color: var(--text);
  background: #f5f8fb;
  font-size: 14px;
  font-weight: 800;
}

.bond-info-table td,
.calculator-result-table td,
.cashflow-table td {
  color: var(--text);
  font-size: 14px;
}

.calculator-layout {
  display: grid;
  grid-template-columns: minmax(280px, 0.85fr) minmax(420px, 1.15fr);
  gap: 18px;
  align-items: start;
}

.calculator-form {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.calculator-form label {
  color: var(--text);
  font-weight: 700;
}

.checkbox-label {
  display: flex;
  grid-template-columns: none;
  gap: 10px;
  align-items: center;
}

.checkbox-label input {
  min-height: auto;
}

.calculator-result-table {
  min-width: 420px;
}

.calculator-result-table td,
.cashflow-table td {
  text-align: right;
  font-weight: 800;
}

.calculator-result-table th,
.cashflow-table th:first-child,
.cashflow-table td:first-child,
.cashflow-table th:nth-child(2),
.cashflow-table td:nth-child(2) {
  text-align: left;
}

.cashflow-table-wrap {
  margin-top: 20px;
}

.cashflow-table-wrap h3 {
  margin-bottom: 12px;
  font-size: 18px;
}

.table-note {
  margin: 12px 0 0;
}

@media (max-width: 960px) {
  .detail-summary,
  .calculator-layout {
    grid-template-columns: 1fr;
  }

  .risk-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .summary-metrics,
  .risk-summary-grid {
    grid-template-columns: 1fr;
  }

  .detail-summary,
  .risk-summary-panel,
  .bond-info-panel,
  .bond-calculator-panel {
    padding: 18px;
  }
}
</style>
