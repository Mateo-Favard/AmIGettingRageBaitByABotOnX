<template>
  <div class="min-h-screen flex flex-col">
    <header class="border-b border-zinc-800 px-6 py-4">
      <nav>
        <NuxtLink to="/" class="text-xl font-bold text-zinc-100 hover:text-white no-underline transition-colors">
          Am I Getting Rage Bait by a Bot on X?
        </NuxtLink>
      </nav>
    </header>

    <main class="flex-1 px-4 py-8 mx-auto w-full max-w-4xl">
      <slot />
    </main>

    <footer class="border-t border-zinc-800 px-6 py-4 text-center text-sm text-zinc-500">
      <p>
        Open source &mdash;
        <a
          href="https://github.com/Mateo-Favard/AmIGettingRageBaitByABotOnX"
          target="_blank"
          rel="noopener noreferrer"
          class="text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          GitHub
        </a>
        &mdash;
        <NuxtLink
          to="/legal"
          class="text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          Mentions l&eacute;gales
        </NuxtLink>
      </p>
    </footer>
  </div>
</template>
