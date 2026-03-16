<template>
  <div>
    <NuxtLink
      to="/"
      class="inline-flex items-center gap-1 text-sm text-zinc-400 hover:text-zinc-200 transition-colors mb-6"
    >
      &larr; Nouvelle analyse
    </NuxtLink>

    <!-- Loading -->
    <AnalysisSkeleton v-if="state.loading" />

    <!-- Error -->
    <div v-else-if="state.error" class="text-center py-16">
      <p class="text-red-500 text-lg mb-4">
        {{ state.error }}
      </p>
      <button
        class="px-6 py-3 bg-zinc-800 text-zinc-200 font-semibold rounded-xl
               hover:bg-zinc-700 transition-colors"
        @click="retry"
      >
        Réessayer
      </button>
    </div>

    <!-- Results -->
    <div v-else-if="state.data" class="space-y-6">
      <ProfileCard :profile="state.data.profile" />

      <!-- Composite score -->
      <div class="rounded-xl border border-zinc-800 bg-zinc-800/50 p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-1.5">
            <h3 class="text-lg font-semibold text-zinc-100">
              Total score
            </h3>
            <div class="relative group">
              <span class="flex items-center justify-center w-4 h-4 rounded-full border border-zinc-600 text-zinc-500 text-[10px] font-bold cursor-default select-none hover:border-zinc-400 hover:text-zinc-300 transition-colors">
                ?
              </span>
              <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-zinc-300 leading-relaxed shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-150 z-10">
                Score composite pondéré calculé à partir des 4 signaux. Plus il est élevé, plus le compte présente des caractéristiques associées au rage bait opportuniste ou au boting.
                <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-zinc-700" />
              </div>
            </div>
          </div>
          <span class="text-2xl font-bold" :class="compositeScoreColor">
            {{ Math.round(state.data.composite_score) }}/100
          </span>
        </div>
        <ScoreBar :score="state.data.composite_score" large />
      </div>

      <ScoreBreakdown :scores="state.data.scores" />

      <!-- Metadata + actions -->
      <div
        class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3
               text-sm text-zinc-500"
      >
        <div class="flex items-center gap-4 flex-wrap">
          <span>Analyse du {{ formatDate(state.data.analyzed_at) }}</span>
          <span
            v-if="state.data.tweets_analyzed"
            class="px-2 py-0.5 rounded text-xs bg-zinc-800 text-zinc-400 border border-zinc-700"
          >
            {{ state.data.tweets_analyzed }} tweets analysés
          </span>
          <span
            v-if="state.data.cached"
            class="px-2 py-0.5 rounded text-xs bg-zinc-800 text-zinc-400 border border-zinc-700"
          >
            résultat en cache
          </span>
        </div>
        <CopyLinkButton />
      </div>
    </div>

    <!-- Invalid handle -->
    <div v-else class="text-center py-16">
      <p class="text-zinc-400">
        Handle invalide.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const handle = computed(() => route.params.handle as string)

const { state, analyzeByHandle } = useAnalysis()

const compositeScoreColor = computed(() => {
  if (!state.data) return 'text-zinc-500'
  const score = state.data.composite_score
  if (score < 30) return 'text-green-500'
  if (score < 60) return 'text-yellow-500'
  return 'text-red-500'
})

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function retry() {
  if (handle.value) {
    await analyzeByHandle(handle.value)
  }
}

useHead({
  title: computed(() =>
    state.data
      ? `@${state.data.handle} - Score: ${Math.round(state.data.composite_score)}/100`
      : `Analyse de @${handle.value}`,
  ),
})

onMounted(async () => {
  if (handle.value) {
    await analyzeByHandle(handle.value)
  }
})
</script>
