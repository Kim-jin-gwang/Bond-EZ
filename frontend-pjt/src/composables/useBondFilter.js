import { computed } from 'vue'

export function createEmptyBondFilters() {
  return {
    bondTypes: [],
    maturities: [],
    yields: [],
    ratings: [],
    interestCycles: [],
    optionTypes: [],
    seniorities: [],
  }
}

export function useBondFilter(bonds, searchKeyword, selectedFilters) {
  const filteredBonds = computed(() => {
    const keyword = searchKeyword.value.toLowerCase()
    const filters = selectedFilters.value

    return bonds.filter((bond) => {
      const matchesKeyword =
        !keyword ||
        bond.name.toLowerCase().includes(keyword) ||
        bond.shortName.toLowerCase().includes(keyword) ||
        bond.code.toLowerCase().includes(keyword) ||
        bond.shortCode.toLowerCase().includes(keyword) ||
        bond.issuer.toLowerCase().includes(keyword) ||
        bond.type.toLowerCase().includes(keyword) ||
        bond.option.toLowerCase().includes(keyword)

      return (
        matchesKeyword &&
        matchesIncluded(filters.bondTypes, bond.type) &&
        matchesMaturity(bond, filters.maturities) &&
        matchesYield(bond, filters.yields) &&
        matchesIncluded(filters.ratings, bond.ratingGroup) &&
        matchesIncluded(filters.interestCycles, bond.interestCycle) &&
        matchesIncluded(filters.optionTypes, bond.option) &&
        matchesIncluded(filters.seniorities, bond.seniority)
      )
    })
  })

  return { filteredBonds }
}

function hasSelected(values) {
  return Array.isArray(values) && values.length > 0
}

function matchesIncluded(values, target) {
  return !hasSelected(values) || values.includes(target)
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
