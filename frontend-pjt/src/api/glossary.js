import { cachedQuery } from './cache'
import { apiGet } from './client'

export const GLOSSARY_PAGE_SIZE = 20

export function fetchGlossaryTerms(params = {}) {
  const requestParams = {
    ...params,
    page: params.page || 1,
    size: params.size || GLOSSARY_PAGE_SIZE,
  }
  const cacheKey = `glossary:list:${JSON.stringify(requestParams)}`

  return cachedQuery(cacheKey, async () => {
    const payload = await apiGet('/glossary', { params: requestParams, raw: true })
    return normalizePaginatedResponse(payload, normalizeTerm)
  })
}

export function fetchGlossaryCategories() {
  return cachedQuery('glossary:categories', async () => {
    const data = await apiGet('/glossary/categories')
    return getItems(data).map(normalizeCategory).filter((item) => item.name)
  })
}

function getItems(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.data)) return data.data
  if (Array.isArray(data?.items)) return data.items
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.terms)) return data.terms
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

function normalizeCategory(item) {
  return {
    id: item.category_id || item.id || '',
    name: item.category_name || item.category || '',
  }
}

function normalizeTerm(item) {
  const category = item.category || {}

  return {
    id: item.term_id || item.id || item.term_name || item.term || '',
    term: item.term_name || item.term || '',
    categoryId: category.category_id || item.category_id || '',
    category: category.category_name || item.category_name || '',
    level: item.difficulty || item.level || '',
    desc: item.description || item.desc || '',
    example: item.example_text || item.example || '',
  }
}
