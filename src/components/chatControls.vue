<template>
  <div class="input-group">
    <input
      v-model="message"
      @keyup.enter="handleSend"
      placeholder="type a message..."
      class="text-input"
    />
    <button @click="handleSend" class="action-button" :disabled="!message">send</button>
    <button @click="$emit('fact')" class="action-button">fact</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const emit = defineEmits<{(e: 'send', message: string): void; (e: 'fact'): void;}>();

const message = ref('');

function handleSend() {
  if (!message.value) return;
  emit('send', message.value);
  message.value = '';
}
</script>

<style scoped>
/* uses global input-group styles */
</style>