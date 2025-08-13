<template>
  <transition name="swpop">
    <div v-if="swatchesOpen" class="swatch-drawer">
      <div class="row2x2">
        <button @click="setPickerToBbyColor" :style="bbyButtonStyle">BBY</button>
        <button @click="setPickerToUserColor" :style="userButtonStyle">USER</button>
      </div>
      <div class="swatch-grid">
        <div
          v-for="s in swatches"
          :key="s"
          class="swatch"
          :style="{ backgroundColor: s }"
          @click="setSwatchColor(s)"
        />
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
const {
  swatchesOpen,
  swatches,
  bbyButtonStyle,
  userButtonStyle,
  setPickerToBbyColor,
  setPickerToUserColor,
  setSwatchColor
} = defineProps<{
  swatchesOpen: boolean;
  swatches: string[];
  bbyButtonStyle: Record<string, string>;
  userButtonStyle: Record<string, string>;
  setPickerToBbyColor: () => void;
  setPickerToUserColor: () => void;
  setSwatchColor: (color: string) => void;
}>();
</script>

<style scoped>
.swatch-drawer {
  padding: .4rem;
  border: var(--border);
  border-radius: calc(var(--border-radius)*.8);
  background: var(--panel-colour);
  display: flex;
  flex-direction: column;
  gap: .5rem;
}

.row2x2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: .5rem;
}

.swatch-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: .35rem;
}

.swatch {
  width: 100%;
  aspect-ratio: 1/1;
  border-radius: 50%;
  border: var(--border-width) solid var(--bby-colour-dark);
  cursor: pointer;
}

.swpop-enter-active,
.swpop-leave-active {
  transition: opacity .12s ease, transform .12s ease;
}

.swpop-enter-from,
.swpop-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
