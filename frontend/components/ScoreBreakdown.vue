<template>
  <div class="rounded-xl border border-zinc-800 bg-zinc-800/50 p-5 space-y-4">
    <h3 class="text-lg font-semibold text-zinc-100">
      Détail des signaux
    </h3>

    <ScoreBar
      v-for="signal in signals"
      :key="signal.key"
      :score="signal.value"
      :label="signal.label"
    />
  </div>
</template>

<script setup lang="ts">
import type { ScoreBreakdown as ScoreBreakdownType } from '~/composables/useAnalysis'

const props = defineProps<{
  scores: ScoreBreakdownType
}>()

const signals = computed(() => [
  { key: 'ai_content', label: 'Contenu IA', value: props.scores.ai_content_score },
  { key: 'behavioral', label: 'Comportement', value: props.scores.behavioral_score },
  { key: 'sentiment', label: 'Sentiment', value: props.scores.sentiment_score },
  { key: 'opportunism', label: 'Opportunisme', value: props.scores.opportunism_score },
])
</script>
