<template>
  <div class="family-tree">
    <div>
      parents:
      <template v-if="family.parents.length">
        <span
          v-for="p in family.parents"
          :key="p.id"
          class="family-link"
          @click="selectCell(p.id)"
        >#{{ p.id }}</span>
      </template>
      <span v-else>{{ noParentsText }}</span>
    </div>
    <div>
      children:
      <template v-if="family.children.length">
        <span
          v-for="c in family.children"
          :key="c.id"
          class="family-link"
          @click="selectCell(c.id)"
        >#{{ c.id }}</span>
      </template>
      <span v-else>none</span>
    </div>
  </div>
</template>

<script setup lang="ts">
interface CellRef { id: number }
interface Family { parents: CellRef[]; children: CellRef[] }
const { family, selectCell, noParentsText = 'none' } = defineProps<{
  family: Family;
  selectCell: (id: number) => void;
  noParentsText?: string;
}>();
</script>

<style scoped>
.family-tree{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.family-link{cursor:pointer;margin-right:.25rem;color:var(--accent-colour)}
.family-link:hover{text-decoration:underline}
</style>
