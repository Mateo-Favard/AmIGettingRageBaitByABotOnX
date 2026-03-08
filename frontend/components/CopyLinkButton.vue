<template>
  <button
    class="flex items-center gap-2 px-4 py-2 text-sm rounded-lg border border-zinc-700
           text-zinc-400 hover:text-zinc-200 hover:border-zinc-600 transition-colors"
    @click="copyLink"
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="w-4 h-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      stroke-width="2"
    >
      <path
        v-if="!copied"
        stroke-linecap="round"
        stroke-linejoin="round"
        d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
      />
      <path
        v-else
        stroke-linecap="round"
        stroke-linejoin="round"
        d="M5 13l4 4L19 7"
      />
    </svg>
    {{ copied ? 'Lien copié !' : 'Copier le lien' }}
  </button>
</template>

<script setup lang="ts">
const copied = ref(false)
let timeout: ReturnType<typeof setTimeout> | null = null

async function copyLink() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    copied.value = true
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => {
      copied.value = false
    }, 2000)
  }
  catch {
    // Clipboard API not available — silently fail
  }
}
</script>
