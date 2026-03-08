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
      :tooltip="signal.tooltip"
    />
  </div>
</template>

<script setup lang="ts">
import type { ScoreBreakdown as ScoreBreakdownType } from '~/composables/useAnalysis'

const props = defineProps<{
  scores: ScoreBreakdownType
}>()

const signals = computed(() => [
  {
    key: 'ai_content',
    label: 'Contenu IA',
    value: props.scores.ai_content_score,
    tooltip: 'Détecte les tweets au style mécanique ou généré — vocabulaire répétitif, formulations stéréotypées, cadence de publication anormale.',
  },
  {
    key: 'behavioral',
    label: 'Comportement',
    value: props.scores.behavioral_score,
    tooltip: 'Analyse les patterns du compte — ratio followers/following suspect, volume de tweets excessif, compte récent avec forte activité.',
  },
  {
    key: 'sentiment',
    label: 'Sentiment',
    value: props.scores.sentiment_score,
    tooltip: 'Mesure la proportion de tweets négatifs ou alarmistes — ton catastrophiste, vocabulaire émotionnel intense, appels à la peur ou à la colère.',
  },
  {
    key: 'opportunism',
    label: 'Opportunisme',
    value: props.scores.opportunism_score,
    tooltip: 'Combine trois signaux : surreprésentation de tweets "problème", sauts thématiques fréquents entre les sujets, et surf systématique sur les tendances du moment.',
  },
])
</script>
