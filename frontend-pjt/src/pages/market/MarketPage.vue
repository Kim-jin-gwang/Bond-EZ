<script setup>
import { computed, ref, watch } from 'vue'
import { bonds } from '../../data/bonds'

const emit = defineEmits(['navigate'])

const props = defineProps({
  marketSearch: {
    type: Object,
    default: null,
  },
})

// 필터 상태 관리
const filtersOpen = ref(false)
const searchKeyword = ref(props.marketSearch?.keyword || '')
const selectedFilters = ref({
  bondTypes: props.marketSearch?.filters?.bondTypes || [],
  maturities: props.marketSearch?.filters?.maturities || [],
  yields: props.marketSearch?.filters?.yields || [],
  ratings: props.marketSearch?.filters?.ratings || [],
  interestCycles: props.marketSearch?.filters?.interestCycles || [],
})

const filterGroups = [
  {
    key: 'bondTypes',
    label: '채권 종류',
    options: ['국채', '회사채', '금융채'],
  },
  {
    key: 'maturities',
    label: '만기',
    options: ['1년 이하', '1~3년', '3~5년', '5~10년', '10년 이상'],
  },
  {
    key: 'yields',
    label: '수익률',
    options: ['3% 이상', '4% 이상', '5% 이상', '6% 이상'],
  },
  {
    key: 'ratings',
    label: '신용등급',
    options: ['AAA', 'AA', 'A', 'BBB'],
  },
  {
    key: 'interestCycles',
    label: '이자 지급 주기',
    options: ['3개월', '6개월', '12개월', '만기일시'],
  },
]

const compareActive = ref(false)

// Props 변경 시 로컬 상태 동기화
watch(() => props.marketSearch, (newVal) => {
  if (newVal) {
    searchKeyword.value = newVal.keyword || ''
    if (newVal.filters) {
      selectedFilters.value = {
        bondTypes: newVal.filters.bondTypes || [],
        maturities: newVal.filters.maturities || [],
        yields: newVal.filters.yields || [],
        ratings: newVal.filters.ratings || [],
        interestCycles: newVal.filters.interestCycles || [],
      }
    }
  }
}, { deep: true })

function hasSelected(values) {
  return Array.isArray(values) && values.length > 0
}

function matchesMaturity(bond, maturities) {
  if (!hasSelected(maturities)) return true
  return maturities.some((range) => {
    if (range === '1년 이하') return bond.maturityYears <= 1
    if (range === '1~3년') return bond.maturityYears > 1 && bond.maturityYears <= 3
    if (range === '3~5년') return bond.maturityYears > 3 && bond.maturityYears <= 5
    if (range === '5~10년') return bond.maturityYears > 5 && bond.maturityYears <= 10
    if (range === '10년 이상') return bond.maturityYears >= 10
    return true
  })
}

function matchesYield(bond, yields) {
  if (!hasSelected(yields)) return true
  return yields.some((yieldText) => {
    const threshold = Number(yieldText.replace(/[^0-9.]/g, ''))
    return bond.yieldValue >= threshold
  })
}

const filteredBonds = computed(() => {
  const keyword = searchKeyword.value.toLowerCase()
  const filters = selectedFilters.value

  return bonds.filter((bond) => {
    const matchesKeyword =
      !keyword ||
      bond.name.toLowerCase().includes(keyword) ||
      bond.code.toLowerCase().includes(keyword) ||
      bond.type.toLowerCase().includes(keyword) ||
      bond.option.toLowerCase().includes(keyword)

    const matchesType = !hasSelected(filters.bondTypes) || filters.bondTypes.includes(bond.type)
    const matchesRating = !hasSelected(filters.ratings) || filters.ratings.includes(bond.ratingGroup)
    const matchesCycle = !hasSelected(filters.interestCycles) || filters.interestCycles.includes(bond.interestCycle)

    return (
      matchesKeyword &&
      matchesType &&
      matchesMaturity(bond, filters.maturities) &&
      matchesYield(bond, filters.yields) &&
      matchesRating &&
      matchesCycle
    )
  })
})

