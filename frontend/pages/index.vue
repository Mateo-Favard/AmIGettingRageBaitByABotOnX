<template>
  <div class="text-center pt-16 sm:pt-24">
    <h1 class="text-3xl sm:text-4xl font-bold mb-2">
      Analysez un compte Twitter/X
    </h1>
    <p class="text-zinc-400 mb-8 text-lg">
      Évaluez la probabilité qu'un compte soit un compte opportuniste de rage bait.
    </p>

    <form class="flex flex-col sm:flex-row gap-3 max-w-xl mx-auto" @submit.prevent="onSubmit">
      <input
        v-model="url"
        type="text"
        placeholder="Collez un lien Twitter/X (ex: https://x.com/username)"
        class="flex-1 px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-zinc-100
               placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition-colors"
      >
      <button
        type="submit"
        class="px-6 py-3 bg-zinc-100 text-zinc-900 font-semibold rounded-xl
               hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="!isValidUrl"
      >
        Analyser
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
const url = ref('')

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

  await navigateTo(`/analysis/${handle}`)
}
</script>
