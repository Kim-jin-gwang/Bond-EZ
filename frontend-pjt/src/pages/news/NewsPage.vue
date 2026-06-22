<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { NEWS_PAGE_SIZE, fetchNews, fetchNewsProviders } from '../../api/news'
import { useDebouncedRef } from '../../composables/useDebouncedRef'

const keywordInput = ref('')
const keyword = useDebouncedRef(keywordInput)
const selectedPublisher = ref('')
const selectedDate = ref('')
const openedSummaryId = ref(null)
const remoteNewsItems = ref([])
const providers = ref([])
const isLoading = ref(false)
const error = ref(null)
const currentPage = ref(1)
const pageInfo = ref({
  number: 1,
  size: NEWS_PAGE_SIZE,
  totalElements: 0,
  totalPages: 1,
})
let requestId = 0

const pageButtons = computed(() => getPageButtons(currentPage.value, pageInfo.value.totalPages))

watch([keyword, selectedPublisher, selectedDate], () => {
  currentPage.value = 1
  loadNews()
})

watch(currentPage, loadNews)

function resetFilters() {
  keywordInput.value = ''
  selectedPublisher.value = ''
  selectedDate.value = ''
  openedSummaryId.value = null
}

function toggleSummary(id) {
  openedSummaryId.value = openedSummaryId.value === id ? null : id
}

