<template>
	<button @click="say('test bubble', 'kevinonline420', userColour)">+ add test bubble</button>

	<TransitionGroup tag="div" class="bubble-container" name="bubble-list" appear>
		<div
			v-for="bubble in bbyState.bubbles"
			:key="bubble.id"
			class="speech-bubble"
			:data-bubble-id="bubble.id"
			@click="removeBubble(bubble.id)"
			:data-author="bubble.author"
			:style="{
				'backgroundColor': bubble.bgColour,
				'borderColor': bubble.borderColour,
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

.bubble-list-move {transition: transform var(--transition-time) cubic-bezier(0.55, 0, 0.1, 1);}

.bubble-list-enter-active {animation: bubbleFadeUp var(--transition-time, 0.2s) ease-out;}

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