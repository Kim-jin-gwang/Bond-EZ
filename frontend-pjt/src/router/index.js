import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../pages/home/HomePage.vue'), meta: { page: 'home' } },
  { path: '/market', name: 'market', component: () => import('../pages/market/MarketPage.vue'), meta: { page: 'market' } },
  { path: '/detail/:bondId?', name: 'detail', component: () => import('../pages/bond-detail/BondDetailPage.vue'), meta: { page: 'detail' } },
  { path: '/compare', name: 'compare', component: () => import('../pages/compare/ComparePage.vue'), meta: { page: 'compare' } },
  {
    path: '/indicators/:indicatorId?',
    name: 'indicators',
    component: () => import('../pages/indicators/IndicatorsPage.vue'),
    meta: { page: 'indicators' },
  },
  { path: '/profile', name: 'profile', component: () => import('../pages/member/LoginProfilePage.vue'), meta: { page: 'profile' } },
  { path: '/news', name: 'news', component: () => import('../pages/news/NewsPage.vue'), meta: { page: 'news' } },
  { path: '/dictionary', name: 'dictionary', component: () => import('../pages/dictionary/DictionaryPage.vue'), meta: { page: 'dictionary' } },
  { path: '/guide/:subPage?', name: 'guide', component: () => import('../pages/guide/GuidePage.vue'), meta: { page: 'guide' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
