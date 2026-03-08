<template>
  <div class="w-full">
    <div v-if="label" class="flex justify-between items-center mb-1">
      <span class="text-sm text-zinc-400">{{ label }}</span>
      <span class="text-sm font-medium" :class="scoreTextColor">
        {{ displayScore }}
      </span>
    </div>
    <div class="w-full bg-zinc-700 rounded-full overflow-hidden" :class="large ? 'h-3' : 'h-2'">
      <div
        class="h-full rounded-full transition-all duration-700 ease-out"
        :class="scoreBarColor"
        :style="{ width: `${clampedScore}%` }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  score: number | null
  label?: string
  large?: boolean
}>(), {
  label: undefined,
  large: false,
})

const clampedScore = computed(() => {
  if (props.score == null) return 0
  return Math.max(0, Math.min(100, props.score))
})

const displayScore = computed(() => {
  if (props.score == null) return 'N/A'
  return `${Math.round(props.score)}/100`
})

const scoreBarColor = computed(() => {
  if (props.score == null) return 'bg-zinc-600'
  if (props.score < 30) return 'bg-green-500'
  if (props.score < 60) return 'bg-yellow-500'
  return 'bg-red-500'
})

const scoreTextColor = computed(() => {
  if (props.score == null) return 'text-zinc-500'
  if (props.score < 30) return 'text-green-500'
  if (props.score < 60) return 'text-yellow-500'
  return 'text-red-500'
})
</script>
