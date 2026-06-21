export function parseRate(value) {
  const number = Number(String(value ?? '').replace(/[^0-9.-]/g, ''))
  return Number.isFinite(number) ? number : null
}

export function formatRate(value) {
  return Number.isFinite(value) ? `${value.toFixed(2)}%` : '-'
}

export function formatRateGap(value) {
  if (!Number.isFinite(value)) return '-'
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%p`
}

export function getCountryTone(country = '') {
  if (country.includes('미국')) return 'us'
  if (country.includes('일본')) return 'jp'
  if (country.includes('한국') || country.includes('대한민국')) return 'kr'
  return 'default'
}

export function getSpreadState(spread) {
  if (!Number.isFinite(spread)) return '데이터 없음'
  if (spread < 0) return '역전 구간'
  if (spread <= 0.15) return '평탄 구간'
  return '정상 구간'
}

export function barHeight(rate) {
  return Number.isFinite(rate) ? `${Math.max(4, (rate / 10) * 100)}%` : '4%'
}

export function spreadBarStyle(spread) {
  if (!Number.isFinite(spread)) return {}

  const width = Math.min(50, (Math.abs(spread) / 1.5) * 50)
  return spread >= 0
    ? { left: '50%', width: `${width}%` }
    : { right: '50%', width: `${width}%` }
}
