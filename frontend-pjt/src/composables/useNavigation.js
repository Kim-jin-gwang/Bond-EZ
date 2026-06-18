import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'

const routeNames = {
  home: 'home',
  market: 'market',
  detail: 'detail',
  compare: 'compare',
  indicators: 'indicators',
  profile: 'profile',
  news: 'news',
  dictionary: 'dictionary',
  guide: 'guide',
}

export function useNavigation() {
  const router = useRouter()
  const appStore = useAppStore()

  function navigate(page, payload) {
    if (page === 'guide') {
      router.push({ name: 'guide', params: { subPage: payload || 'what' } })
      return
    }

    if (page === 'indicators') {
      const indicatorId = payload || appStore.selectedIndicatorId
      appStore.setIndicator(indicatorId)
      router.push({ name: 'indicators', params: { indicatorId } })
      return
    }

    if (page === 'market') {
      appStore.setMarketSearch(payload)
    }

    if (page === 'compare') {
      appStore.setCompareBonds(payload?.bonds || appStore.compareBonds)
      const ids = appStore.compareBonds.map((bond) => bond.bondId).filter(Boolean)
      router.push({
        name: 'compare',
        query: ids.length === 2 ? { ids: ids.join(',') } : undefined,
      })
      return
    }

    if (page === 'detail') {
      appStore.setSelectedBond(payload?.bond || appStore.selectedBond)
      router.push({
        name: 'detail',
        params: { bondId: appStore.selectedBond?.bondId || '' },
      })
      return
    }

    router.push({ name: routeNames[page] || 'home' })
  }

  return { navigate }
}
