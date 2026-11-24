<template>
  <div class="hero">
    <img src="/logo.png">
    <div class="card" @click="open">Open card</div>
    <button aria-label="Disabled" @click="$router.push('/x')"><h5>Heading in button</h5></button>
    <input placeholder="Search our website">
    <a href="#" @click.prevent="toggle">Menu</a>
    <a href="https://example.org" target="_blank">External</a>
    <span tabindex="2">Odd order</span>
    <span class="visually-hidden">Click me</span>
    <span data-bs-toggle="tooltip" tabindex="0">Term</span>
  </div>
</template>
<script>
import { Tooltip } from 'bootstrap'
export default { mounted() { new Tooltip(this.$el) } }
</script>
<style scoped>
.hero { height: 600px; overflow: hidden; transition: all .3s; }
.pill { word-break: break-word; }
.sticky-filters { position: sticky; top: 80px; }
button:focus { outline: none; }
body :focus-visible { outline: 4px solid #ffd800 !important; }
</style>
