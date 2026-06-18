import { bonds, selectedBond } from '../data/bonds'
import { cachedQuery } from './cache'
import { apiGet } from './client'

export function getBonds() {
  return bonds
}

export function fetchBonds() {
  return cachedQuery('bonds:list', async () => {
    try {
      const data = await apiGet('/bonds')
      const items = getItems(data)
      return items.length ? items.map(normalizeBond) : bonds
    } catch {
      return bonds
    }
  })
}

export function getSelectedBond() {
  return selectedBond
}

export function fetchBondDetail(bondId = selectedBond.bondId) {
  return cachedQuery(`bonds:detail:${bondId}`, async () => {
    try {
      const data = await apiGet(`/bonds/${bondId}`)
      return normalizeBond(data)
    } catch {
      return selectedBond
    }
  })
}

export function fetchBondCompare(ids) {
  const compareIds = Array.isArray(ids) ? ids.slice(0, 2) : []

  return cachedQuery(`bonds:compare:${compareIds.join(',')}`, async () => {
    if (compareIds.length !== 2) {
      return bonds.slice(0, 2)
    }

    try {
      const data = await apiGet('/bonds/compare', { params: { ids: compareIds } })
      const items = getItems(data)
      return items.length === 2 ? items.map(normalizeBond) : bonds.slice(0, 2)
    } catch {
      return bonds.slice(0, 2)
    }
  })
}

function getItems(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.items)) return data.items
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.bonds)) return data.bonds
  return []
}

function normalizeBond(item) {
  const base = bonds.find((bond) => String(bond.bondId) === String(item?.bond_id || item?.id))
    || bonds.find((bond) => bond.code === item?.isin_code)
    || selectedBond
  const basic = item?.basic_info || item || {}
  const issue = item?.issue_redemption || item || {}
  const interest = item?.interest_condition || item || {}
  const option = item?.option_exercise || item?.option || item || {}
  const market = item?.latest_market_data || item?.market_data || item || {}
  const issuer = basic.issuer || item?.issuer || {}
  const industry = issuer.industry || item?.industry || {}
  const paymentCycleMonths = interest.payment_cycle_months
    || item?.payment_cycle_months
    || interest.interest_payment_unit_months
    || item?.interest_payment_unit_months

  return {
    ...base,
    bondId: normalizeId(basic.bond_id || item?.bond_id || item?.id || base.bondId),
    name: basic.bond_name || item?.bond_name || base.name,
    shortName: basic.short_name || item?.short_name || base.shortName,
    code: basic.isin_code || item?.isin_code || base.code,
    shortCode: basic.short_code || item?.short_code || base.shortCode,
    issuer: issuer.issuer_name || basic.issuer_name || item?.issuer_name || base.issuer,
    industry: industry.industry_name || basic.industry_name || item?.industry_name || base.industry,
    type: valueOrName(basic.bond_type || item?.bond_type, base.type),
    price: formatNumber(market.price, base.price),
    priceValue: toNumber(market.price, base.priceValue),
    substitutePrice: formatNumber(market.substitute_price, base.substitutePrice),
    change: formatPercent(market.price_change_rate, base.change, true),
    priceChangeRate: toNumber(market.price_change_rate, base.priceChangeRate),
    volume: formatCompactAmount(market.trading_volume, base.volume),
    tradingVolume: toNumber(market.trading_volume, base.tradingVolume),
    buyYield: formatPercent(market.bid_yield, base.buyYield),
    yieldValue: toNumber(market.bid_yield, base.yieldValue),
    sellYield: formatPercent(market.ask_yield, base.sellYield),
    ytm: formatPercent(market.ytm, base.ytm),
    duration: formatYears(market.duration, base.duration),
    durationValue: toNumber(market.duration, base.durationValue),
    rating: valueOrName(item?.credit_rating || basic.credit_rating, base.rating),
    ratingGroup: valueOrName(item?.rating_group || basic.rating_group, base.ratingGroup),
    issueDate: issue.issue_date || item?.issue_date || base.issueDate,
    listingDate: issue.listing_date || item?.listing_date || base.listingDate,
    maturity: formatDate(issue.maturity_date || item?.maturity_date, base.maturity),
    maturityDate: issue.maturity_date || item?.maturity_date || base.maturityDate,
    maturityYears: toMaturityYears(issue.maturity_date || item?.maturity_date, base.maturityYears),
    coupon: formatPercent(interest.coupon_rate || item?.coupon_rate, base.coupon),
    couponRate: toNumber(interest.coupon_rate || item?.coupon_rate, base.couponRate),
    interestType: valueOrName(interest.interest_type || item?.interest_type, base.interestType),
    interestPaymentMethod: interest.interest_payment_method || item?.interest_payment_method || base.interestPaymentMethod,
    interestCycle: formatMonthCycle(paymentCycleMonths, base.interestCycle),
    paymentCycleMonths: toNumber(paymentCycleMonths, base.paymentCycleMonths),
    interestPaymentUnitMonths: toNumber(
      interest.interest_payment_unit_months || item?.interest_payment_unit_months,
      base.interestPaymentUnitMonths,
    ),
    interestCalculationMonths: toNumber(
      interest.interest_calculation_months || item?.interest_calculation_months,
      base.interestCalculationMonths,
    ),
    interestPrePostType: interest.interest_pre_post_type || item?.interest_pre_post_type || base.interestPrePostType,
    firstInterestPaymentDate: interest.first_interest_payment_date || item?.first_interest_payment_date || base.firstInterestPaymentDate,
    interestPaymentBasis: interest.interest_payment_basis || item?.interest_payment_basis || base.interestPaymentBasis,
    interestMonthEndType: interest.interest_month_end_type || item?.interest_month_end_type || base.interestMonthEndType,
    option: valueOrName(option.option_type || item?.option_type, base.option),
    optionType: valueOrName(option.option_type || item?.option_type, base.optionType),
    optionExercise: normalizeOptionExercise(option, base.optionExercise),
    seniority: valueOrName(item?.seniority || basic.seniority, base.seniority),
    guaranteeStatus: valueOrName(item?.guarantee_status || basic.guarantee_status, base.guaranteeStatus),
    underwriter: issue.underwriter || item?.underwriter || base.underwriter,
    issueAmount: formatNumber(issue.issue_amount || item?.issue_amount, base.issueAmount),
    redemptionMethod: issue.redemption_method || item?.redemption_method || base.redemptionMethod,
    maturityRedemptionRate: formatPercent(issue.maturity_redemption_rate || item?.maturity_redemption_rate, base.maturityRedemptionRate),
    earlyRedemptionDescription:
      issue.early_redemption_description || item?.early_redemption_description || base.earlyRedemptionDescription,
    marketType: market.market_type || item?.market_type || base.marketType,
  }
}

