<template>
  <div class="pt-16 sm:pt-24">
    <div class="text-center">
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

    <!-- Mission statement -->
    <div class="mt-16 max-w-2xl mx-auto">
      <div class="rounded-xl border border-zinc-800 bg-zinc-800/50 p-6 space-y-4 text-sm text-zinc-400 leading-relaxed">
        <h2 class="text-base font-semibold text-zinc-200">
          Pourquoi cet outil existe
        </h2>
        <p>
          Les réseaux sociaux sont devenus un terrain de jeu pour des comptes qui
          exploitent la colère, la peur et l'indignation pour générer de l'engagement.
          Ces comptes — bots, fermes à contenus ou influenceurs opportunistes — produisent
          du <strong class="text-zinc-300">rage bait</strong> à échelle industrielle :
          des publications conçues pour provoquer une réaction émotionnelle plutôt que
          pour informer.
        </p>
        <p>
          Ce phénomène n'est pas anodin. La désinformation et la manipulation de
          l'information sont aujourd'hui des enjeux majeurs de
          <strong class="text-zinc-300">santé publique</strong> et de
          <strong class="text-zinc-300">santé mentale</strong>.
          L'exposition répétée à des contenus alarmistes, polarisants ou artificiellement
          générés contribue à l'anxiété, à la radicalisation des opinions et à l'érosion
          de la confiance dans l'information.
        </p>
        <p>
          Cet outil open source analyse les comptes Twitter/X à travers plusieurs signaux
          — détection de contenu IA, patterns comportementaux, analyse de sentiment et
          opportunisme — pour vous aider à
          <strong class="text-zinc-300">prendre du recul</strong> sur ce que vous
          consommez. Ce n'est pas un tribunal, c'est une boussole.
        </p>
      </div>
    </div>
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
