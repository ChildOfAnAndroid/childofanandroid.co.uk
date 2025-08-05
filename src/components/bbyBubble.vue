<template>
  <button @click="say('test bubble')">+ Add Test Bubble</button>

  <TransitionGroup tag="div" class="bubble-container" name="bubble-list" appear>
    <div
      v-for="bubble in bbyState.bubbles"
      :key="bubble.id"
      class="speech-bubble"
      :data-bubble-id="bubble.id"
    >
      <span v-html="bubble.text"></span>
    </div>
  </TransitionGroup>
</template>

<script setup lang="ts">
import { onUpdated, nextTick } from 'vue';
import { bbyUse } from '@/composables/bbyUse.ts';

const { bbyState, say } = bbyUse();

onUpdated(async () => {
  await nextTick();
  const container = document.querySelector('.bubble-container');
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
});
</script>

<style scoped>
.bubble-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 1rem 0;
  gap: 0.75rem;
  overflow-y: auto;
  scroll-behavior: smooth;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.bubble-container::-webkit-scrollbar {
  display: none;
}

.bubble-list-move {
  transition: transform 0.4s cubic-bezier(0.55, 0, 0.1, 1);
}

.bubble-list-enter-active {
  animation: bubbleFadeUp 0.5s ease-out;
}
@keyframes bubbleFadeUp {
  0% {
    transform: translateY(30px);
    opacity: 0;
  }
  100% {
    transform: translateY(0);
    opacity: 0.8;
  }
}

</style>
