<script setup>
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import GlobalNav from './components/gnb/GlobalNav.vue'
import { useNavigation } from './composables/useNavigation'
import { useAppStore } from './stores/app'

const route = useRoute()
const appStore = useAppStore()
const { navigate } = useNavigation()

const currentPage = computed(() => route.meta.page || 'home')
const currentSubPage = computed(() => route.params.subPage || 'what')
const selectedIndicatorId = computed(() => route.params.indicatorId || appStore.selectedIndicatorId)

watch(selectedIndicatorId, (indicatorId) => {
  if (currentPage.value === 'indicators') {
    appStore.setIndicator(indicatorId)
  }
}, { immediate: true })
</script>

<template>
  <div class="app-shell">
    <GlobalNav :active-page="currentPage" @navigate="navigate" />
    <main>
      <RouterView v-slot="{ Component }">
        <component
          :is="Component"
          :selected-indicator-id="selectedIndicatorId"
          :market-search="appStore.marketSearch"
          :compare-bonds="appStore.compareBonds"
          :is-logged-in="appStore.isLoggedIn"
          :user="appStore.user"
          :current-sub-page="currentSubPage"
          @navigate="navigate"
          @login="appStore.login"
          @logout="appStore.logout"
        />
      </RouterView>
    </main>
  </div>
</template>