async function loadNews() {
  const activeRequest = ++requestId
  isLoading.value = true
  error.value = null

  try {
    const result = await fetchNews(buildNewsParams())
    if (activeRequest !== requestId) return
    remoteNewsItems.value = result.items
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

function buildNewsParams() {
  return {
    page: currentPage.value,
    size: NEWS_PAGE_SIZE,
    keyword: keyword.value.trim(),
    provider_id: selectedPublisher.value,
    published_from: selectedDate.value,
    published_to: selectedDate.value,
  }
}

function goToPage(page) {
  if (page < 1 || page > pageInfo.value.totalPages || page === currentPage.value) return
  currentPage.value = page
}

function getPageButtons(page, totalPages) {
  const safeTotal = Math.max(1, totalPages || 1)
  const start = Math.max(1, Math.min(page - 2, safeTotal - 4))
  const end = Math.min(safeTotal, start + 4)
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
}

onMounted(async () => {
  const [providerItems] = await Promise.all([
    fetchNewsProviders(),
    loadNews(),
  ])
  providers.value = providerItems
})
</script>

<template>
  <section class="page news-page">
    <div class="page-heading compact">
      <p class="eyebrow">Rate News</p>
      <h1>금리 뉴스</h1>
      <p>금리와 채권시장 관련 뉴스를 모아 원문으로 연결합니다.</p>
    </div>

    <section class="news-filter-panel" aria-label="뉴스 필터">
      <label>
        <span>제목 검색</span>
        <input v-model="keywordInput" type="search" placeholder="뉴스 제목 또는 뉴스사를 검색하세요" />
      </label>
      <label>
        <span>뉴스사</span>
        <select v-model="selectedPublisher">
          <option value="">전체</option>
          <option v-for="publisher in providers" :key="publisher.id" :value="publisher.id">
            {{ publisher.name }}
          </option>
        </select>
      </label>
      <label>
        <span>날짜</span>
        <input v-model="selectedDate" type="date" />
      </label>
      <button type="button" @click="resetFilters">초기화</button>
    </section>

    <section class="news-list-panel">
      <div class="news-list-header">
        <span>총 {{ pageInfo.totalElements }}건</span>
        <strong>금리 관련 뉴스</strong>
      </div>

      <div v-if="isLoading" class="news-empty">
        <p>뉴스를 불러오는 중입니다.</p>
      </div>

      <div v-if="error" class="news-empty error-state">
        <p>뉴스를 불러오지 못했습니다.</p>
        <button type="button" @click="loadNews">다시 시도</button>
      </div>

      <article v-for="item in remoteNewsItems" :key="item.id" class="rate-news-item">
        <div class="news-row">
          <div class="news-main">
            <span class="news-title">{{ item.title }}</span>
            <span class="news-meta">
              <strong>{{ item.publisher }}</strong>
              <time :datetime="item.date">{{ item.date }}</time>
            </span>
          </div>
          <div class="news-actions">
            <button class="summary-button" type="button" @click="toggleSummary(item.id)">
              {{ openedSummaryId === item.id ? '닫기' : '요약' }}
            </button>
            <a class="open-news-button" :href="item.url" target="_blank" rel="noreferrer">뉴스 보기</a>
          </div>
        </div>
        <div v-if="openedSummaryId === item.id" class="news-summary">
          <strong>뉴스 요약</strong>
          <p>{{ item.summary }}</p>
          <a :href="item.url" target="_blank" rel="noreferrer">원문 보기</a>
        </div>
      </article>

      <div v-if="!isLoading && !error && remoteNewsItems.length === 0" class="news-empty">
        <p>조건에 맞는 뉴스가 없습니다.</p>
        <button type="button" @click="resetFilters">필터 초기화</button>
      </div>

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
  </section>
</template>

<style scoped>
.news-page {
  display: grid;
  gap: 20px;
}

.news-filter-panel,
.news-list-panel {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
  box-shadow: var(--shadow);
}

.news-filter-panel {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) 180px 180px auto;
  gap: 14px;
  align-items: end;
  padding: 20px;
}

.news-filter-panel label {
  color: var(--text);
  font-weight: 800;
}

.news-filter-panel button,
.news-empty button {
  min-height: 42px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 14px;
  color: var(--text);
  background: var(--surface);
  font-weight: 800;
}

.news-list-panel {
  padding: 18px;
}

.news-list-header,
.news-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.news-list-header {
  margin-bottom: 12px;
  padding: 0 4px;
}

.news-list-header span,
.news-meta {
  color: var(--muted);
  font-size: 14px;
}

.rate-news-item {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fbfdff;
}

.rate-news-item + .rate-news-item {
  margin-top: 10px;
}

.news-row {
  padding: 16px 18px;
}

.news-main {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.news-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.news-title {
  overflow: hidden;
  font-size: 16px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.news-meta {
  display: flex;
  gap: 12px;
}

.news-meta strong {
  color: var(--primary-dark);
}

.summary-button,
.open-news-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  border: 1px solid var(--primary);
  border-radius: 8px;
  padding: 0 14px;
  color: var(--primary);
  background: white;
  font-weight: 900;
  text-decoration: none;
  white-space: nowrap;
}

.open-news-button {
  border-color: var(--line);
  color: var(--text);
}

.news-summary {
  margin: 0 18px 16px;
  padding: 16px;
  border: 1px solid #d7e7e9;
  border-radius: 8px;
  background: #f4fafb;
}

.news-summary strong {
  display: block;
  margin-bottom: 8px;
  color: var(--primary-dark);
}

.news-summary p {
  margin-bottom: 10px;
  line-height: 1.65;
}

.news-summary a {
  color: var(--primary);
  font-size: 14px;
  font-weight: 900;
  text-decoration: none;
}

.news-empty {
  display: grid;
  place-items: center;
  gap: 10px;
  min-height: 180px;
  color: var(--muted);
}

.news-empty p {
  margin-bottom: 0;
}

.error-state {
  border-color: #f2c7c7;
  background: #fff7f7;
}

.pagination {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 18px;
}

.pagination button {
  min-width: 38px;
  min-height: 38px;
  border: 1px solid var(--primary);
  border-radius: 8px;
  padding: 0 14px;
  color: var(--primary);
  background: white;
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

@media (max-width: 900px) {
  .news-filter-panel,
  .news-row {
    grid-template-columns: 1fr;
  }

  .news-row {
    display: grid;
  }
}
</style>
