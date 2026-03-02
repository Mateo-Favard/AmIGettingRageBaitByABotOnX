<template>
  <div class="app-layout">
    <header class="app-header">
      <nav>
        <NuxtLink to="/" class="app-title">Am I Getting Rage Bait by a Bot on X?</NuxtLink>
      </nav>
    </header>

    <main class="app-main">
      <slot />
    </main>

    <footer class="app-footer">
      <p>
        Open source —
        <a href="https://github.com" target="_blank" rel="noopener noreferrer">GitHub</a>
      </p>
    </footer>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: system-ui, -apple-system, sans-serif;
  color: #1a1a1a;
}

.app-header {
  padding: 1rem 2rem;
  border-bottom: 1px solid #e5e5e5;
}

.app-title {
  font-size: 1.25rem;
  font-weight: 700;
  text-decoration: none;
  color: inherit;
}

.app-main {
  flex: 1;
  padding: 2rem;
  max-width: 960px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  padding: 1rem 2rem;
  text-align: center;
  border-top: 1px solid #e5e5e5;
  font-size: 0.875rem;
  color: #666;
}
</style>
