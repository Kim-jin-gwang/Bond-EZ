<script setup>
import { computed, ref } from 'vue'

const keyword = ref('')
const selectedPublisher = ref('전체')
const selectedDate = ref('')
const openedSummaryId = ref(null)

const newsItems = [
  {
    id: 'rate-001',
    title: '국고채 금리, 장기물 중심으로 상승 마감',
    url: 'https://www.yna.co.kr/',
    publisher: '연합뉴스',
    date: '2026-06-05',
    summary:
      '장기물 금리가 상승하면서 채권 가격 부담이 커졌습니다. 장기 채권을 매수하려는 투자자는 금리 추가 상승 가능성과 듀레이션 위험을 함께 확인할 필요가 있습니다.',
  },
  {
    id: 'rate-002',
    title: '미국채 10년물 금리 하락, 기준금리 인하 기대 재부각',
    url: 'https://www.reuters.com/',
    publisher: 'Reuters',
    date: '2026-06-04',
    summary:
      '미국 장기금리가 하락하며 시장의 금리 인하 기대가 다시 커졌습니다. 국내 채권시장에도 장기물 수요와 환율 변동을 통해 간접 영향을 줄 수 있습니다.',
  },
  {
    id: 'rate-003',
    title: '한국은행 기준금리 동결 이후 채권시장 변동성 확대',
    url: 'https://www.bok.or.kr/',
    publisher: '한국은행',
    date: '2026-06-03',
    summary:
      '기준금리 동결 이후 시장은 향후 인하 시점과 물가 흐름을 다시 반영하고 있습니다. 단기채와 장기채의 반응이 다를 수 있어 만기별 금리 변화를 보는 것이 중요합니다.',
  },
  {
    id: 'rate-004',
    title: '회사채 시장, 우량 등급 중심으로 수요 회복',
    url: 'https://www.mk.co.kr/',
    publisher: '매일경제',
    date: '2026-06-02',
    summary:
      '우량 회사채 수요가 회복되며 신용등급이 높은 발행사의 조달 여건이 개선되는 흐름입니다. 다만 등급이 낮은 회사채는 신용 스프레드를 별도로 점검해야 합니다.',
  },
  {
    id: 'rate-005',
    title: '예금 금리와 채권 수익률 격차 확대',
    url: 'https://www.hankyung.com/',
    publisher: '한국경제',
    date: '2026-06-01',
    summary:
      '예금 대비 채권 수익률 매력이 커지고 있지만 채권은 가격 변동과 중도 매도 위험이 있습니다. 세후 수익률과 투자 기간을 함께 비교하는 접근이 필요합니다.',
  },
]

const publishers = computed(() => ['전체', ...new Set(newsItems.map((item) => item.publisher))])

const filteredNews = computed(() => {
  const normalizedKeyword = keyword.value.trim().toLowerCase()

  return newsItems.filter((item) => {
    const matchesKeyword =
      !normalizedKeyword ||
      item.title.toLowerCase().includes(normalizedKeyword) ||
      item.publisher.toLowerCase().includes(normalizedKeyword)
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

.news-filter-panel button {
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

.news-list-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 12px;
  padding: 0 4px;
}

.news-list-header span {
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
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: center;
  padding: 16px 18px;
}

.news-main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  gap: 18px;
  align-items: center;
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
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  align-items: center;
  color: var(--muted);
  font-size: 14px;
  text-align: right;
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

.summary-button:hover,
.open-news-button:hover {
  color: white;
  background: var(--primary);
}

.open-news-button {
  border-color: var(--line);
  color: var(--text);
}

.open-news-button:hover {
  border-color: var(--primary);
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

.news-empty button {
  border: 1px solid var(--primary);
  border-radius: 8px;
  padding: 8px 14px;
  color: var(--primary);
  background: white;
  font-weight: 800;
}

@media (max-width: 900px) {
  .news-filter-panel,
  .news-row,
  .news-main {
    grid-template-columns: 1fr;
  }

  .news-actions {
    justify-content: flex-start;
  }

  .news-meta {
    text-align: left;
  }
}
</style>