function resetFilters() {
  searchKeyword.value = ''
  selectedFilters.value = {
    bondTypes: [],
    maturities: [],
    yields: [],
    ratings: [],
    interestCycles: [],
  }
}
</script>

<template>
  <section class="page market-page">
    <!-- 검색 및 필터 섹션 -->
    <section class="search-panel market-search">
      <div class="search-box">
        <span aria-hidden="true">⌕</span>
        <input v-model="searchKeyword" type="search" placeholder="종목명, 코드, 종류로 검색하세요" />
        <button type="button" @click="filtersOpen = !filtersOpen">
          {{ filtersOpen ? '필터 접기' : '상세 필터' }}
        </button>
      </div>

      <div v-if="filtersOpen" class="filter-grid">
        <fieldset v-for="group in filterGroups" :key="group.key" class="filter-group">
          <legend>{{ group.label }}</legend>
          <label v-for="option in group.options" :key="option" class="filter-chip">
            <input v-model="selectedFilters[group.key]" type="checkbox" :value="option" />
            <span>{{ option }}</span>
          </label>
        </fieldset>
        <div class="filter-actions">
          <button class="btn-reset" type="button" @click="resetFilters">초기화</button>
        </div>
      </div>
    </section>

    <div class="toolbar market-toolbar">
      <div class="market-info">
        <p class="eyebrow">전체 채권 시세</p>
        <h1>{{ filteredBonds.length }}개의 채권이 검색되었습니다</h1>
      </div>
      <button class="compare-fab" :class="{ enabled: compareActive }" type="button" @click="$emit('navigate', 'compare')">
        비교하기
      </button>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>선택</th>
            <th>종목명(종목코드)</th>
            <th>구분</th>
            <th>현재가</th>
            <th>등락률</th>
            <th>매수/매도 수익률</th>
            <th>액션</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="bond in filteredBonds" :key="bond.code">
            <td><input v-model="compareActive" type="checkbox" /></td>
            <td>
              <div class="bond-name-cell">
                <strong>{{ bond.name }}</strong>
                <span class="code">{{ bond.code }}</span>
              </div>
            </td>
            <td>
              <span class="market-badge" :class="bond.marketType === '장내' ? 'internal' : 'external'">
                {{ bond.marketType }}
              </span>
            </td>
            <td class="price">{{ bond.price }}</td>
            <td :class="bond.change.startsWith('+') ? 'up' : 'down'">{{ bond.change }}</td>
            <td class="yields">{{ bond.buyYield }} / {{ bond.sellYield }}</td>
            <td><button class="small-action" type="button" @click="$emit('navigate', 'detail')">상세정보</button></td>
          </tr>
          <tr v-if="filteredBonds.length === 0">
            <td colspan="7" class="empty-cell">
              <div class="empty-msg">
                <p>조건에 맞는 채권이 없습니다.</p>
                <button type="button" @click="resetFilters">필터 초기화하기</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.market-search {
  margin-bottom: 32px;
  background: white;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid var(--line);
}

.market-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 16px;
}

.market-info h1 {
  font-size: 20px;
  font-weight: 800;
  margin-top: 4px;
}

.bond-name-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.bond-name-cell .code {
  font-size: 12px;
  color: var(--muted);
}

.market-badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.market-badge.internal {
  background: #eef4f8;
  color: var(--primary);
}

.market-badge.external {
  background: #fff7ec;
  color: var(--accent);
}

.filter-actions {
  grid-column: 1 / -1;
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
}

.btn-reset {
  background: transparent;
  border: none;
  color: var(--muted);
  text-decoration: underline;
  font-size: 14px;
}

.empty-msg {
  padding: 40px 0;
  color: var(--muted);
}

.empty-msg button {
  margin-top: 12px;
  color: var(--primary);
  font-weight: 600;
  background: transparent;
  border: 1px solid var(--primary);
  padding: 8px 16px;
  border-radius: 8px;
}

.price {
  font-weight: 700;
}

.yields {
  font-variant-numeric: tabular-nums;
}
</style>