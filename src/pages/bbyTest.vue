<!-- 
CHARIS CAT // CHILD OF AN ANDROID - 2025 
src/pages/bbyIndex.vue 
-->

<template>
	<!-- padding and boundaries -->
	<div class="page-container">
               <bubbleGraveyard />

		<!-- two column layout -->
		<div class="left-column">
		</div>
		
		<div class="big-bby">
			<div class="bby-stage">
				<bbySprite />
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
/*import { bbyUse } from '@/composables/bbyUse.ts';*/
import bbySprite from '@/components/bbySprite.vue';
import bubbleGraveyard from '@/components/bubbleGraveyard.vue';

/*const { bbyState } = bbyUse();*/

</script>

<style scoped>
/* scoped styles to prevent them from leaking */
.page-container {
	display: flex;
	flex-direction: row;
	width: 100%;
	height: var(--full-height);
	padding: var(--padding);
	box-sizing: border-box;
	position: relative;
}
</style>