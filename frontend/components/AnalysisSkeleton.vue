<template>
  <div class="space-y-6 animate-pulse">
    <!-- Profile card skeleton -->
    <div class="rounded-xl border border-zinc-800 bg-zinc-800/50 p-5">
      <div class="flex items-center gap-4">
        <div class="w-14 h-14 rounded-full bg-zinc-700" />
        <div class="space-y-2">
          <div class="h-5 w-32 bg-zinc-700 rounded" />
          <div class="h-4 w-24 bg-zinc-700 rounded" />
        </div>
      </div>
      <div class="mt-4 flex gap-6">
        <div class="h-4 w-20 bg-zinc-700 rounded" />
        <div class="h-4 w-20 bg-zinc-700 rounded" />
        <div class="h-4 w-20 bg-zinc-700 rounded" />
      </div>
    </div>

    <!-- Composite score skeleton -->
    <div class="rounded-xl border border-zinc-800 bg-zinc-800/50 p-5 space-y-3">
      <div class="h-6 w-48 bg-zinc-700 rounded" />
      <div class="h-3 w-full bg-zinc-700 rounded-full" />
    </div>

    <!-- Score breakdown skeleton -->
    <div class="rounded-xl border border-zinc-800 bg-zinc-800/50 p-5 space-y-4">
      <div class="h-5 w-40 bg-zinc-700 rounded" />
      <div v-for="i in 5" :key="i" class="space-y-1">
        <div class="flex justify-between">
          <div class="h-3 w-24 bg-zinc-700 rounded" />
          <div class="h-3 w-12 bg-zinc-700 rounded" />
        </div>
        <div class="h-2 w-full bg-zinc-700 rounded-full" />
      </div>
    </div>
  </div>
</template>
