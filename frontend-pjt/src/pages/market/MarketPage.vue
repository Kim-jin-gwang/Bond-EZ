<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { BOND_PAGE_SIZE, fetchBonds, fetchFilterOptions, fetchCuratedBonds } from '../../api/bonds'
import { createEmptyBondFilters } from '../../composables/useBondFilter'
import { useDebouncedRef } from '../../composables/useDebouncedRef'
import { useAppStore } from '../../stores/app'

const emit = defineEmits(['navigate'])

const props = defineProps({
  marketSearch: {
    type: Object,
    default: null,
  },
})

const appStore = useAppStore()
const isCuratedMode = ref(false)
const filtersOpen = ref(false)
const searchInput = ref(props.marketSearch?.keyword || '')
const searchKeyword = useDebouncedRef(searchInput)
const selectedBondCodes = ref([])
const selectedFilters = ref({
  bondTypes: props.marketSearch?.filters?.bondTypes || [],
  maturities: props.marketSearch?.filters?.maturities || [],
  minCoupon: props.marketSearch?.filters?.minCoupon !== undefined ? props.marketSearch.filters.minCoupon : '',
  maxCoupon: props.marketSearch?.filters?.maxCoupon !== undefined ? props.marketSearch.filters.maxCoupon : '',
  ratings: props.marketSearch?.filters?.ratings || [],
  interestCycles: props.marketSearch?.filters?.interestCycles || [],
  optionTypes: props.marketSearch?.filters?.optionTypes || [],
  seniorities: props.marketSearch?.filters?.seniorities || [],
  guaranteeStatuses: props.marketSearch?.filters?.guaranteeStatuses || [],
})
const showOnlyWithPrice = ref(true)
const excludeExpired = ref(true)
const bonds = ref([])
const isLoading = ref(false)
const error = ref(null)
const currentPage = ref(1)
const pageInfo = ref({
  number: 1,
  size: BOND_PAGE_SIZE,
  totalElements: 0,
  totalPages: 1,
})
let requestId = 0

const filterGroups = ref([
  {
    key: 'bondTypes',
    label: '채권 종류',
    options: [
      { value: '국채', label: '국채' },
      { value: '회사채', label: '회사채' },
      { value: '금융채', label: '금융채' },
    ],
  },
  {
    key: 'maturities',
    label: '만기',
    options: [
      { value: '1년 이하', label: '1년 이하' },
      { value: '1~3년', label: '1~3년' },
      { value: '3~5년', label: '3~5년' },
      { value: '5~10년', label: '5~10년' },
      { value: '10년 이상', label: '10년 이상' },
    ],
  },
  {
    key: 'couponRates',
    label: '표면금리',
  },
  {
    key: 'ratings',
    label: '신용등급',
    options: [
      { value: 'AAA', label: 'AAA' },
      { value: 'AA', label: 'AA' },
      { value: 'A', label: 'A' },
      { value: 'BBB', label: 'BBB' },
    ],
  },
  {
    key: 'interestCycles',
    label: '이자 지급 주기',
    options: [
      { value: '1개월', label: '1개월' },
      { value: '2개월', label: '2개월' },
      { value: '3개월', label: '3개월' },
      { value: '6개월', label: '6개월' },
      { value: '12개월', label: '12개월' },
      { value: '만기일시', label: '만기일시' },
    ],
  },
  {
    key: 'optionTypes',
    label: '옵션',
    options: [
      { value: 'CALL', label: 'CALL' },
      { value: 'PUT', label: 'PUT' },
      { value: '없음', label: '없음' },
    ],
  },
  {
    key: 'seniorities',
    label: '선후순위',
    options: [
      { value: '선순위', label: '선순위' },
      { value: '후순위', label: '후순위' },
    ],
  },
  {
    key: 'guaranteeStatuses',
    label: '보증 여부',
    options: [],
  },
])

