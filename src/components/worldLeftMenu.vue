<template>
  <div class="world-left">
    <div class="vertical-panel">
      <h1 class="page-title">bbyWorld</h1>
      <h2 v-if="subtitle" class="subtitle">{{ subtitle }}</h2>

      <!-- BOARD SIZE CONTROL -->
      <div class="grp">
        <label class="section" for="board-size">board size</label>
        <div class="row3">
          <button class="action" @click="decBoard">-</button>
          <input id="board-size" type="number" v-model.number="boardSizeModel" :min="boardSizeMin" step="16" />
          <button class="action" @click="incBoard">+</button>
        </div>
        <small style="opacity:.7">changing size clears the world</small>
      </div>

      <!-- WORLD CONTROL -->
      <div class="grp">
        <label class="section">world</label>
        <button class="action" @click="clearWorld">clear</button>
      </div>

      <!-- CARD SELECTION -->
      <div class="grp">
        <label class="section">{{ cardLabel }}</label>
        <div class="card-swatch-bar">
          <button
            v-for="card in cards"
            :key="card.label"
            class="card-swatch"
            :class="{ selected: selectedCardLabel === card.label }"
            @click="selectCard(card.label)"
          >
            <img :src="card.stamp_url || card.url" :alt="card.label" />
          </button>
        </div>
      </div>

      <!-- STATS -->
      <div class="grp">
        <label class="section">stats</label>
        <div class="world-stats">
          <span>
            TIME: {{ elapsedTimeDisplay }}
            <span v-if="aetherState"> | AETHER: <span :style="{color: aetherColor}">{{ aetherState }}</span></span>
          </span>
          <span>
            CELLS: {{ livingCellsCount }}
            <span v-if="avgLifespan !== undefined"> | AVG LIFE: {{ avgLifespan }}</span>
          </span>
          <template v-if="stats">
            <span v-if="stats.spawns !== undefined">SPAWNS: {{ stats.spawns }}</span>
            <span v-if="stats.reproductions !== undefined">REPRODUCTIONS: {{ stats.reproductions }}</span>
            <span v-if="stats.warDeaths !== undefined">WAR: {{ stats.warDeaths }}</span>
            <span v-if="stats.babyMerges !== undefined">BBY: {{ stats.babyMerges }}</span>
            <span v-if="stats.squishDeaths !== undefined">SQUISH: {{ stats.squishDeaths }}</span>
            <span v-if="stats.fadedDeaths !== undefined">FADE: {{ stats.fadedDeaths }}</span>
            <span v-if="stats.conflicts !== undefined">CONFLICT: {{ stats.conflicts }}</span>
            <span v-if="stats.chargeDecays !== undefined">CHARGE DRAIN: {{ stats.chargeDecays }}</span>
            <span v-if="stats.overcrowdDecays !== undefined">OVERCROWD: {{ stats.overcrowdDecays }}</span>
          </template>
        </div>
      </div>

      <!-- GROUP STATS -->
      <div class="grp" v-if="sortedGroupStats && sortedGroupStats.length">
        <label class="section">colour groups</label>
        <div class="group-stats">
          <div class="group-row header">
            <span>colour</span>
            <span v-if="hasGroupField('count')">count</span>
            <span>%</span>
            <span>age</span>
            <span v-if="hasGroupField('avgCharge')">charge</span>
            <span v-if="hasGroupField('avgEnergy')">energy</span>
            <span v-if="hasGroupField('avgMass')">mass</span>
            <span v-if="hasGroupField('avgStrength')">strength</span>
          </div>
          <div
            class="group-row"
            v-for="g in sortedGroupStats"
            :key="g.colour"
            :class="{selected: highlightedGroup === g.colour}"
            @click="selectGroup(g.colour)"
          >
            <div class="group-bar" :style="{ background: g.colour, width: g.percentage + '%' }"></div>
            <span class="colour-cell"><span class="colour-swatch" :style="{ background: g.colour }"></span> {{ g.colour }}</span>
            <span v-if="g.count !== undefined">{{ g.count }}</span>
            <span>{{ g.percentage.toFixed(1) }}%</span>
            <span>{{ formatTicks(g.avgAge) }}</span>
            <span v-if="g.avgCharge !== undefined">{{ g.avgCharge.toFixed(1) }}</span>
            <span v-if="g.avgEnergy !== undefined">{{ g.avgEnergy.toFixed(1) }}</span>
            <span v-if="g.avgMass !== undefined">{{ g.avgMass.toFixed(2) }}</span>
            <span v-if="g.avgStrength !== undefined">{{ g.avgStrength.toFixed(2) }}</span>
          </div>
        </div>
      </div>

      <!-- OPTIONAL GROUP INSIGHT -->
      <div class="grp" v-if="selectedGroupInfo">
        <label class="section">group insight</label>
        <div class="group-insight">
          <span class="colour-swatch" :style="{ background: selectedGroupInfo.colour }"></span>
          <span>{{ selectedGroupInfo.message }}</span>
        </div>
      </div>

      <!-- SLOT FOR EXTRA CONTENT -->
      <slot />

      <!-- SELECTED CELL INFO -->
      <div class="grp" v-if="selectedCell">
        <label class="section">cell {{ selectedCell.id }} info</label>
        <div class="cell-stats">
          <div class="cell-colour">
            <span class="colour-swatch" :style="{ background: `rgba(${selectedCell.r},${selectedCell.g},${selectedCell.b},${selectedCell.a/255})` }"></span>
            <span>{{ selectedCell.r }},{{ selectedCell.g }},{{ selectedCell.b }},{{ selectedCell.a }}</span>
          </div>
          <div>pos: {{ selectedCell.x }}, {{ selectedCell.y }} | age: {{ formatTicks(selectedCell.age) }}<span v-if="selectedCell.lifeStage"> ({{ selectedCell.lifeStage }})</span></div>
          <div v-if="selectedCell.lifespan !== undefined">lifespan: {{ formatTicks(selectedCell.lifespan) }}</div>
          <div v-if="selectedCell.reputation !== undefined">reputation: {{ selectedCell.reputation.toFixed(2) }}<span v-if="selectedCell.isInsane"> (INSANE)</span></div>
          <div v-if="selectedCell.energy !== undefined">energy: {{ selectedCell.energy.toFixed(1) }}</div>
          <div v-if="selectedCell.charge !== undefined">charge: {{ selectedCell.charge.toFixed(1) }}</div>
          <div v-if="selectedCell.aggression !== undefined">aggr: {{ selectedCell.aggression.toFixed(2) }}</div>
          <div v-if="selectedCell.strength !== undefined">strength: {{ selectedCell.strength.toFixed(2) }}</div>
          <div v-if="selectedCell.cargo !== undefined">cargo: {{ selectedCell.cargo.toFixed(1) }}</div>
        </div>
      </div>

      <!-- FAMILY TREE -->
      <div class="grp" v-if="selectedCell">
        <label class="section">cell {{ selectedCell.id }} family</label>
        <div class="family-tree">
          <div>
            Parents:
            <template v-if="selectedFamily && selectedFamily.parents.length">
              <span v-for="p in selectedFamily.parents" :key="p.id" class="family-link" @click="selectCellById(p.id)">#{{ p.id }}</span>
            </template>
            <span v-else>none</span>
          </div>
          <div>
            Children:
            <template v-if="selectedFamily && selectedFamily.children.length">
              <span v-for="c in selectedFamily.children" :key="c.id" class="family-link" @click="selectCellById(c.id)">#{{ c.id }}</span>
            </template>
            <span v-else>none</span>
          </div>
        </div>
      </div>

      <!-- LEGEND -->
      <div v-if="!hideLegend" class="grp">
        <label class="section" :style="hasToggleLegend ? {cursor: 'pointer'} : null" @click="toggleLegend">legend</label>
        <div class="legend" v-show="legendVisible">
          <p><strong>colour:</strong> red wants to be on fire, blue wants to be wet, green wants to grow. transparent things are less strong.</p>
          <p><strong>but:</strong> red burns lots of energy, greens need lots of room, blues pool together but slip off heights.</p>
          <p><strong>bbys:</strong> when two cells make un bby, they're a mixture of their parents. the little flashes on screen are them being born!</p>
          <p><strong>jobs:</strong> cells move toward the resources they need on the board.</p>
          <p><strong>stats:</strong> % shows each colour's share of living cells, age and energy track group averages.</p>
        </div>
      </div>

      <!-- SPEED -->
      <div class="grp">
        <label class="section">speed ({{ ticksPerSecond }} TPS)</label>
        <div class="row2">
          <button class="action" @click="slowDown">-</button>
          <button class="action" @click="speedUp">+</button>
        </div>
      </div>

      <!-- ZOOM -->
      <div class="grp">
        <label class="section">zoom</label>
        <div class="row3">
          <button class="action" @click="zoomOut">-</button>
          <div class="zoom-display">{{ (zoomFactor*100).toFixed(0) }}%</div>
          <button class="action" @click="zoomIn">+</button>
        </div>
        <button class="action" @click="toggleScope" :class="{active: scopeActive}">scope</button>
        <button class="action" @click="resetView">reset view</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { computed, toRefs } from 'vue';
