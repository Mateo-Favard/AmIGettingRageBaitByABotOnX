<template>
  <div class="analysis-page">
    <p v-if="!handle">Handle invalide.</p>
    <p v-else>Analyse du compte <strong>@{{ handle }}</strong> — à implémenter (Phase 4).</p>
    <NuxtLink to="/">Retour</NuxtLink>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const handle = computed(() => route.params.handle as string)
</script>
