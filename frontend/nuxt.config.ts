export default defineNuxtConfig({
  ssr: true,

  devtools: { enabled: false },
  telemetry: false,

  modules: ['@nuxtjs/tailwindcss'],

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    apiInternalUrl: process.env.NUXT_API_INTERNAL_URL || 'http://localhost:8000',
    public: {},
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
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
        },
      ],
    },
  },

  compatibilityDate: '2025-01-01',
})
