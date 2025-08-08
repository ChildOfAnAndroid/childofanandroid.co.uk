<template>
  <button @click="say('test bubble', 'kevinonline420')">+ add test bubble</button>

  <TransitionGroup tag="div" class="bubble-container" name="bubble-list" appear>
    <div
      v-for="bubble in bbyState.bubbles"
      :key="bubble.id"
      class="speech-bubble"
      :data-bubble-id="bubble.id"
      @click="removeBubble(bubble.id)"
      :data-author="bubble.author"
      :style="{
        'backgroundColor': bubble.bgColor,
        'borderColor': bubble.borderColor,
      }"
    >
      <span v-html="bubble.text"></span>
      <strong class="bubble-author"> {{ bubble.author }}</strong>
    </div>
  </TransitionGroup>
</template>

<script setup lang="ts">
import { onUpdated, nextTick } from 'vue';
import { bbyUse } from '@/composables/bbyUse.ts';

const { bbyState, say, removeBubble } = bbyUse();

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
  padding: var(--padding);
  gap: var(--spacing);
  overflow-y: auto;
  scroll-behavior: smooth;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.bubble-container::-webkit-scrollbar {display: none;}

.bubble-list-move {transition: transform var(--transition-time) cubic-bezier(0.55, 0, 0.1, 1);}

.bubble-list-enter-active {animation: bubbleFadeUp var(--transition-time) ease-out;}

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
