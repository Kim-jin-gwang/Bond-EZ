import { cachedQuery } from './cache'
import { apiGet } from './client'

export function fetchNews() {
  return cachedQuery('news:list', async () => {
    const data = await apiGet('/news')
    return getItems(data).map(normalizeNews)
  })
}

function getItems(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.items)) return data.items
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.news)) return data.news
  return []
}

function normalizeNews(item) {
  const provider = item.provider || item.source || {}

  return {
    id: item.news_id || item.id,
    title: item.title || '',
    url: item.url || '#',
    publisher: provider.provider_name || item.provider_name || item.source_name || '',
    date: normalizeDate(item.published_at || item.created_at || item.date),
    summary: item.summary || '',
  }
}

function normalizeDate(value) {
  if (!value) return ''
  return String(value).slice(0, 10)
}
