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
  display: flex;
  flex-direction: row;
  width: var(--full-width, 100dvw);
  height: var(--full-height, 100dvh);
  position: relative;
  background-color: var(--bg-color);
}

.main-content-area {
  flex-grow: 1; /* all available space */
  height: var(--full-height, 100dvh);
  position: relative;
  overflow: hidden; /* contains the pages */
}
</style>