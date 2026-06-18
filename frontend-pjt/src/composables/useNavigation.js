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
    }

    router.push({ name: routeNames[page] || 'home' })
  }

  return { navigate }
}
