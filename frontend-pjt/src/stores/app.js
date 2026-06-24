import { defineStore } from 'pinia'
import { loginApi, logoutApi, fetchMeApi, withdrawApi } from '../api/auth'
import { fetchFavorites, addFavorite, removeFavorite } from '../api/bonds'

export const useAppStore = defineStore('app', {
  state: () => ({
    selectedIndicatorId: 'treasury-rate',
    marketSearch: null,
    compareBonds: [],
    selectedBond: null,
    isLoggedIn: false,
    user: null,
    favoriteBonds: [],
    favoriteBondIds: new Set(),
    recentBonds: JSON.parse(localStorage.getItem('recent_bonds') || '[]'),
  }),
  actions: {
    setIndicator(indicatorId = 'treasury-rate') {
      this.selectedIndicatorId = indicatorId
    },
    setMarketSearch(searchPayload = null) {
      this.marketSearch = (searchPayload?.source === 'search' || searchPayload?.source === 'curated') ? searchPayload : null
    },
    setCompareBonds(bonds = []) {
      this.compareBonds = bonds
    },
    setSelectedBond(bond = null) {
      this.selectedBond = bond
    },
    addRecentBond(bond) {
      if (!bond) return
      const filtered = this.recentBonds.filter(b => String(b.bondId) !== String(bond.bondId))
      filtered.unshift(bond)
      this.recentBonds = filtered.slice(0, 10)
      localStorage.setItem('recent_bonds', JSON.stringify(this.recentBonds))
    },
    
    // Check if session is already active on boot
    async checkAuth() {
      try {
        const data = await fetchMeApi()
        const rawUser = data?.user || data
        if (rawUser) {
          this.user = this.normalizeUser(rawUser)
          this.isLoggedIn = true
          await this.loadFavorites()
        } else {
          this.clearUserData()
        }
      } catch {
        this.clearUserData()
      }
    },

    // Handle real login via credentials
    async login(credentials) {
      try {
        const data = await loginApi(credentials)
        const rawUser = data?.user || data
        this.user = this.normalizeUser(rawUser)
        this.isLoggedIn = true
        await this.loadFavorites()
        return true
      } catch (err) {
        this.clearUserData()
        throw err
      }
    },

    // Handle real logout
    async logout() {
      try {
        await logoutApi()
      } catch (err) {
        console.error('Logout failed:', err)
      } finally {
        this.clearUserData()
      }
    },

    // Handle account withdrawal (deletion)
    async withdraw() {
      try {
        await withdrawApi()
      } catch (err) {
        console.error('Account withdrawal failed:', err)
        throw err
      } finally {
        this.clearUserData()
      }
    },

    // Load user's favorite bonds
    async loadFavorites() {
      if (!this.isLoggedIn) return
      try {
        const data = await fetchFavorites()
        const items = data?.items || data || []
        this.favoriteBonds = items
        this.favoriteBondIds = new Set(items.map(b => String(b.bondId)))
      } catch (err) {
        console.error('Failed to load favorites:', err)
      }
    },

    // Toggle favorite bond (star ★)
    async toggleFavorite(bondId) {
      if (!this.isLoggedIn) {
        throw new Error('UNAUTHORIZED')
      }
      
      const normalizedId = String(bondId)
      const isFav = this.favoriteBondIds.has(normalizedId)
      
      if (isFav) {
        this.favoriteBondIds.delete(normalizedId)
        this.favoriteBondIds = new Set(this.favoriteBondIds) // Vue 반응성 트리거
        const originalBonds = [...this.favoriteBonds]
        this.favoriteBonds = this.favoriteBonds.filter(b => String(b.bondId) !== normalizedId)
        
        try {
          await removeFavorite(normalizedId)
        } catch (err) {
          console.error('Failed to remove favorite:', err)
          this.favoriteBondIds.add(normalizedId)
          this.favoriteBondIds = new Set(this.favoriteBondIds) // Vue 반응성 트리거
          this.favoriteBonds = originalBonds
          alert('관심 채권 해제에 실패했습니다.')
        }
      } else {
        this.favoriteBondIds.add(normalizedId)
        this.favoriteBondIds = new Set(this.favoriteBondIds) // Vue 반응성 트리거
        try {
          const newFavBond = await addFavorite(normalizedId)
          if (newFavBond) {
            if (!this.favoriteBonds.some(b => String(b.bondId) === normalizedId)) {
              this.favoriteBonds.push(newFavBond)
            }
          }
        } catch (err) {
          console.error('Failed to add favorite:', err)
          this.favoriteBondIds.delete(normalizedId)
          this.favoriteBondIds = new Set(this.favoriteBondIds) // Vue 반응성 트리거
          alert('관심 채권 등록에 실패했습니다.')
        }
      }
    },

    isFavorite(bondId) {
      return this.favoriteBondIds.has(String(bondId))
    },

    clearUserData() {
      this.user = null
      this.isLoggedIn = false
      this.favoriteBonds = []
      this.favoriteBondIds = new Set()
    },

    normalizeUser(rawUser) {
      if (!rawUser) return null
      const fullName = (rawUser.last_name || '') + (rawUser.first_name || '')
      const name = fullName.trim() || rawUser.username || '투자자'
      return {
        id: rawUser.user_id || rawUser.id,
        username: rawUser.username,
        email: rawUser.email || 'no-email@example.com',
        name: name,
        avatar: name.charAt(0),
        type: rawUser.type || '안정추구형',
      }
    }
  },
})