const props = defineProps();
const { ticksPerSecond, zoomFactor, scopeActive, selectedCell, selectedFamily } = toRefs(props);
const boardSizeModel = computed({
  get: () => props.boardSize,
  set: (v:number) => props.setBoardSize && props.setBoardSize(v)
});
const boardSizeMin = props.boardSizeMin ?? 32;
const decBoard = () => props.decBoard && props.decBoard();
const incBoard = () => props.incBoard && props.incBoard();
const clearWorld = () => props.clearWorld && props.clearWorld();
const selectCard = (label:string) => props.selectCard && props.selectCard(label);
const selectGroup = (colour:string) => props.selectGroup && props.selectGroup(colour);
const selectCellById = (id:number) => props.selectCellById && props.selectCellById(id);
const slowDown = () => props.slowDown && props.slowDown();
const speedUp = () => props.speedUp && props.speedUp();
const zoomIn = () => props.zoomIn && props.zoomIn();
const zoomOut = () => props.zoomOut && props.zoomOut();
const toggleScope = () => props.toggleScope && props.toggleScope();
const resetView = () => props.resetView && props.resetView();
const hasToggleLegend = computed(() => !!props.toggleLegend);
const toggleLegend = () => props.toggleLegend && props.toggleLegend();
const livingCellsCount = computed(() => {
  if (!props.livingCells) return 0;
  if (typeof props.livingCells.filter === 'function') {
    return props.livingCells.filter((c:any) => c.alive ?? true).length;
  }
  return props.livingCells.length || 0;
});
const legendVisible = computed(() => props.showLegend === undefined ? true : props.showLegend);
const cardLabel = props.cardLabel || 'select a cell stamp:';
const hasGroupField = (key:string) => props.sortedGroupStats && props.sortedGroupStats.length && props.sortedGroupStats[0][key] !== undefined;
const subtitle = props.subtitle;
const hideLegend = props.hideLegend;
</script>

