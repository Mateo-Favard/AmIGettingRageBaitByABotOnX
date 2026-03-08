import { ref, computed, reactive, readonly, watch, watchEffect, onMounted, onUnmounted, nextTick } from 'vue'
import { vi } from 'vitest'

// Stub Nuxt auto-imports as globals (components use them without explicit imports)
const globals = {
  ref,
  computed,
  reactive,
  readonly,
  watch,
  watchEffect,
  onMounted,
  onUnmounted,
  nextTick,
  useRuntimeConfig: () => ({
    public: { apiBaseUrl: 'http://localhost:8000' },
  }),
  useRoute: () => ({ params: {} }),
  useHead: () => {},
  navigateTo: vi.fn(),
  definePageMeta: () => {},
}

for (const [key, value] of Object.entries(globals)) {
  vi.stubGlobal(key, value)
}
