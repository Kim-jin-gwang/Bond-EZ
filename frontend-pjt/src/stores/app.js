import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    selectedIndicatorId: 'treasury-rate',
    marketSearch: null,
    compareBonds: [],
    selectedBond: null,
    isLoggedIn: false,
    user: {
      name: '윤투자',
      email: 'bond@example.com',
      type: '안정추구형',
      avatar: '윤',
    },
  }),
  actions: {
    setIndicator(indicatorId = 'treasury-rate') {
      this.selectedIndicatorId = indicatorId
    },
    setMarketSearch(searchPayload = null) {
      this.marketSearch = searchPayload?.source === 'search' ? searchPayload : null
    },
    setCompareBonds(bonds = []) {
      this.compareBonds = bonds
    },
    setSelectedBond(bond = null) {
      this.selectedBond = bond
    },
    login() {
      this.isLoggedIn = true
    },
    logout() {
      this.isLoggedIn = false
    },
  },
})
