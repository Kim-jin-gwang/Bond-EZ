import { cachedQuery } from './cache'
import { apiGet } from './client'

const INDICATOR_META = {
  'treasury-rate': {
    shortTitle: '국고채·미국채',
    summary: '국고채와 미국채 금리를 비교해 시장이 반영하는 장단기 금리 수준을 확인합니다.',
    insight: '장기 금리가 단기 금리보다 높거나 낮은지 함께 보면 금리 방향성과 만기 부담을 판단하는 데 도움이 됩니다.',
  },
  'central-bank-rate': {
    shortTitle: '기준금리',
    summary: '나라별 기준금리와 주요 국채 금리를 함께 확인합니다.',
    insight: '기준금리 차이는 환율, 해외 금리, 국내 채권 금리에도 영향을 줄 수 있어 함께 보는 것이 좋습니다.',
  },
  'credit-rating-yield': {
    shortTitle: '신용등급 금리',
    summary: '신용등급별 평균 수익률을 비교해 등급별 위험 보상 수준을 확인합니다.',
    insight: '등급이 낮을수록 수익률이 높아질 수 있지만, 발행사 재무 상태와 유동성도 함께 확인해야 합니다.',
  },
  'deposit-compare': {
    shortTitle: '예금 비교',
    summary: '은행 예금 금리와 채권 수익률을 비교할 때 기준으로 삼을 수 있는 데이터를 확인합니다.',
    insight: '예금은 원금 보장 여부가 다르기 때문에 채권 수익률과 단순 비교하기보다 투자 기간과 위험을 함께 봐야 합니다.',
  },
  'yield-spread': {
    shortTitle: '장단기 금리차',
    summary: '장기 금리와 단기 금리의 차이를 통해 시장의 경기 전망과 금리 기대를 확인합니다.',
    insight: '금리차가 축소되거나 역전될 때는 장기채 가격 변동 부담과 경기 둔화 가능성을 함께 점검하는 것이 좋습니다.',
  },
  'yield-curve': {
    shortTitle: 'Yield Curve',
    summary: '만기별 금리를 연결해 금리 곡선의 기울기를 확인합니다.',
    insight: '수익률 곡선의 기울기는 시장의 금리 경로와 경기 전망을 읽는 보조 지표로 활용할 수 있습니다.',
  },
}

export function getIndicators() {
  return []
}

export function fetchIndicators() {
  return cachedQuery('indicators:list', async () => {
    try {
      const data = await apiGet('/indicators')
      const summaries = getItems(data)

      if (!summaries.length) {
        return []
      }

      const indicators = await Promise.all(summaries.map(fetchIndicatorDetail))
      return indicators.filter(Boolean)
    } catch {
      return []
    }
  })
}

async function fetchIndicatorDetail(summary) {
  if (!summary?.id || !summary?.endpoint) {
    return null
  }

  try {
    const path = summary.endpoint.replace(/^\/api\/v1/, '')
    const detail = await apiGet(path)
    return normalizeIndicator(summary, getItems(detail))
  } catch {
    return null
  }
}

function normalizeIndicator(summary, rows) {
  const meta = INDICATOR_META[summary.id] || {}
  const base = {
    id: summary.id,
    title: summary.title,
    shortTitle: meta.shortTitle || summary.short_title || summary.title,
    summary: meta.summary || '',
    insight: meta.insight || '',
  }

  if (summary.id === 'treasury-rate') {
    return normalizeTreasuryRate(base, rows)
  }

  if (summary.id === 'central-bank-rate') {
    return normalizeCentralBankRate(base, rows)
  }

  if (summary.id === 'credit-rating-yield') {
    return normalizeCreditRatingYield(base, rows)
  }

  if (summary.id === 'deposit-compare') {
    return normalizeDepositCompare(base, rows)
  }

  if (summary.id === 'yield-spread') {
    return normalizeYieldSpread(base, rows)
  }

  if (summary.id === 'yield-curve') {
    return normalizeYieldCurve(base, rows)
  }

  return null
}

function normalizeTreasuryRate(base, rows) {
  const tableRows = rows.map((row) => [
    normalizeCountry(row.country),
    formatPercent(row.three_year_yield),
    formatPercent(row.ten_year_yield),
    '3년물 / 10년물 금리',
  ])
  const korea = rows.find((row) => normalizeCountry(row.country).includes('한국')) || rows[0]

  return {
    ...base,
    value: formatPercent(korea?.ten_year_yield),
    caption: '10년물 기준',
    chartType: 'line',
    chartPoints: linePoints(rows.map((row) => row.ten_year_yield)),
    tableColumns: ['구분', '3년 금리', '10년 금리', '해석'],
    tableRows,
    stats: rows.map((row) => ({ label: `${normalizeCountry(row.country)} 10년`, value: formatPercent(row.ten_year_yield) })),
  }
}

