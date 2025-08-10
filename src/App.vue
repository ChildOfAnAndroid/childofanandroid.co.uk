<!-- 
CHARIS CAT // CHILD OF AN ANDROID - 2025 
src/App.vue 
-->

<template>
  <div id="app-container">
    <!-- PAGE COMPONENTS -->
    <div class="main-content-area">
      <router-view name="main"></router-view>
    </div>

    <!-- NAVIGATION BAR -->
    <router-view name="nav"></router-view>
  </div>
</template>

<style>
#app-container {
  min-width: 0;
  display: flex;
  flex-direction: row;
  width: var(--full-width, 100dvw);
  height: var(--full-height, 100dvh);
  position: relative;
  background-color: var(--bg-color);
  transition: background-color var(--transition-time) ease-in-out;
  transition: border-color var(--transition-time) ease-in-out;
}

.main-content-area {
  min-width: 0;
  flex: 1 1 auto;             /* take remaining space */
  height: var(--full-height);
  position: relative;
}
</style>