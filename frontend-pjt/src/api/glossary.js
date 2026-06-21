import { cachedQuery } from './cache'
import { apiGet } from './client'

const PAGE_SIZE = 100

export function fetchGlossaryTerms() {
  return cachedQuery('glossary:list:all', async () => {
    const glossaryItems = []
    let page = 1

    while (true) {
      const data = await apiGet('/glossary', { params: { page, size: PAGE_SIZE } })
      const items = getItems(data)
      glossaryItems.push(...items.map(normalizeTerm))

      if (items.length < PAGE_SIZE) {
        break
      }

      page += 1
    }

    return glossaryItems
  })
}

export function fetchGlossaryCategories() {
  return cachedQuery('glossary:categories', async () => {
    const data = await apiGet('/glossary/categories')
    return getItems(data).map((item) => item.category_name || item.category || '').filter(Boolean)
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