const selectedBonds = computed(() =>
  selectedBondCodes.value
    .map((code) => bonds.value.find((bond) => bond.code === code))
    .filter(Boolean),
)

const canCompare = computed(() => selectedBondCodes.value.length === 2)

watch(() => props.marketSearch, (newVal) => {
  if (newVal) {
    isCuratedMode.value = newVal.source === 'curated'
    searchInput.value = newVal.keyword || ''
    if (newVal.filters) {
      selectedFilters.value = {
        bondTypes: newVal.filters.bondTypes || [],
        maturities: newVal.filters.maturities || [],
        minCoupon: newVal.filters.minCoupon !== undefined ? newVal.filters.minCoupon : '',
        maxCoupon: newVal.filters.maxCoupon !== undefined ? newVal.filters.maxCoupon : '',
        ratings: newVal.filters.ratings || [],
        interestCycles: newVal.filters.interestCycles || [],
        optionTypes: newVal.filters.optionTypes || [],
        seniorities: newVal.filters.seniorities || [],
        guaranteeStatuses: newVal.filters.guaranteeStatuses || [],
      }
    }
  }
}, { deep: true })

const visibleBonds = computed(() => bonds.value)
const pageButtons = computed(() => getPageButtons(currentPage.value, pageInfo.value.totalPages))

watch([searchKeyword, selectedFilters, showOnlyWithPrice, excludeExpired], () => {
  currentPage.value = 1
  loadBonds()
}, { deep: true })

watch(currentPage, () => {
  selectedBondCodes.value = []
  loadBonds()
})

function resetFilters() {
  searchInput.value = ''
  selectedFilters.value = createEmptyBondFilters()
}

function clearGroupFilter(key) {
  if (key === 'couponRates') {
    selectedFilters.value.minCoupon = ''
    selectedFilters.value.maxCoupon = ''
  } else {
    selectedFilters.value[key] = []
  }
}

function isBondSelected(code) {
  return selectedBondCodes.value.includes(code)
}

function isSelectionDisabled(code) {
  return !isBondSelected(code) && selectedBondCodes.value.length >= 2
}

function toggleBondSelection(code) {
  if (isBondSelected(code)) {
    selectedBondCodes.value = selectedBondCodes.value.filter((selectedCode) => selectedCode !== code)
    return
  }

  if (selectedBondCodes.value.length < 2) {
    selectedBondCodes.value = [...selectedBondCodes.value, code]
  }
}

function compareSelectedBonds() {
  if (!canCompare.value) {
    return
  }

  emit('navigate', 'compare', {
    source: 'market',
    bonds: selectedBonds.value,
  })
}

