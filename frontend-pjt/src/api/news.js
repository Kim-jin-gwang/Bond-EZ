import { cachedQuery } from './cache'
import { apiGet } from './client'

export const NEWS_PAGE_SIZE = 20

export function fetchNews(params = {}) {
  const requestParams = {
    ...params,
    page: params.page || 1,
    size: params.size || NEWS_PAGE_SIZE,
  }
  const cacheKey = `news:list:${JSON.stringify(requestParams)}`

  return cachedQuery(cacheKey, async () => {
    const payload = await apiGet('/news', { params: requestParams, raw: true })
    return normalizePaginatedResponse(payload, normalizeNews)
  })
}

export function fetchNewsProviders() {
  return cachedQuery('news:providers', async () => {
    const data = await apiGet('/news/providers')
    return getItems(data).map(normalizeProvider)
  })
}

function getItems(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.data)) return data.data
  if (Array.isArray(data?.items)) return data.items
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.news)) return data.news
  return []
}

function normalizePaginatedResponse(payload, normalizer) {
  const items = getItems(payload)
  const page = payload?.page || {}

  return {
    items: items.map(normalizer),
    page: {
      number: page.number || 1,
      size: page.size || items.length,
      totalElements: page.total_elements ?? items.length,
      totalPages: page.total_pages || 1,
    },
  }
}

function normalizeProvider(item) {
  return {
    id: item.provider_id || item.id || '',
    name: item.provider_name || item.name || '',
  }
}

function normalizeNews(item) {
  const provider = item.provider || item.source || {}

  return {
    id: item.news_id || item.id,
    title: item.title || '',
    url: item.url || '#',
    providerId: provider.provider_id || item.provider_id || item.source_id || '',
    publisher: provider.provider_name || item.provider_name || item.source_name || '',
    date: normalizeDate(item.published_at || item.created_at || item.date),
    summary: item.summary || '',
  }
}

function normalizeDate(value) {
  if (!value) return ''
  return String(value).slice(0, 10)
}
