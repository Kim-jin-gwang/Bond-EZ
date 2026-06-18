<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchGlossaryTerms } from '../../api/glossary'

const keyword = ref('')
const selectedCategory = ref('전체')
const remoteTerms = ref(null)

const terms = [
  {
    term: '채권',
    category: '기본 개념',
    level: '입문',
    desc: '정부, 공공기관, 기업 등이 돈을 빌리기 위해 발행하는 증서입니다. 투자자는 채권을 사고 정해진 이자와 만기 상환금을 받을 권리를 갖습니다.',
    example: '국고채, 회사채, 금융채',
  },
  {
    term: '국채',
    category: '기본 개념',
    level: '입문',
    desc: '국가가 발행하는 채권입니다. 일반적으로 신용 위험이 낮아 다른 채권 금리를 비교할 때 기준 역할을 합니다.',
    example: '국고채 3년, 국고채 10년',
  },
  {
    term: '회사채',
    category: '기본 개념',
    level: '입문',
    desc: '기업이 자금을 조달하기 위해 발행하는 채권입니다. 발행 기업의 신용도에 따라 금리와 위험이 달라집니다.',
    example: 'AA등급 회사채, BBB등급 회사채',
  },
  {
    term: '금융채',
    category: '기본 개념',
    level: '입문',
    desc: '은행, 카드사, 캐피탈사 등 금융기관이 발행하는 채권입니다. 발행 기관과 만기에 따라 수익률 차이가 큽니다.',
    example: '은행채, 여전채',
  },
  {
    term: '표면금리',
    category: '가격·수익률',
    level: '입문',
    desc: '채권 액면가에 대해 발행자가 약속한 연 이자율입니다. 실제 투자 수익률은 매수 가격에 따라 달라질 수 있습니다.',
    example: '액면 10,000원, 표면금리 3%면 연 300원 이자',
  },
  {
    term: 'YTM',
    category: '가격·수익률',
    level: '중요',
    desc: 'Yield To Maturity의 약자로, 현재 가격에 매수해 만기까지 보유한다고 가정했을 때 기대되는 연 환산 수익률입니다.',
    example: '매수수익률 3.82%',
  },
  {
    term: '매수수익률',
    category: '가격·수익률',
    level: '중요',
    desc: '투자자가 해당 가격으로 채권을 살 때 기대할 수 있는 수익률입니다. 가격이 내려가면 보통 매수수익률은 올라갑니다.',
    example: '가격 10,185원 / 매수수익률 3.82%',
  },
  {
    term: '매도수익률',
    category: '가격·수익률',
    level: '기초',
    desc: '투자자가 보유 채권을 팔 때 시장에서 제시되는 수익률입니다. 매수수익률과 매도수익률 차이는 거래 비용처럼 작용할 수 있습니다.',
    example: '매수 3.82% / 매도 3.71%',
  },
  {
    term: '액면가',
    category: '가격·수익률',
    level: '입문',
    desc: '만기에 상환받는 기준 금액입니다. 채권 가격은 액면가보다 높거나 낮게 거래될 수 있습니다.',
    example: '액면가 10,000원',
  },
  {
    term: '프리미엄 채권',
    category: '가격·수익률',
    level: '심화',
    desc: '시장 가격이 액면가보다 높은 채권입니다. 표면금리가 시장금리보다 높을 때 이런 형태가 자주 나타납니다.',
    example: '10,000원 액면 채권이 10,185원에 거래',
  },
  {
    term: '할인채',
    category: '가격·수익률',
    level: '심화',
    desc: '액면가보다 낮은 가격에 거래되거나 이자 없이 할인 발행되는 채권입니다. 만기 상환 차익이 수익의 핵심이 됩니다.',
    example: '9,800원에 매수해 만기 10,000원 상환',
  },
  {
    term: '만기',
    category: '발행·상환',
    level: '입문',
    desc: '발행자가 원금을 상환하기로 약속한 날짜입니다. 만기가 길수록 금리 변화에 따른 가격 변동이 커질 수 있습니다.',
    example: '2030.06.10 만기',
  },
  {
    term: '잔존만기',
    category: '발행·상환',
    level: '기초',
    desc: '현재 시점부터 채권 만기일까지 남은 기간입니다. 투자 기간과 유동성 계획을 세울 때 중요합니다.',
    example: '잔존만기 5년',
  },
  {
    term: '이자 지급 주기',
    category: '발행·상환',
    level: '기초',
    desc: '채권 이자가 지급되는 간격입니다. 3개월, 6개월, 12개월, 만기일시 지급 등으로 나뉩니다.',
    example: '3개월마다 이자 지급',
  },
  {
    term: '콜옵션',
    category: '발행·상환',
    level: '중요',
    desc: '발행자가 정해진 조건에 따라 만기 전에 채권을 조기상환할 수 있는 권리입니다. 투자자는 예상보다 빨리 원금을 돌려받을 수 있습니다.',
    example: 'CALL 조건부 금융채',
  },
  {
    term: '조기상환',
    category: '발행·상환',
    level: '중요',
    desc: '만기 전에 원금이 상환되는 일입니다. 금리가 하락하면 발행자가 높은 이자의 기존 채권을 조기상환할 유인이 커집니다.',
    example: '콜옵션 행사로 만기 전 상환',
  },
  {
    term: '신용등급',
    category: '리스크',
    level: '중요',
    desc: '발행자가 원리금을 갚을 능력을 평가한 등급입니다. 등급이 낮을수록 일반적으로 수익률은 높지만 부도 위험도 커집니다.',
    example: 'AAA, AA, A, BBB',
  },
  {
    term: '신용 스프레드',
    category: '리스크',
    level: '심화',
    desc: '회사채 등 위험자산 금리와 국채 같은 기준 금리의 차이입니다. 시장이 요구하는 위험 보상 수준을 보여줍니다.',
    example: 'AA 회사채 금리 4.12% - 국고채 3.42%',
  },
  {
    term: '듀레이션',
    category: '리스크',
    level: '중요',
    desc: '금리 변화에 채권 가격이 얼마나 민감하게 움직이는지 보여주는 지표입니다. 듀레이션이 길수록 금리 변동 위험이 큽니다.',
    example: '듀레이션 6.4년',
  },
  {
    term: '유동성 위험',
    category: '리스크',
    level: '중요',
    desc: '원하는 시점에 원하는 가격으로 채권을 팔기 어려운 위험입니다. 거래량이 적은 채권일수록 유동성 위험이 커질 수 있습니다.',
    example: '거래량 부족으로 매도 호가가 넓어짐',
  },
  {
    term: '금리 위험',
    category: '리스크',
    level: '중요',
    desc: '시장금리가 변하면서 채권 가격이 변동하는 위험입니다. 일반적으로 금리가 오르면 기존 채권 가격은 하락합니다.',
    example: '금리 상승 → 채권 가격 하락',
  },
  {
    term: '장단기 금리차',
    category: '시장 지표',
    level: '심화',
    desc: '짧은 만기 금리와 긴 만기 금리의 차이입니다. 경기 전망과 기준금리 인하 기대를 해석할 때 자주 쓰입니다.',
    example: '국고채 3년-10년 금리차',
  },
  {
    term: 'Yield Curve',
    category: '시장 지표',
    level: '심화',
    desc: '만기별 금리를 연결한 곡선입니다. 우상향, 평탄화, 역전 여부를 통해 시장의 금리 경로와 경기 기대를 볼 수 있습니다.',
    example: '3개월, 1년, 3년, 10년 금리 곡선',
  },
  {
    term: '기준금리',
    category: '시장 지표',
    level: '기초',
    desc: '중앙은행이 통화정책의 기준으로 삼는 금리입니다. 채권 금리와 예금 금리, 대출 금리에 큰 영향을 줍니다.',
    example: '한국은행 기준금리',
  },
  {
    term: '호가',
    category: '거래',
    level: '기초',
    desc: '시장에서 사고팔기 위해 제시된 가격입니다. 매수호가와 매도호가의 차이가 크면 거래 비용이 커질 수 있습니다.',
    example: '매수호가 10,180원 / 매도호가 10,190원',
  },
  {
    term: '장내채권',
    category: '거래',
    level: '기초',
    desc: '거래소 시장에서 표준화된 방식으로 거래되는 채권입니다. 가격과 거래 정보를 비교적 확인하기 쉽습니다.',
    example: 'KRX 장내 채권',
  },
  {
    term: '장외채권',
    category: '거래',
    level: '기초',
    desc: '증권사 등을 통해 개별적으로 거래되는 채권입니다. 같은 채권도 증권사별 제시 가격이 다를 수 있습니다.',
    example: '증권사 장외 채권 상품',
  },
  {
    term: '세후 수익률',
    category: '세금·수익',
    level: '중요',
    desc: '세금과 비용을 반영한 실제 수익률입니다. 채권 투자는 표면금리보다 세후 수익률을 함께 보는 것이 중요합니다.',
    example: '세전 3.82% / 세후 3.23%',
  },
  {
    term: '이자소득세',
    category: '세금·수익',
    level: '기초',
    desc: '채권 이자에 부과되는 세금입니다. 일반적으로 세후 수익을 계산할 때 이자소득세와 지방소득세를 함께 고려합니다.',
    example: '이자소득세 및 지방소득세',
  },
]

const activeTerms = computed(() => remoteTerms.value?.length ? remoteTerms.value : terms)

const categories = computed(() => ['전체', ...new Set(activeTerms.value.map((term) => term.category))])

const filteredTerms = computed(() => {
  const normalizedKeyword = keyword.value.trim().toLowerCase()

  return activeTerms.value.filter((term) => {
    const matchesKeyword =
      !normalizedKeyword ||
      term.term.toLowerCase().includes(normalizedKeyword) ||
      term.desc.toLowerCase().includes(normalizedKeyword) ||
      term.example.toLowerCase().includes(normalizedKeyword)
    const matchesCategory = selectedCategory.value === '전체' || term.category === selectedCategory.value

    return matchesKeyword && matchesCategory
  })
})

onMounted(async () => {
  try {
    const items = await fetchGlossaryTerms()
    remoteTerms.value = items.length ? items : null
  } catch {
    remoteTerms.value = null
  }
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
        <button type="button" @click="keyword = ''; selectedCategory = '전체'">전체 용어 보기</button>
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
