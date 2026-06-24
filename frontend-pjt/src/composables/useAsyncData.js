import { onMounted, ref } from 'vue'

export function useAsyncData(loader, options = {}) {
  const data = ref(options.initialData ?? null)
  const isLoading = ref(Boolean(options.immediate ?? true))
  const error = ref(null)

  async function execute() {
    isLoading.value = true
    error.value = null

    try {
      data.value = await loader()
    } catch (err) {
      error.value = err
    } finally {
      isLoading.value = false
    }
  }

  if (options.immediate ?? true) {
    onMounted(execute)
  }

  return {
    data,
    isLoading,
    error,
    execute,
  }
}
