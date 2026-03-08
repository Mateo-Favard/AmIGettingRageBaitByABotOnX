export {
  ref,
  computed,
  reactive,
  readonly,
  watch,
  watchEffect,
  onMounted,
  onUnmounted,
  defineComponent,
  nextTick,
} from 'vue'

export function useRuntimeConfig() {
  return {
    public: {
      apiBaseUrl: 'http://localhost:8000',
    },
  }
}

export function useRoute() {
  return { params: {} }
}

export function useHead(_input: unknown) {}
export function navigateTo(_path: string) {}
