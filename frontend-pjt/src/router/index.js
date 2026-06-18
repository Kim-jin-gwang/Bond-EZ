import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../pages/home/HomePage.vue'
import MarketPage from '../pages/market/MarketPage.vue'
import BondDetailPage from '../pages/bond-detail/BondDetailPage.vue'
import ComparePage from '../pages/compare/ComparePage.vue'
import IndicatorsPage from '../pages/indicators/IndicatorsPage.vue'
import LoginProfilePage from '../pages/member/LoginProfilePage.vue'
import NewsPage from '../pages/news/NewsPage.vue'
import DictionaryPage from '../pages/dictionary/DictionaryPage.vue'
import GuidePage from '../pages/guide/GuidePage.vue'

const routes = [
  { path: '/', name: 'home', component: HomePage, meta: { page: 'home' } },
  { path: '/market', name: 'market', component: MarketPage, meta: { page: 'market' } },
  { path: '/detail', name: 'detail', component: BondDetailPage, meta: { page: 'detail' } },
  { path: '/compare', name: 'compare', component: ComparePage, meta: { page: 'compare' } },
  {
    path: '/indicators/:indicatorId?',
    name: 'indicators',
    component: IndicatorsPage,
    meta: { page: 'indicators' },
  },
  { path: '/profile', name: 'profile', component: LoginProfilePage, meta: { page: 'profile' } },
  { path: '/news', name: 'news', component: NewsPage, meta: { page: 'news' } },
  { path: '/dictionary', name: 'dictionary', component: DictionaryPage, meta: { page: 'dictionary' } },
  { path: '/guide/:subPage?', name: 'guide', component: GuidePage, meta: { page: 'guide' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
