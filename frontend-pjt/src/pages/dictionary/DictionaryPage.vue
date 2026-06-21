<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchGlossaryCategories, fetchGlossaryTerms } from '../../api/glossary'

const keyword = ref('')
const allCategoryLabel = '전체'
const selectedCategory = ref(allCategoryLabel)
const remoteTerms = ref([])
const remoteCategories = ref([])

const activeTerms = computed(() => remoteTerms.value)

const categories = computed(() => {
  const categoryNames = remoteCategories.value.length
    ? remoteCategories.value
    : [...new Set(activeTerms.value.map((term) => term.category).filter(Boolean))]

  return [allCategoryLabel, ...categoryNames]
})

const filteredTerms = computed(() => {
  const normalizedKeyword = normalizeSearchText(keyword.value)

  return activeTerms.value
    .map((term, index) => ({
      term,
      index,
      searchRank: getSearchRank(term, normalizedKeyword),
    }))
    .filter(({ term, searchRank }) => {
      const matchesKeyword = !normalizedKeyword || searchRank > 0
      const matchesCategory = selectedCategory.value === allCategoryLabel || term.category === selectedCategory.value

      return matchesKeyword && matchesCategory
    })
    .sort((a, b) => {
      if (!normalizedKeyword) return a.index - b.index
      return a.searchRank - b.searchRank || a.index - b.index
    })
    .map(({ term }) => term)
})

function normalizeSearchText(value) {
  return String(value || '').trim().toLowerCase()
}

function includesKeyword(value, normalizedKeyword) {
  return normalizeSearchText(value).includes(normalizedKeyword)
}

function getSearchRank(term, normalizedKeyword) {
  if (!normalizedKeyword) return 1
  if (includesKeyword(term.term, normalizedKeyword)) return 1
  if (includesKeyword(term.category, normalizedKeyword)) return 2
  if (includesKeyword(term.level, normalizedKeyword)) return 3
  if (includesKeyword(term.desc, normalizedKeyword)) return 4
  if (includesKeyword(term.example, normalizedKeyword)) return 5
  return 0
}

function resetSearch() {
  keyword.value = ''
  selectedCategory.value = allCategoryLabel
}

onMounted(async () => {
  const [items, categoryItems] = await Promise.all([
    fetchGlossaryTerms(),
    fetchGlossaryCategories(),
  ])
  remoteTerms.value = items
  remoteCategories.value = categoryItems
})
</script>

<template>
  <section class="page dictionary-page">
    <div class="page-heading compact">
      <p class="eyebrow">Bond Dictionary</p>
      <h1>채권 용어 사전</h1>
      <p>채권을 검색하고 비교할 때 자주 만나는 용어를 쉽게 풀어 정리했습니다.</p>
    </div>

    <section class="dictionary-toolbar" aria-label="용어 검색과 분류">
      <div class="dictionary-search">
        <span aria-hidden="true">⌕</span>
        <input v-model="keyword" type="search" placeholder="궁금한 채권 용어를 검색하세요" />
      </div>

      <div class="category-tabs" aria-label="용어 분류">
        <button
          v-for="category in categories"
          :key="category"
          :class="{ active: selectedCategory === category }"
          type="button"
          @click="selectedCategory = category"
        >
          {{ category }}
        </button>
      </div>
    </section>

    <section class="dictionary-summary">
      <article>
        <span>전체 용어</span>
        <strong>{{ activeTerms.length }}개</strong>
      </article>
      <article>
        <span>현재 표시</span>
        <strong>{{ filteredTerms.length }}개</strong>
      </article>
      <article>
        <span>분류</span>
        <strong>{{ categories.length - 1 }}개</strong>
      </article>
    </section>

    <section class="term-grid" aria-label="채권 용어 목록">
      <article v-for="term in filteredTerms" :key="term.term" class="term-card dictionary-term-card">
        <div class="term-card-header">
          <div>
            <span class="term-category">{{ term.category }}</span>
            <h2>{{ term.term }}</h2>
          </div>
          <span class="term-level">{{ term.level }}</span>
        </div>
        <p>{{ term.desc }}</p>
        <div class="term-example">
          <span>예시</span>
          <strong>{{ term.example }}</strong>
        </div>
      </article>

      <div v-if="filteredTerms.length === 0" class="dictionary-empty">
        <p>검색 조건에 맞는 용어가 없습니다.</p>
        <button type="button" @click="resetSearch">전체 용어 보기</button>
      </div>
    </section>
  </section>
</template>

<style scoped>
.dictionary-page {
  display: grid;
  gap: 20px;
}

.dictionary-toolbar,
.dictionary-summary,
.dictionary-term-card,
.dictionary-empty {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
  box-shadow: var(--shadow);
}

.dictionary-toolbar {
  display: grid;
  gap: 16px;
  padding: 20px;
}

.dictionary-search {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  align-items: center;
  min-height: 54px;
  margin-bottom: 0;
  padding: 0 16px;
}

.dictionary-search span {
  color: var(--primary);
  font-weight: 900;
}

.category-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
}

.category-tabs button {
  flex: 0 0 auto;
  min-height: 38px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 13px;
  color: var(--text);
  background: white;
  font-size: 14px;
  font-weight: 800;
}

.category-tabs button.active {
  border-color: var(--primary);
  color: white;
  background: var(--primary);
}

.dictionary-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0;
  overflow: hidden;
}

.dictionary-summary article {
  display: grid;
  gap: 6px;
  padding: 18px 20px;
  border-right: 1px solid var(--line);
}

.dictionary-summary article:last-child {
  border-right: 0;
}

.dictionary-summary span,
.term-category,
.term-example span {
  color: var(--muted);
  font-size: 13px;
  font-weight: 800;
}

.dictionary-summary strong {
  color: var(--primary-dark);
  font-size: 24px;
}

.term-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.dictionary-term-card {
  display: grid;
  gap: 14px;
  margin-bottom: 0;
  padding: 20px;
}

.term-card-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
}

.term-card-header h2 {
  margin: 4px 0 0;
  font-size: 22px;
}

.term-level {
  flex: 0 0 auto;
  border-radius: 999px;
  padding: 5px 9px;
  color: var(--primary);
  background: #e8f3f4;
  font-size: 12px;
  font-weight: 900;
}

.dictionary-term-card p {
  margin-bottom: 0;
  line-height: 1.65;
}

.term-example {
  display: grid;
  gap: 4px;
  padding: 12px;
  border-radius: 8px;
  background: var(--surface-soft);
}

.term-example strong {
  color: var(--text);
  font-size: 14px;
}

.dictionary-empty {
  grid-column: 1 / -1;
  display: grid;
  place-items: center;
  gap: 10px;
  min-height: 220px;
  color: var(--muted);
}

.dictionary-empty p {
  margin-bottom: 0;
}

.dictionary-empty button {
  border: 1px solid var(--primary);
  border-radius: 8px;
  padding: 8px 14px;
  color: var(--primary);
  background: white;
  font-weight: 800;
}

@media (max-width: 820px) {
  .term-grid,
  .dictionary-summary {
    grid-template-columns: 1fr;
  }

  .dictionary-summary article {
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .dictionary-summary article:last-child {
    border-bottom: 0;
  }
}
</style>
