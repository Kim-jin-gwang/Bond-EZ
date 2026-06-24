import { ref, watch } from 'vue'

export function useDebouncedRef(source, delay = 250) {
  const debounced = ref(source.value)
  let timerId = null

  watch(source, (value) => {
    window.clearTimeout(timerId)
    timerId = window.setTimeout(() => {
      debounced.value = value
    }, delay)
  })

  return debounced
}
