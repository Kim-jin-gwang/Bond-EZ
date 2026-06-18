import { cachedQuery } from './cache'
import { apiGet } from './client'

export function fetchGlossaryTerms() {
  return cachedQuery('glossary:list', async () => {
    const data = await apiGet('/glossary')
    return getItems(data).map(normalizeTerm)
  })
}

function getItems(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.items)) return data.items
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.terms)) return data.terms
  return []
}

function normalizeTerm(item) {
  const category = item.category || {}

  return {
    term: item.term_name || item.term || '',
    category: category.category_name || item.category_name || '',
    level: item.difficulty || item.level || '',
    desc: item.description || item.desc || '',
    example: item.example_text || item.example || '',
  }
}
