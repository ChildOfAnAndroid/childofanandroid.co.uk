<!-- CHARIS CAT // CHILD OF AN ANDROID - 2025 -->
<template>
  <div class="page-container">
    <bubbleGraveyard />
    <div class="book-gallery">
      <div v-for="card in cards" :key="card.factData.id" class="book-card">

        <!-- TITLE -->
        <div class="card-header">
          <h2 class="fact-name">{{ card.factName }}</h2>
        </div>

        <!-- IMAGE + OVERLAYS -->
        <div class="image-wrap">
          <img :src="card.url" :alt="`Image for the fact: ${card.factName}`" />
          <div class="artist-label">{{ card.imageAuthor || 'unknown artist' }}</div>
        </div>

        <!-- VALUE — MAX ALLOWED (between image and fact) -->
        <div class="stats-row between">
          <div class="stat-pill" title="Base Value">
            <span class="pill-label">value</span>
            <span class="pill-value" :title="card.factData.teach_bonus.toLocaleString()">ᛒ {{ formatCompactUK(card.factData.teach_bonus) }}</span>
          </div>
          <div class="stat-pill" title="Total Allowed In World">
            <span class="pill-label">max allowed</span>
            <span class="pill-value" :title="card.factData.num_produced.toLocaleString()">{{ formatCompactUK(card.factData.num_produced) }}</span>
          </div>
        </div>

        <!-- FACT on dark footer + dates -->
        <div class="card-footer">
          <div class="fact-block">
            <p class="fact-value">"{{ card.factData.value }}"</p>
            <p class="byline">~ {{ card.factData.author }}</p>
          </div>
          <div class="dates-footer">
            <span>fact: <strong>{{ formatDate(card.factData.timestamp) }}</strong></span>
            <span>id: <strong>{{ card.factData.id }}</strong></span>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import bubbleGraveyard from '@/components/bubbleGraveyard.vue';
import { bbyUse } from '@/composables/bbyUse.ts';

const { fetchBbyBookGallery } = bbyUse();

interface BookCard {
  url: string;
  imageAuthor?: string;
  factName: string;
  factData: {
    value: string;
    author: string;
    timestamp: number;
    teach_bonus: number;
    num_produced: number;
    id: number;
  };
}
const cards = ref<BookCard[]>([]);

function formatCompactUK(n: number): string {
  if (n === undefined || n === null || !isFinite(n as any)) return '—';
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  const trim = (s: string) => s.replace(/\.0$/, '');
  if (abs < 1_000) return sign + Math.round(abs).toLocaleString();
  if (abs < 1_000_000) return sign + trim((abs / 1_000).toFixed(1)) + 'k';
  if (abs < 1_000_000_000) return sign + trim((abs / 1_000_000).toFixed(1)) + 'm';
  return sign + trim((abs / 1_000_000_000).toFixed(1)) + 'b';
}

function formatDate(ts: number): string {
  if (!ts) return '—';
  try {
    const d = new Date(ts * 1000);
    return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: '2-digit' });
  } catch {
    return '—';
  }
}

/** shrink long titles so they fit on 2 lines without ellipses */
function fitTitlesToTwoLines() {
  const nodes = document.querySelectorAll('.fact-name');
  nodes.forEach((el) => {
    const element = el as HTMLElement;
    const style = getComputedStyle(element);
    const lineHeight = parseFloat(style.lineHeight || '18');
    const maxLines = 2;
    const maxHeight = lineHeight * maxLines;
    element.style.fontSize = ''; // clear previous inline size
    let size = parseFloat(style.fontSize || '16');
    const minSize = 12;
    let guard = 0;
    while (element.scrollHeight > maxHeight && size > minSize && guard < 40) {
      size -= 1;
      element.style.fontSize = size + 'px';
      guard++;
    }
  });
}

onMounted(async () => {
  cards.value = await fetchBbyBookGallery();
  await nextTick();
  fitTitlesToTwoLines();
});
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: var(--full-height);
  padding: var(--padding);
  box-sizing: border-box;
  overflow-y: auto;
}

.book-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--spacing);
}

