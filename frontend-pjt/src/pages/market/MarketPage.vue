<script setup>
import { computed, ref, watch } from 'vue'
import { fetchBonds } from '../../api/bonds'
import { useAsyncData } from '../../composables/useAsyncData'
import { createEmptyBondFilters, useBondFilter } from '../../composables/useBondFilter'
import { useDebouncedRef } from '../../composables/useDebouncedRef'

const {
  data: bonds,
  isLoading,
  error,
  execute: reloadBonds,
} = useAsyncData(fetchBonds, {
  initialData: [],
})

const emit = defineEmits(['navigate'])

const props = defineProps({
  marketSearch: {
    type: Object,
    default: null,
  },
})

const filtersOpen = ref(false)
const searchInput = ref(props.marketSearch?.keyword || '')
const searchKeyword = useDebouncedRef(searchInput)
const selectedBondCodes = ref([])
const visibleLimit = ref(50)
const selectedFilters = ref({
  ...createEmptyBondFilters(),
  ...props.marketSearch?.filters,
})

const filterGroups = [
  { key: 'bondTypes', label: '채권 종류', options: ['국채', '회사채', '금융채'] },
  { key: 'maturities', label: '만기', options: ['1년 이하', '1~3년', '3~5년', '5~10년', '10년 이상'] },
  { key: 'yields', label: '수익률', options: ['3% 이상', '4% 이상', '5% 이상', '6% 이상'] },
  { key: 'ratings', label: '신용등급', options: ['AAA', 'AA', 'A', 'BBB'] },
  { key: 'interestCycles', label: '이자 지급 주기', options: ['3개월', '6개월', '12개월', '만기일시'] },
  { key: 'optionTypes', label: '옵션', options: ['CALL', 'PUT', '없음'] },
  { key: 'seniorities', label: '선후순위', options: ['선순위', '후순위'] },
]

const selectedBonds = computed(() =>
  selectedBondCodes.value
    .map((code) => bonds.value.find((bond) => bond.code === code))
    .filter(Boolean),
)

const canCompare = computed(() => selectedBondCodes.value.length === 2)

watch(() => props.marketSearch, (newVal) => {
  if (newVal) {
    searchInput.value = newVal.keyword || ''
    if (newVal.filters) {
      selectedFilters.value = {
        bondTypes: newVal.filters.bondTypes || [],
        maturities: newVal.filters.maturities || [],
        yields: newVal.filters.yields || [],
        ratings: newVal.filters.ratings || [],
        interestCycles: newVal.filters.interestCycles || [],
        optionTypes: newVal.filters.optionTypes || [],
        seniorities: newVal.filters.seniorities || [],
      }
    }
  }
}, { deep: true })

watch([searchKeyword, selectedFilters], () => {
  visibleLimit.value = 50
}, { deep: true })

const { filteredBonds } = useBondFilter(bonds, searchKeyword, selectedFilters)
const visibleBonds = computed(() => filteredBonds.value.slice(0, visibleLimit.value))
const hasMoreBonds = computed(() => visibleBonds.value.length < filteredBonds.value.length)

function resetFilters() {
  searchInput.value = ''
  selectedFilters.value = createEmptyBondFilters()
}

function showMoreBonds() {
  visibleLimit.value += 50
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

function formatOptionLabel(option) {
  const label = String(option || '').trim()

  if (!label || label === '-') return '-'
  if (label.includes('해당사항없음') || label.includes('해당 사항 없음')) return '해당사항 없음'
  if (label.includes('없음')) return '없음'
  return label
}
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
        <h1 aria-live="polite">{{ filteredBonds.length }}개의 채권이 검색되었습니다</h1>
        <p class="selection-help">비교할 채권을 최대 2개까지 선택하세요. 현재 {{ selectedBondCodes.length }}/2개 선택</p>
      </div>
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
            <th>매수/매도 수익률</th>
            <th>옵션/행사일</th>
            <th>만기/이자</th>
            <th>상세</th>
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
            <td class="yields">{{ bond.buyYield }} / {{ bond.sellYield }}</td>
            <td class="option-cell">
              <strong>{{ formatOptionLabel(bond.option) }}</strong>
              <span class="nowrap">{{ bond.optionExercise?.startDate1 || '-' }}</span>
            </td>
            <td class="maturity-cell">
              <strong>{{ bond.maturity }}</strong>
              <span class="nowrap">{{ bond.interestCycle }} · {{ bond.interestType }}</span>
            </td>
            <td class="action-cell"><button class="small-action" type="button" @click="$emit('navigate', 'detail', { bond })">상세정보</button></td>
          </tr>
          <tr v-if="!isLoading && filteredBonds.length === 0">
            <td colspan="10" class="empty-cell">
              <div class="empty-msg">
                <p>조건에 맞는 채권이 없습니다.</p>
                <button type="button" @click="resetFilters">필터 초기화하기</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="hasMoreBonds" class="more-results">
      <button type="button" @click="showMoreBonds">
        {{ filteredBonds.length - visibleBonds.length }}개 더 보기
      </button>
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
.more-results button {
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

.more-results {
  display: flex;
  justify-content: center;
  margin-top: 18px;
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
  width: 18%;
}

.market-page th:nth-child(3),
.market-page td:nth-child(3) {
  width: 14%;
}

.market-page th:nth-child(4),
.market-page td:nth-child(4) {
  width: 14%;
}

.market-page th:nth-child(5),
.market-page td:nth-child(5),
.market-page th:nth-child(6),
.market-page td:nth-child(6) {
  width: 8%;
}

.market-page th:nth-child(7),
.market-page td:nth-child(7) {
  width: 10%;
}

.market-page th:nth-child(8),
.market-page td:nth-child(8) {
  width: 11%;
}

.market-page th:nth-child(9),
.market-page td:nth-child(9) {
  width: 11%;
}

.market-page th:nth-child(10),
.market-page td:nth-child(10) {
  width: 8%;
}

</style>
