<template>
  <div class="home">
    <h1>Analysez un compte Twitter/X</h1>
    <p class="subtitle">
      Évaluez la probabilité qu'un compte soit un compte opportuniste de rage bait.
    </p>

    <form class="analyze-form" @submit.prevent="onSubmit">
      <input
        v-model="url"
        type="text"
        placeholder="Collez un lien Twitter/X (ex: https://x.com/username)"
        class="url-input"
        :disabled="loading"
      />
      <button type="submit" class="analyze-btn" :disabled="loading || !isValidUrl">
        {{ loading ? 'Analyse en cours...' : 'Analyser' }}
      </button>
    </form>

    <p v-if="error" class="error-message">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
const url = ref('')
const loading = ref(false)
const error = ref('')

const TWITTER_URL_REGEX = /^https?:\/\/(twitter\.com|x\.com)\/([a-zA-Z0-9_]{1,15})\/?$/

const isValidUrl = computed(() => TWITTER_URL_REGEX.test(url.value))

function extractHandle(twitterUrl: string): string | null {
  const match = twitterUrl.match(TWITTER_URL_REGEX)
  return match ? match[2] : null
}

async function onSubmit() {
  if (!isValidUrl.value) return

  const handle = extractHandle(url.value)
  if (!handle) return

  loading.value = true
  error.value = ''

  try {
    const config = useRuntimeConfig()
    const result = await $fetch<{ id: string }>(`${config.public.apiBaseUrl}/api/v1/analyze`, {
      method: 'POST',
      body: { url: url.value },
    })
    await navigateTo(`/analysis/${handle}`)
  } catch (e: any) {
    error.value = e?.data?.error?.message || 'Une erreur est survenue lors de l\'analyse.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home {
  text-align: center;
  padding-top: 4rem;
}

h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  margin-bottom: 2rem;
}

.analyze-form {
  display: flex;
  gap: 0.75rem;
  max-width: 600px;
  margin: 0 auto;
}

.url-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid #e5e5e5;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.url-input:focus {
  outline: none;
  border-color: #333;
}

.analyze-btn {
  padding: 0.75rem 1.5rem;
  background: #1a1a1a;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.analyze-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  color: #dc2626;
  margin-top: 1rem;
}

@media (max-width: 640px) {
  .analyze-form {
    flex-direction: column;
  }
}
</style>
