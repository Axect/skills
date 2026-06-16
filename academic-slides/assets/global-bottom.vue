<template>
  <footer v-if="$slidev.nav.currentPage > 1" class="deck-footer">
    <span class="dot" />
    <span>{{ $slidev.configs.title }}</span>
    <span class="spacer" />
    <span>{{ $slidev.nav.currentPage }} / {{ $slidev.nav.total }}</span>
  </footer>
</template>