<style scoped>
.world-left{flex:1 1 320px;min-width:280px;height:100%;display:flex;flex-direction:column}
.vertical-panel{position:relative;width:100%;height:100%;overflow-y:auto;padding:var(--padding);background:var(--panel-colour);border:var(--border);border-radius:var(--border-radius);box-shadow:var(--box-shadow);display:flex;flex-direction:column;gap:calc(var(--spacing)*1.1)}
.world-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.subtitle{text-align:center;font-size:1rem;margin:0 0 0.5rem 0}
.group-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.group-row{display:grid;grid-template-columns:2fr 1fr 1fr 1.5fr 1fr 1fr;gap:.25rem;position:relative;cursor:pointer;align-items:center}
.group-row.header{font-weight:700;cursor:default}
.group-row.selected{outline:1px solid var(--accent-colour)}
.group-bar{position:absolute;top:0;left:0;bottom:0;opacity:.2;pointer-events:none}
.colour-cell{display:flex;align-items:center;gap:.25rem}
.colour-swatch{width:1rem;height:1rem;border:var(--border);border-radius:2px;flex-shrink:0}
.grp{display:flex;flex-direction:column;gap:.5rem}
.legend{font-size:var(--small-font-size);display:flex;flex-direction:column;gap:.25rem;line-height:1.2}
.section{font-size:var(--small-font-size);text-align:center;opacity:.85;letter-spacing:.1em;text-transform:uppercase}
.action{display:block;width:100%;padding:.4rem .5rem;transition:all .2s ease-out;text-align:center}
.action.active,.action:active{background:var(--accent-hover);border-color:var(--accent-colour)!important}
.row2{display:grid;grid-template-columns:repeat(2,1fr);gap:.5rem}
.row3{display:grid;grid-template-columns:1fr auto 1fr;gap:.5rem;align-items:center}
.zoom-display{text-align:center;font-size:var(--small-font-size)}
#board-size{width:4rem;text-align:center}
.card-swatch-bar{display:flex;flex-wrap:wrap;gap:.5rem}
.card-swatch{border:var(--border);padding:2px;background:var(--panel-colour);cursor:pointer}
.card-swatch img{width:32px;height:32px;image-rendering:pixelated;display:block}
.card-swatch.selected{border-color:var(--accent-colour);background:var(--accent-hover)}
.cell-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.cell-colour{display:flex;align-items:center;gap:.25rem}
.family-tree{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.family-link{cursor:pointer;margin-right:.25rem;color:var(--accent-colour)}
.family-link:hover{text-decoration:underline}
.group-insight{display:flex;align-items:center;gap:.25rem;font-size:var(--small-font-size)}
</style>
