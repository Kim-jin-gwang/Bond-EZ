<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import GlobalNav from './components/gnb/GlobalNav.vue'
import HomePage from './pages/home/HomePage.vue'
import MarketPage from './pages/market/MarketPage.vue'
import BondDetailPage from './pages/bond-detail/BondDetailPage.vue'
import ComparePage from './pages/compare/ComparePage.vue'
import IndicatorsPage from './pages/indicators/IndicatorsPage.vue'
import LoginProfilePage from './pages/member/LoginProfilePage.vue'
import NewsPage from './pages/news/NewsPage.vue'
import DictionaryPage from './pages/dictionary/DictionaryPage.vue'
import GuidePage from './pages/guide/GuidePage.vue'

const currentPage = ref('home')
const currentSubPage = ref(null)
const selectedIndicatorId = ref('treasury-rate')
const marketSearch = ref(null)
const compareBonds = ref([])
const isLoggedIn = ref(false)
const user = ref({
  name: '윤투자',
  email: 'bond@example.com',
  type: '안정추구형',
  avatar: '윤'
})

const pages = {
  home: HomePage,
  market: MarketPage,
  detail: BondDetailPage,
  compare: ComparePage,
  indicators: IndicatorsPage,
  profile: LoginProfilePage,
  news: NewsPage,
  dictionary: DictionaryPage,
  guide: GuidePage,
}

function buildHash(page, subPage, indicatorId) {
  const params = new URLSearchParams()
  params.set('page', page)

  if (subPage) {
    params.set('sub', subPage)
  }

  if (page === 'indicators') {
    params.set('indicator', indicatorId)
  }

  return `#${params.toString()}`
}

function readRoute() {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ''))
  const page = pages[params.get('page')] ? params.get('page') : 'home'
  const subPage = params.get('sub')
  const indicatorId = params.get('indicator') || 'treasury-rate'

  return { page, subPage, indicatorId }
}

function applyRoute(page, subPage, indicatorId, searchPayload, comparePayload) {
  currentPage.value = page
  currentSubPage.value = subPage

  if (page === 'indicators') {
    selectedIndicatorId.value = indicatorId
  }

  if (page === 'market') {
    marketSearch.value = searchPayload?.source === 'search' ? searchPayload : null
  }

  if (page === 'compare') {
    compareBonds.value = comparePayload?.bonds || compareBonds.value
  }
}

function navigate(page, payload, options = {}) {
  let subPage = null
  let indicatorId = selectedIndicatorId.value
  let searchPayload = marketSearch.value
  let comparePayload = null

  if (page === 'guide') {
    subPage = payload || 'what'
  } else if (page === 'indicators') {
    indicatorId = payload || selectedIndicatorId.value
  } else if (page === 'market') {
    searchPayload = payload
  } else if (page === 'compare') {
    comparePayload = payload
  }

  applyRoute(page, subPage, indicatorId, searchPayload, comparePayload)

  const state = { page, subPage, indicatorId, searchPayload, comparePayload }
  const hash = buildHash(page, subPage, indicatorId)

  if (options.replace) {
    window.history.replaceState(state, '', hash)
  } else {
    window.history.pushState(state, '', hash)
  }

  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleLogin() {
  isLoggedIn.value = true
}

function handleLogout() {
  isLoggedIn.value = false
}

function handlePopState() {
  const route = readRoute()
  const state = window.history.state
  applyRoute(
    state?.page || route.page,
    state?.subPage || route.subPage,
    state?.indicatorId || route.indicatorId,
    state?.searchPayload || null,
    state?.comparePayload || null
  )
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  const { page, subPage, indicatorId } = readRoute()
  navigate(page, page === 'guide' ? subPage : indicatorId, { replace: true })
  window.addEventListener('popstate', handlePopState)
})

onBeforeUnmount(() => {
  window.removeEventListener('popstate', handlePopState)
})
</script>

<template>
  <div class="app-shell">
    <GlobalNav :active-page="currentPage" @navigate="navigate" />
    <main>
      <component
        :is="pages[currentPage]"
        :selected-indicator-id="selectedIndicatorId"
        :market-search="marketSearch"
        :compare-bonds="compareBonds"
        :is-logged-in="isLoggedIn"
        :user="user"
        :current-sub-page="currentSubPage"
        @navigate="navigate"
        @login="handleLogin"
        @logout="handleLogout"
      />
    </main>
  </div>
</template>