.book-card {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;   /* keep sections locked in order */
  gap: 2px;                      /* reduced spacing between sections */
  height: 100%;
  padding: var(--padding);
  border: var(--border-width) solid var(--bby-colour-dark);
  border-radius: 6px;
  background: var(--panel-colour);
  box-shadow: var(--box-shadow);
  position: relative;
  overflow: hidden;
}

/* header / title */
.card-header {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2px 6px;              /* tighter */
  min-height: 42px;              /* slightly shorter */
  border-bottom: 1px solid var(--bby-colour-dark); /* lighter divider */
}

.fact-name {
  font-size: var(--font-size);
  color: var(--font-colour);
  margin: 0;
  text-align: center;
  font-weight: bold;
  line-height: 1.15;
  white-space: normal;
  word-break: break-word;
  text-shadow: 0 1px 0 rgba(0,0,0,.35);
}


/* image + overlays */
.image-wrap { position: relative; }
.image-wrap img {
  display: block;  
  margin-top: 0;
  width: 100%;
  aspect-ratio: 1 / 1;
  image-rendering: pixelated;
  border-radius: 4px;
  margin-bottom: 1px;
}

.artist-label {
  position: absolute;
  bottom: 2px;
  right: 2px;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: hsla(0, 0%, 100%, 0.519);
  pointer-events: none;
  /* text outline (no background) for light/dark art) */
  text-shadow:
    1px 0 0 #000,
   -1px 0 0 #000,
    0 1px 0 #000,
    0 -1px 0 #000,
    1px 1px 0 #000,
   -1px -1px 0 #000,
    1px -1px 0 #000,
   -1px 1px 0 #000;
}




/* definition */
/* definition */
.fact-value {
  text-align: center;
  font-size: var(--small-font-size);
  font-style: italic;
  color: #c0c0c0;
  margin: 0 auto;            /* horizontal centering */
  flex-grow: 1;              /* take space so centering works */
  min-height: 3em;
  display: flex;             /* turn the paragraph into a flex box */
  align-items: center;       /* vertical centering */
  justify-content: center;   /* horizontal centering */
}


/* footer */
.card-footer {
  flex: 1;                         /* occupy remaining height so top stays locked */
  display: flex;
  flex-direction: column;
  gap: 6px;                        /* reduced gap */
  background: var(--bby-colour-black);
  padding: 6px;                    /* reduced padding */
  border-radius: calc(var(--border-radius) / 2);
  border-top: 1px solid var(--bby-colour-dark); /* lighter divider */
  min-height: 120px;
  justify-content: space-between;  /* dates at the bottom */
  margin-top: auto;              /* NEW: pushes whole footer down within the card */
}

.fact-block{
  display: flex;
  flex-direction: column;
  justify-content: center;   /* center description vertically within the black area */
  flex-grow: 1;              /* occupy available footer space */
}

.byline {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--font-colour);
  text-align: right;
  opacity: 0.5;              /* semi-transparent author names */
}

.stats-row{
  display:grid;
  grid-template-columns:1fr 1fr; /* equal widths */
  align-items:stretch;           /* equal heights */
  gap:var(--padding);
}
.stats-row.between { margin: 1px 0; }
.stat-pill{
  display:flex;
  flex-direction:column;
  justify-content:center;
  align-items:center;
  background:var(--bby-colour-dark);
  padding:2px 3px;
  border-radius:10px;
  height:32px;              /* reduced height */
}
.pill-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  opacity: 0.85;
  line-height: 1;
  margin-bottom: 4px;
  white-space: nowrap;
}
.pill-value{
  font-size:clamp(0.85rem,1.2vw,1.05rem);
  color:var(--bby-colour-black);
  font-weight:800;
  line-height:1.05;
  text-align:center;
  white-space:nowrap;        /* one line always */
  font-variant-numeric:tabular-nums;
}

.dates-footer {
  font-size: 0.72rem;
  opacity: .85;
  display: flex;
  justify-content: space-between;
  padding: 0 2px;
}
.dates-footer strong { color: var(--font-colour); font-weight: 700; }
</style>