<template>
  <div
    class="speech-bubble"
    :data-bubble-id="bubble.id"
    :data-author="bubble.author"
    :style="{ backgroundColor: bubble.bgColour, borderColor: bubble.borderColour }"
    @click="$emit('remove', bubble.id)"
  >
    <span v-html="bubble.text"></span>
    <strong class="bubble-author">{{ bubble.author }}</strong>
  </div>
</template>

<script setup lang="ts">
interface Bubble {
  id: string;
  text: string;
  author?: string;
  bgColour?: string;
  borderColour?: string;
}

defineProps<{ bubble: Bubble }>();
defineEmits<{ (e: 'remove', id: string): void }>();
</script>

<style scoped>
.bubble-list-move {
  transition: transform var(--transition-time) cubic-bezier(0.55, 0, 0.1, 1);
}

.bubble-list-enter-active {
  animation: bubbleFadeUp var(--transition-time, 0.2s) ease-out;
}

.speech-bubble {
  position: relative;
  max-width: var(--bubble-width);
  padding: var(--padding);
  border: var(--border);
  border-radius: var(--border-radius);
  background-color: var(--bby-colour, rgba(133, 239, 238, 0.9));
  box-shadow: var(--box-shadow);
  word-break: break-word;
  text-align: var(--font-align);
  z-index: var(--bubble-z);
}

.bubble-author {
  display: inline;
  margin-left: var(--spacing, 0.5vmax);
  font-size: var(--small-font-size);
  font-weight: bold;
}

@keyframes bubbleFadeUp {
  0% {
    transform: translateY(var(--nav-width));
    opacity: 0;
  }
  100% {
    transform: translateY(0);
    opacity: 0.8;
  }
}
</style>
