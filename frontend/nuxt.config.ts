export default defineNuxtConfig({
  ssr: true,

  devtools: { enabled: false },
  telemetry: false,

  runtimeConfig: {
    // Server-only (never exposed to client)
    apiSecret: '',
    // Public (exposed to client)
    public: {
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
    },
  },

  app: {
    head: {
      title: 'Am I Getting Rage Bait by a Bot on X?',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Analysez un compte Twitter/X et évaluez la probabilité de rage bait opportuniste.' },
      ],
      htmlAttrs: {
        lang: 'fr',
      },
    },
  },

  compatibilityDate: '2025-01-01',
})