function normalizeId(id) {
  return typeof id === 'number' ? id : String(id)
}

function valueOrName(value, fallback) {
  if (value && typeof value === 'object') {
    return value.name || value.label || value.code || fallback
  }

  return value || fallback
}

function toNumber(value, fallback = 0) {
  if (value === null || value === undefined || value === '') return fallback
  const number = Number(String(value).replace(/[^0-9.-]/g, ''))
  return Number.isFinite(number) ? number : fallback
}

function formatNumber(value, fallback = '-') {
  if (value === null || value === undefined || value === '') return fallback
  const number = Number(value)
  return Number.isFinite(number) ? number.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(value)
}

function formatPercent(value, fallback = '-', showSign = false) {
  if (value === null || value === undefined || value === '') return fallback
  const number = Number(value)

  if (!Number.isFinite(number)) {
    return String(value)
  }

  const sign = showSign && number > 0 ? '+' : ''
  return `${sign}${number.toFixed(2)}%`
}

function formatCompactAmount(value, fallback = '-') {
  const number = Number(value)

  if (!Number.isFinite(number)) {
    return fallback
  }

  if (number >= 100000000) {
    return `${(number / 100000000).toFixed(1)}억`
  }

  return number.toLocaleString()
}

function formatYears(value, fallback = '-') {
  if (value === null || value === undefined || value === '') return fallback
  return `${Number(value).toFixed(2)}년`
}

function formatMonthCycle(value, fallback = '-') {
  if (!value) return fallback
  return `${value}개월`
}

function formatDate(value, fallback = '-') {
  if (!value) return fallback
  return String(value).replaceAll('-', '.')
}

function toMaturityYears(value, fallback) {
  if (!value) return fallback
  const days = (new Date(value).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  return Math.max(0, Math.ceil(days / 365))
}

function normalizeOptionExercise(option, fallback) {
  if (!option || Object.keys(option).length === 0) {
    return fallback
  }

  return {
    startDate1: option.exercise_start_date_1 || option.start_date_1 || option.next_exercise_date || option.startDate1 || '',
    endDate1: option.exercise_end_date_1 || option.end_date_1 || option.endDate1 || '',
    startDate2: option.exercise_start_date_2 || option.start_date_2 || option.startDate2 || '',
    endDate2: option.exercise_end_date_2 || option.end_date_2 || option.endDate2 || '',
    reason: option.exercise_reason || option.call_reason || option.reason || '',
  }
}
