<template>
  <div class="w-full">
    <div v-if="label" class="flex justify-between items-center mb-1">
      <div class="flex items-center gap-1.5">
        <span class="text-sm text-zinc-400">{{ label }}</span>
        <div v-if="tooltip" class="relative group">
          <span class="flex items-center justify-center w-4 h-4 rounded-full border border-zinc-600 text-zinc-500 text-[10px] font-bold cursor-default select-none hover:border-zinc-400 hover:text-zinc-300 transition-colors">
            ?
          </span>
          <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-zinc-300 leading-relaxed shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-150 z-10">
            {{ tooltip }}
            <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-zinc-700" />
          </div>
        </div>
      </div>
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
  tooltip?: string
}>(), {
  label: undefined,
  large: false,
  tooltip: undefined,
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
