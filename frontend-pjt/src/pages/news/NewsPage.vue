<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchNews } from '../../api/news'

const keyword = ref('')
const selectedPublisher = ref('전체')
const selectedDate = ref('')
const openedSummaryId = ref(null)
const remoteNewsItems = ref([])

const publishers = computed(() => ['전체', ...new Set(remoteNewsItems.value.map((item) => item.publisher).filter(Boolean))])

const filteredNews = computed(() => {
  const normalizedKeyword = keyword.value.trim().toLowerCase()

  return remoteNewsItems.value.filter((item) => {
    const title = String(item.title || '').toLowerCase()
    const publisher = String(item.publisher || '').toLowerCase()
    const matchesKeyword = !normalizedKeyword || title.includes(normalizedKeyword) || publisher.includes(normalizedKeyword)
    const matchesPublisher = selectedPublisher.value === '전체' || item.publisher === selectedPublisher.value
    const matchesDate = !selectedDate.value || item.date === selectedDate.value

    return matchesKeyword && matchesPublisher && matchesDate
  })
})

function resetFilters() {
  keyword.value = ''
  selectedPublisher.value = '전체'
  selectedDate.value = ''
  openedSummaryId.value = null
}

function toggleSummary(id) {
  openedSummaryId.value = openedSummaryId.value === id ? null : id
}

onMounted(async () => {
  remoteNewsItems.value = await fetchNews()
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
        <input v-model="keyword" type="search" placeholder="뉴스 제목 또는 뉴스사를 검색하세요" />
      </label>
      <label>
        <span>뉴스사</span>
        <select v-model="selectedPublisher">
          <option v-for="publisher in publishers" :key="publisher" :value="publisher">
            {{ publisher }}
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
        <span>총 {{ filteredNews.length }}건</span>
        <strong>금리 관련 뉴스</strong>
      </div>

      <article v-for="item in filteredNews" :key="item.id" class="rate-news-item">
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

      <div v-if="filteredNews.length === 0" class="news-empty">
        <p>조건에 맞는 뉴스가 없습니다.</p>
        <button type="button" @click="resetFilters">필터 초기화</button>
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