function normalizeCentralBankRate(base, rows) {
  const tableRows = rows.map((row) => [
    normalizeCountry(row.country?.country_name || row.country),
    formatPercent(row.base_interest_rate),
    formatPercent(row.three_year_yield),
    formatPercent(row.ten_year_yield),
  ])
  const korea = rows.find((row) => normalizeCountry(row.country?.country_name || row.country).includes('한국')) || rows[0]

  return {
    ...base,
    value: formatPercent(korea?.base_interest_rate),
    caption: '기준금리',
    chartType: 'bar',
    bars: barHeights(rows.map((row) => row.base_interest_rate)),
    tableColumns: ['국가', '기준금리', '3년 금리', '10년 금리'],
    tableRows,
    stats: rows.map((row) => ({
      label: normalizeCountry(row.country?.country_name || row.country),
      value: formatPercent(row.base_interest_rate),
    })),
  }
}

function normalizeCreditRatingYield(base, rows) {
  const tableRows = rows.map((row) => [
    row.credit_rating || row.rating_group || '-',
    formatPercent(row.average_ytm),
    `${row.bond_count ?? 0}건`,
    '등급별 평균 수익률',
  ])
  const first = rows[0]

  return {
    ...base,
    value: formatPercent(first?.average_ytm),
    caption: first ? `${first.credit_rating} 기준` : '',
    chartType: 'bar',
    bars: barHeights(rows.map((row) => row.average_ytm)),
    tableColumns: ['신용등급', '평균 금리', '채권 수', '해석'],
    tableRows,
    stats: rows.map((row) => ({ label: row.credit_rating || row.rating_group || '-', value: formatPercent(row.average_ytm) })),
  }
}

function normalizeDepositCompare(base, rows) {
  const tableRows = rows.map((row) => [
    row.bank?.bank_name || '-',
    row.product_name || '-',
    formatPercent(row.base_rate),
    formatPercent(row.prime_rate),
  ])
  const best = rows.reduce((max, row) => Number(row.prime_rate) > Number(max?.prime_rate ?? -Infinity) ? row : max, rows[0])

  return {
    ...base,
    value: formatPercent(best?.prime_rate),
    caption: best?.bank?.bank_name || '우대금리 기준',
    chartType: 'bar',
    bars: barHeights(rows.map((row) => row.prime_rate)),
    tableColumns: ['은행', '상품명', '기본금리', '우대금리'],
    tableRows,
    stats: rows.map((row) => ({ label: row.bank?.bank_name || '-', value: formatPercent(row.prime_rate) })),
  }
}

function normalizeYieldSpread(base, rows) {
  const tableRows = rows.map((row) => [
    normalizeCountry(row.country),
    formatPercentPoint(row.yield_curve_spread),
    '10년물 - 3년물',
    '장단기 금리차',
  ])
  const korea = rows.find((row) => normalizeCountry(row.country).includes('한국')) || rows[0]

  return {
    ...base,
    value: formatPercentPoint(korea?.yield_curve_spread),
    caption: '10년물 - 3년물',
    chartType: 'line',
    chartPoints: linePoints(rows.map((row) => row.yield_curve_spread)),
    tableColumns: ['국가', '금리차', '기준', '해석'],
    tableRows,
    stats: rows.map((row) => ({ label: normalizeCountry(row.country), value: formatPercentPoint(row.yield_curve_spread) })),
  }
}

function normalizeYieldCurve(base, rows) {
  const korea = rows.find((row) => normalizeCountry(row.country).includes('한국')) || rows[0]
  const points = korea?.points || []
  const tableRows = points.map((point) => [
    point.maturity,
    formatPercent(point.yield),
    '-',
    '만기별 금리',
  ])

  return {
    ...base,
    value: formatPercent(points.at(-1)?.yield),
    caption: korea ? `${normalizeCountry(korea.country)} 기준` : '',
    chartType: 'curve',
    chartPoints: linePoints(points.map((point) => point.yield)),
    tableColumns: ['만기', '금리', '전일 대비', '해석'],
    tableRows,
    stats: points.map((point) => ({ label: point.maturity, value: formatPercent(point.yield) })),
  }
}

function getItems(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.items)) return data.items
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.data)) return data.data
  if (Array.isArray(data?.tabs)) return data.tabs
  if (Array.isArray(data?.indicators)) return data.indicators
  return []
}

function formatPercent(value) {
  const number = Number(value)
  return Number.isFinite(number) ? `${number.toFixed(2)}%` : '-'
}

function formatPercentPoint(value) {
  const number = Number(value)
  return Number.isFinite(number) ? `${number.toFixed(2)}%p` : '-'
}

function normalizeCountry(value) {
  if (!value) return '-'
  return String(value)
}

function barHeights(values) {
  const numbers = values.map(Number).filter(Number.isFinite)
  const max = Math.max(...numbers, 1)
  return values.map((value) => {
    const number = Number(value)
    return Number.isFinite(number) ? Math.max(12, Math.round((number / max) * 92)) : 12
  })
}

function linePoints(values) {
  const numbers = values.map(Number).filter(Number.isFinite)

  if (!numbers.length) {
    return ''
  }

  const min = Math.min(...numbers)
  const max = Math.max(...numbers)
  const range = max - min || 1
  const width = 680
  const left = 20
  const top = 58
  const height = 130
  const step = numbers.length > 1 ? width / (numbers.length - 1) : 0

  return numbers
    .map((value, index) => {
      const x = left + step * index
      const y = top + height - ((value - min) / range) * height
      return `${Math.round(x)},${Math.round(y)}`
    })
    .join(' ')
}
