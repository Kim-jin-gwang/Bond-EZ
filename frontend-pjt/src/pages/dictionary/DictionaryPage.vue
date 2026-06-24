<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { GLOSSARY_PAGE_SIZE, fetchGlossaryCategories, fetchGlossaryTerms } from '../../api/glossary'
import { useDebouncedRef } from '../../composables/useDebouncedRef'

const keywordInput = ref('')
const keyword = useDebouncedRef(keywordInput)
const allCategoryLabel = '전체'
const selectedCategory = ref('')
const remoteTerms = ref([])
const remoteCategories = ref([])
const isLoading = ref(false)
const error = ref(null)
const currentPage = ref(1)
const pageInfo = ref({
  number: 1,
  size: GLOSSARY_PAGE_SIZE,
  totalElements: 0,
  totalPages: 1,
})
let requestId = 0

const activeTerms = computed(() => remoteTerms.value)

const categories = computed(() => {
  return [
    { id: '', name: allCategoryLabel },
    ...remoteCategories.value,
  ]
})

const pageButtons = computed(() => getPageButtons(currentPage.value, pageInfo.value.totalPages))

watch([keyword, selectedCategory], () => {
  currentPage.value = 1
  loadTerms()
})

watch(currentPage, loadTerms)

function resetSearch() {
  keywordInput.value = ''
  selectedCategory.value = ''
}

async function loadTerms() {
  const activeRequest = ++requestId
  isLoading.value = true
  error.value = null

  try {
    const result = await fetchGlossaryTerms(buildGlossaryParams())
    if (activeRequest !== requestId) return
    remoteTerms.value = result.items
    pageInfo.value = result.page
    currentPage.value = result.page.number
  } catch (err) {
    if (activeRequest !== requestId) return
    error.value = err
  } finally {
    if (activeRequest === requestId) {
      isLoading.value = false
    }
  }
}

function buildGlossaryParams() {
  return {
    page: currentPage.value,
    size: GLOSSARY_PAGE_SIZE,
    keyword: keyword.value.trim(),
    category_id: selectedCategory.value,
  }
}

function goToPage(page) {
  if (page < 1 || page > pageInfo.value.totalPages || page === currentPage.value) return
  currentPage.value = page
}

function getPageButtons(page, totalPages) {
  const safeTotal = Math.max(1, totalPages || 1)
  const pageGroupSize = 5
  const start = Math.floor((page - 1) / pageGroupSize) * pageGroupSize + 1
  const end = Math.min(safeTotal, start + pageGroupSize - 1)
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
}

onMounted(async () => {
  const [categoryItems] = await Promise.all([
    fetchGlossaryCategories(),
    loadTerms(),
  ])
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
        <input v-model="keywordInput" type="search" placeholder="궁금한 채권 용어를 검색하세요" />
      </div>

      <div class="category-tabs" aria-label="용어 분류">
        <button
          v-for="category in categories"
          :key="category.id || category.name"
          :class="{ active: selectedCategory === category.id }"
          type="button"
          @click="selectedCategory = category.id"
        >
          {{ category.name }}
        </button>
      </div>
    </section>

    <section class="dictionary-summary">
      <article>
        <span>전체 용어</span>
        <strong>{{ pageInfo.totalElements }}개</strong>
      </article>
      <article>
        <span>현재 표시</span>
        <strong>{{ activeTerms.length }}개</strong>
      </article>
      <article>
        <span>분류</span>
        <strong>{{ categories.length - 1 }}개</strong>
      </article>
    </section>

    <section class="term-grid" aria-label="채권 용어 목록">
      <div v-if="isLoading" class="dictionary-empty">
        <p>용어를 불러오는 중입니다.</p>
      </div>

      <div v-if="error" class="dictionary-empty error-state">
        <p>용어를 불러오지 못했습니다.</p>
        <button type="button" @click="loadTerms">다시 시도</button>
      </div>

      <article v-for="term in activeTerms" :key="term.id || term.term" class="term-card dictionary-term-card">
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

      <div v-if="!isLoading && !error && activeTerms.length === 0" class="dictionary-empty">
        <p>검색 조건에 맞는 용어가 없습니다.</p>
        <button type="button" @click="resetSearch">전체 용어 보기</button>
      </div>
    </section>

    <div v-if="pageInfo.totalPages > 1" class="pagination">
      <button type="button" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">이전</button>
      <button
        v-for="page in pageButtons"
        :key="page"
        type="button"
        :class="{ active: currentPage === page }"
        @click="goToPage(page)"
      >
        {{ page }}
      </button>
      <button type="button" :disabled="currentPage >= pageInfo.totalPages" @click="goToPage(currentPage + 1)">다음</button>
    </div>
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
  background: var(--surface);
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
  background: var(--surface);
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
  background: var(--surface);
  font-weight: 800;
}

.error-state {
  border-color: #f2c7c7;
  background: color-mix(in srgb, var(--danger) 10%, var(--surface));
}

.pagination {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 4px;
}

.pagination button {
  min-width: 38px;
  min-height: 38px;
  border: 1px solid var(--primary);
  border-radius: 8px;
  padding: 0 14px;
  color: var(--primary);
  background: var(--surface);
  font-weight: 800;
}

.pagination button.active {
  color: white;
  background: var(--primary);
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
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
