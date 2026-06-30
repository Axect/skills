<template>
  <div class="deck-topbar" />
  <!-- Persistent corner mark on content slides only. global-top renders OUTSIDE
       .slidev-layout, so a CSS `.is-cover .deck-logos` descendant rule cannot reach
       it; gate on the layout name instead (cover + section carry their own marks). -->
  <div
    v-if="$slidev.nav.currentLayout !== 'cover' && $slidev.nav.currentLayout !== 'section'"
    class="deck-logos"
  >
    <img src="/logo-fudan.svg" alt="Fudan University" />
    <img src="/logo-riken.png" alt="RIKEN" />
  </div>
</template>
