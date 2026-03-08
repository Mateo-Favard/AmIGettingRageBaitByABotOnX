<template>
  <div class="rounded-xl border border-zinc-800 bg-zinc-800/50 p-5">
    <div class="flex items-center gap-4">
      <img
        v-if="profile.profile_image_url"
        :src="profile.profile_image_url"
        :alt="`Avatar de @${profile.handle}`"
        referrerpolicy="no-referrer"
        class="w-14 h-14 rounded-full border-2 border-zinc-700"
      >
      <div
        v-else
        class="w-14 h-14 rounded-full bg-zinc-700 flex items-center justify-center text-zinc-400 text-xl font-bold"
      >
        {{ profile.handle.charAt(0).toUpperCase() }}
      </div>

      <div class="min-w-0">
        <h2 class="text-lg font-semibold text-zinc-100 truncate">
          {{ profile.display_name }}
        </h2>
        <p class="text-sm text-zinc-400">
          @{{ profile.handle }}
        </p>
      </div>
    </div>

    <div class="mt-4 flex gap-6 text-sm">
      <div>
        <span class="font-semibold text-zinc-100">{{ formatNumber(profile.followers_count) }}</span>
        <span class="text-zinc-500 ml-1">followers</span>
      </div>
      <div>
        <span class="font-semibold text-zinc-100">{{ formatNumber(profile.following_count) }}</span>
        <span class="text-zinc-500 ml-1">following</span>
      </div>
      <div>
        <span class="font-semibold text-zinc-100">{{ formatNumber(profile.tweets_count) }}</span>
        <span class="text-zinc-500 ml-1">tweets</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ProfileSummary } from '~/composables/useAnalysis'

defineProps<{
  profile: ProfileSummary
}>()

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toString()
}
</script>
