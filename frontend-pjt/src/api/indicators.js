import { indicators } from '../data/indicators'
import { cachedQuery } from './cache'
import { apiGet } from './client'

export function getIndicators() {
  return indicators
}

export function fetchIndicators() {
  return cachedQuery('indicators:list', async () => {
    try {
      const data = await apiGet('/indicators')
      const items = getItems(data)
      return items.length ? mergeIndicators(items) : indicators
    } catch {
      return indicators
    }
  })
}

function getItems(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.items)) return data.items
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.indicators)) return data.indicators
  return []
}

function mergeIndicators(items) {
  return indicators.map((indicator) => {
    const apiIndicator = items.find((item) => item.id === indicator.id || item.indicator_id === indicator.id)

    if (!apiIndicator) {
      return indicator
    }

    return {
      ...indicator,
      title: apiIndicator.title || indicator.title,
      shortTitle: apiIndicator.short_title || apiIndicator.shortTitle || indicator.shortTitle,
      value: apiIndicator.value || indicator.value,
      caption: apiIndicator.caption || indicator.caption,
      summary: apiIndicator.summary || indicator.summary,
      insight: apiIndicator.insight || indicator.insight,
      tableRows: apiIndicator.table_rows || indicator.tableRows,
      stats: apiIndicator.stats || indicator.stats,
    }
  })
}