async function loadBonds() {
  const activeRequest = ++requestId
  isLoading.value = true
  error.value = null

  try {
    let result
    if (isCuratedMode.value) {
      const items = await fetchCuratedBonds({ limit: 50 })
      result = {
        items: items,
        page: {
          number: 1,
          size: items.length,
          totalElements: items.length,
          totalPages: 1,
        }
      }
    } else {
      result = await fetchBonds(buildBondParams())
    }
    if (activeRequest !== requestId) return
    bonds.value = result.items
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

function reloadBonds() {
  loadBonds()
}

function buildBondParams() {
  const filters = selectedFilters.value
  const params = {
    page: currentPage.value,
    size: BOND_PAGE_SIZE,
    keyword: searchKeyword.value.trim(),
  }

  if (showOnlyWithPrice.value) {
    params.has_price = true
  }

  if (excludeExpired.value) {
    params.exclude_expired = true
  }

  if (filters.bondTypes.length) params.bond_type = filters.bondTypes
  if (filters.maturities.length) params.maturity_bucket = filters.maturities
  if (filters.minCoupon !== '' && filters.minCoupon !== null && filters.minCoupon !== undefined) {
    params.min_coupon = filters.minCoupon
  }
  if (filters.maxCoupon !== '' && filters.maxCoupon !== null && filters.maxCoupon !== undefined) {
    params.max_coupon = filters.maxCoupon
  }
  if (filters.ratings.length) params.rating_group = filters.ratings
  if (filters.optionTypes.length) params.option_type = filters.optionTypes
  if (filters.seniorities.length) params.seniority = filters.seniorities
  if (filters.guaranteeStatuses && filters.guaranteeStatuses.length) {
    params.guarantee_status = filters.guaranteeStatuses
  }


  const paymentCycles = filters.interestCycles
    .map((cycle) => Number(cycle.replace(/[^0-9]/g, '')))
    .filter(Number.isFinite)

  if (paymentCycles.length) {
    params.payment_cycle_months = paymentCycles
  }

  return params
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

function formatOptionLabel(option) {
  const label = String(option || '').trim()

  if (!label || label === '-') return '-'
  if (label.includes('해당사항없음') || label.includes('해당 사항 없음')) return '해당사항 없음'
  if (label.includes('없음')) return '없음'
  return label
}

async function loadFilterOptions() {
  try {
    const data = await fetchFilterOptions()
    if (!data) return

    const groups = JSON.parse(JSON.stringify(filterGroups.value))

    if (data.bond_types && data.bond_types.length) {
      const group = groups.find(g => g.key === 'bondTypes')
      if (group) {
        group.options = data.bond_types.map(t => ({
          value: t.bond_type,
          label: t.bond_type,
        }))
      }
    }

    if (data.credit_ratings && data.credit_ratings.length) {
      const group = groups.find(g => g.key === 'ratings')
      if (group) {
        const uniqueGroups = Array.from(
          new Set(
            data.credit_ratings.map(r => r.rating_name.replace(/[+-0-9]/g, '').trim())
          )
        ).filter(Boolean)
        
        group.options = uniqueGroups.map(name => ({
          value: name,
          label: name,
        }))
      }
    }

    if (data.seniorities && data.seniorities.length) {
      const group = groups.find(g => g.key === 'seniorities')
      if (group) {
        group.options = data.seniorities.map(s => ({
          value: s.seniority_name,
          label: s.seniority_name,
        }))
      }
    }

    if (data.guarantee_statuses && data.guarantee_statuses.length) {
      const group = groups.find(g => g.key === 'guaranteeStatuses')
      if (group) {
        group.options = data.guarantee_statuses.map(g => ({
          value: g.guarantee_status,
          label: g.guarantee_status,
        }))
      }
    }

    filterGroups.value = groups
  } catch (err) {
    console.error('Failed to load filter options:', err)
  }
}

async function handleFavoriteToggle(bondId) {
  if (!appStore.isLoggedIn) {
    alert('관심 채권 등록은 로그인이 필요한 서비스입니다.')
    return
  }
  try {
    await appStore.toggleFavorite(bondId)
  } catch (err) {
    console.error('Failed to toggle favorite:', err)
  }
}

function clearCuratedMode() {
  isCuratedMode.value = false
  loadBonds()
}

onMounted(() => {
  if (props.marketSearch?.source === 'curated') {
    isCuratedMode.value = true
  }
  loadFilterOptions()
  loadBonds()
})
</script>

<template>
  <section class="page market-page">
    <section class="search-panel market-search">
      <div class="search-box">
        <span aria-hidden="true">⌕</span>
        <label class="sr-only" for="bond-search">채권 검색어</label>
        <input
          id="bond-search"
          v-model="searchInput"
          type="search"
          autocomplete="off"
          placeholder="종목명, 단축코드, 발행기관으로 검색하세요"
        />
        <button type="button" @click="filtersOpen = !filtersOpen">
          {{ filtersOpen ? '필터 접기' : '상세 필터' }}
        </button>
      </div>

      <div v-if="filtersOpen" class="filter-grid">
        <fieldset v-for="group in filterGroups" :key="group.key" class="filter-group">
          <legend>{{ group.label }}</legend>
          <template v-if="group.key === 'couponRates'">
            <div class="coupon-range-wrapper">
              <label class="filter-chip">
                <input
                  type="checkbox"
                  :checked="selectedFilters.minCoupon === '' && selectedFilters.maxCoupon === ''"
                  @change="clearGroupFilter('couponRates')"
                />
                <span>전체</span>
              </label>
              <div class="coupon-range-inputs">
                <input
                  type="number"
                  v-model="selectedFilters.minCoupon"
                  placeholder="최소 (%)"
                  step="0.1"
                  min="0"
                  class="coupon-input"
                />
                <span class="range-separator">~</span>
                <input
                  type="number"
                  v-model="selectedFilters.maxCoupon"
                  placeholder="최대 (%)"
                  step="0.1"
                  min="0"
                  class="coupon-input"
                />
              </div>
            </div>
          </template>
          <template v-else>
            <label class="filter-chip">
              <input
                type="checkbox"
                :checked="selectedFilters[group.key].length === 0"
                @change="clearGroupFilter(group.key)"
              />
              <span>전체</span>
            </label>
            <label v-for="option in group.options" :key="option.value" class="filter-chip">
              <input v-model="selectedFilters[group.key]" type="checkbox" :value="option.value" />
              <span>{{ option.label }}</span>
            </label>
          </template>
        </fieldset>
        <div class="filter-actions">
          <button class="btn-reset" type="button" @click="resetFilters">초기화</button>
        </div>
      </div>
    </section>

    <div v-if="isCuratedMode" class="curated-banner">
      <div class="banner-content">
        <span class="banner-icon">✨</span>
        <span><strong>나의 맞춤 추천 채권</strong>을 골라 보았어요.</span>
        <button class="btn-clear-curated" type="button" @click="clearCuratedMode">전체 채권 보기</button>
      </div>
    </div>

    <div class="toolbar market-toolbar">
      <div class="market-info">
        <p class="eyebrow">{{ isCuratedMode ? '맞춤 큐레이션 추천 채권' : '전체 채권 시세' }}</p>
        <h1 aria-live="polite">{{ isCuratedMode ? '나에게 맞춰 큐레이션된 추천 채권이 ' + bonds.length + '개 있습니다' : pageInfo.totalElements + '개의 채권이 검색되었습니다' }}</h1>
        <p class="selection-help">비교할 채권을 최대 2개까지 선택하세요. 현재 {{ selectedBondCodes.length }}/2개 선택</p>
      </div>
      <div class="toolbar-actions" style="display: flex; align-items: center; gap: 16px;">
        <label class="price-filter-toggle" style="display: flex; align-items: center; gap: 6px; font-weight: 500; cursor: pointer; user-select: none;">
          <input type="checkbox" v-model="showOnlyWithPrice" />
          <span>거래 중인 채권만 보기</span>
        </label>
        <label class="expired-filter-toggle" style="display: flex; align-items: center; gap: 6px; font-weight: 500; cursor: pointer; user-select: none; margin-right: 8px;">
          <input type="checkbox" v-model="excludeExpired" />
          <span>만기된 채권 제외</span>
        </label>
        <button
          class="compare-fab"
          :class="{ enabled: canCompare }"
          type="button"
          :disabled="!canCompare"
          @click="compareSelectedBonds"
        >
          비교하기
        </button>
      </div>
    </div>

    <section v-if="isLoading" class="market-state" aria-live="polite">
      <strong>채권 데이터를 불러오는 중입니다.</strong>
      <p>캐시된 데이터가 있으면 먼저 보여주고, 최신 데이터를 다시 확인합니다.</p>
    </section>

    <section v-if="error" class="market-state error-state" role="alert">
      <strong>채권 데이터를 불러오지 못했습니다.</strong>
      <p>{{ error.message || '잠시 후 다시 시도해주세요.' }}</p>
      <button type="button" @click="reloadBonds">다시 시도</button>
    </section>

    <div class="table-wrap">
      <table>
        <caption class="sr-only">채권 시세 검색 결과</caption>
        <thead>
          <tr>
            <th>선택</th>
            <th>종목명</th>
            <th>발행기관</th>
            <th>분류</th>
            <th>현재가</th>
            <th>등락률</th>
            <th>표면 금리</th>
            <th>옵션/행사일</th>
            <th>만기/이자</th>
            <th>상세</th>
            <th>즐겨찾기</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="bond in visibleBonds" :key="bond.code" :class="{ selected: isBondSelected(bond.code) }">
            <td>
              <input
                type="checkbox"
                :aria-label="`${bond.shortName} 비교 선택`"
                :checked="isBondSelected(bond.code)"
                :disabled="isSelectionDisabled(bond.code)"
                @change="toggleBondSelection(bond.code)"
              />
            </td>
            <td class="bond-title-cell">
              <div class="bond-name-cell">
                <strong>{{ bond.name }}</strong>
                <span class="code">{{ bond.code }} · {{ bond.shortCode }}</span>
              </div>
            </td>
            <td class="issuer-cell">
              <strong>{{ bond.issuer }}</strong>
              <span>{{ bond.industry }}</span>
            </td>
            <td class="classification-cell">
              <span class="market-badge" :class="bond.marketType === '장내' ? 'internal' : 'external'">{{ bond.marketType }}</span>
              <span class="nowrap">{{ bond.type }} · {{ bond.seniority }}</span>
              <span class="nowrap">{{ bond.rating }}</span>
            </td>
            <td class="price">{{ bond.price }}</td>
            <td :class="bond.change.startsWith('+') ? 'up' : 'down'">{{ bond.change }}</td>
            <td class="yields">{{ bond.coupon }}</td>
            <td class="option-cell">
              <strong>{{ formatOptionLabel(bond.option) }}</strong>
              <span class="nowrap">{{ bond.optionExercise?.startDate1 || '-' }}</span>
            </td>
            <td class="maturity-cell">
              <strong>{{ bond.maturity }}</strong>
              <span class="nowrap">{{ bond.interestCycle }} · {{ bond.interestType }}</span>
            </td>
            <td class="action-cell">
              <button class="small-action" type="button" @click="$emit('navigate', 'detail', { bond })">상세정보</button>
            </td>
            <td class="favorite-cell">
              <button 
                class="btn-favorite" 
                type="button" 
                @click="handleFavoriteToggle(bond.bondId)"
                :class="{ active: appStore.isFavorite(bond.bondId) }"
                title="관심 채권 등록/해제"
              >
                {{ appStore.isFavorite(bond.bondId) ? '★' : '☆' }}
              </button>
            </td>
          </tr>
          <tr v-if="!isLoading && visibleBonds.length === 0">
            <td colspan="11" class="empty-cell">
              <div class="empty-msg">
                <p>조건에 맞는 채권이 없습니다.</p>
                <button type="button" @click="resetFilters">필터 초기화하기</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
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
</template>

<style scoped>
.market-search {
  margin-bottom: 32px;
  padding: 24px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
}

.sr-only {
  position: absolute;
  overflow: hidden;
  width: 1px;
  height: 1px;
  padding: 0;
  border: 0;
  margin: -1px;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}

.market-state {
  display: grid;
  gap: 6px;
  margin-bottom: 16px;
  padding: 14px 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.market-state p {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
}

.error-state {
  border-color: #f2c7c7;
  background: #fff7f7;
}

.error-state button,
.pagination button {
  width: fit-content;
  min-height: 38px;
  border: 1px solid var(--primary);
  border-radius: 8px;
  padding: 0 14px;
  color: var(--primary);
  background: white;
  font-weight: 800;
}

.market-page :is(th, td, strong, span, button) {
  word-break: keep-all;
}

.market-page table {
  table-layout: fixed;
  min-width: 0;
}

.market-page th,
.market-page td {
  overflow: hidden;
  padding: 13px 10px;
  vertical-align: middle;
}

.market-page th:last-child,
.market-page td:last-child {
  padding-right: 18px;
}

.market-page th {
  font-size: 13px;
}

.market-page .table-wrap {
  overflow: hidden;
}

.market-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 16px;
}

.market-info h1 {
  margin: 4px 0 6px;
  font-size: 20px;
  font-weight: 800;
}

.selection-help {
  margin-bottom: 0;
  font-size: 14px;
}

.compare-fab:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

tr.selected {
  background: #f3faf9;
}

.bond-name-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.bond-name-cell strong,
.issuer-cell strong,
.classification-cell span,
.option-cell strong,
.maturity-cell strong,
.maturity-cell span {
  display: block;
  overflow: hidden;
  max-width: 100%;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-cell {
  text-align: right;
}

.bond-name-cell .code {
  color: var(--muted);
  font-size: 12px;
  white-space: normal;
}

.market-badge {
  display: inline-block;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.market-badge.internal {
  color: var(--primary);
  background: #eef4f8;
}

.market-badge.external {
  color: var(--accent);
  background: #fff7ec;
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
  border: 0;
  color: var(--muted);
  background: transparent;
  font-size: 14px;
  text-decoration: underline;
}

.empty-msg {
  padding: 40px 0;
  color: var(--muted);
}

.empty-msg button {
  margin-top: 12px;
  border: 1px solid var(--primary);
  border-radius: 8px;
  padding: 8px 16px;
  color: var(--primary);
  background: transparent;
  font-weight: 600;
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
}

.pagination button.active {
  color: white;
  background: var(--primary);
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.price {
  font-weight: 700;
  white-space: nowrap;
}

.yields {
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.nowrap {
  white-space: nowrap;
}

.small-action {
  min-width: 52px;
  padding-inline: 8px;
  white-space: nowrap;
}

.market-page th:first-child,
.market-page td:first-child {
  width: 44px;
}

.market-page th:nth-child(2),
.market-page td:nth-child(2) {
  width: 17%;
}

.market-page th:nth-child(3),
.market-page td:nth-child(3) {
  width: 12%;
}

.market-page th:nth-child(4),
.market-page td:nth-child(4) {
  width: 12%;
}

.market-page th:nth-child(5),
.market-page td:nth-child(5) {
  width: 8%;
}

.market-page th:nth-child(6),
.market-page td:nth-child(6) {
  width: 7%;
}

.market-page th:nth-child(7),
.market-page td:nth-child(7) {
  width: 11%;
}

.market-page th:nth-child(8),
.market-page td:nth-child(8) {
  width: 10%;
}

.market-page th:nth-child(9),
.market-page td:nth-child(9) {
  width: 11%;
}

.market-page th:nth-child(10),
.market-page td:nth-child(10) {
  width: 8%;
}

.market-page th:nth-child(11),
.market-page td:nth-child(11) {
  width: 6%;
}

.favorite-cell {
  text-align: center;
}

.curated-banner {
  background: linear-gradient(90deg, #eff6ff 0%, #dbeafe 100%);
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 12px 18px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.05);
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1e40af;
  font-size: 14px;
}

.banner-icon {
  font-size: 16px;
}

.btn-clear-curated {
  background: white;
  border: 1px solid #3b82f6;
  color: #3b82f6;
  padding: 6px 14px;
  border-radius: 6px;
  font-weight: 800;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-clear-curated:hover {
  background: #3b82f6;
  color: white;
}

.action-wrap {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.btn-favorite {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
  color: #cbd5e1;
  transition: transform 0.2s ease, color 0.2s ease;
}

.btn-favorite:hover {
  transform: scale(1.25);
  color: #fbbf24;
}

.btn-favorite.active {
  color: #fbbf24;
}
</style>
