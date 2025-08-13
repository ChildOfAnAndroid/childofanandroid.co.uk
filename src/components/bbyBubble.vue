<template>
	<button @click="say('test bubble', 'kevinonline420', userColour)">+ add test bubble</button>
        <TransitionGroup tag="div" class="bubble-container" name="bubble-list" appear>
                <bubbleItem
                        v-for="bubble in bbyState.bubbles"
                        :key="bubble.id"
                        :bubble="bubble"
                        @remove="removeBubble"
                />
        </TransitionGroup>
</template>

<script setup lang="ts">
import { onUpdated, nextTick } from 'vue';
import { bbyUse } from '@/composables/bbyUse.ts';
import bubbleItem from '@/components/bubbleItem.vue';

const { bbyState, say, removeBubble, userColour } = bbyUse();

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
	padding: var(--padding, 0.25vmax);
	align-items: var(--font-align);
	gap: var(--spacing, 0.5vmax);
	overflow-y: auto;
	overflow-x: visible;
	scroll-behavior: smooth;
	scrollbar-width: none;
	-ms-overflow-style: none;
}
.bubble-container::-webkit-scrollbar {display: none;}
 
</style>