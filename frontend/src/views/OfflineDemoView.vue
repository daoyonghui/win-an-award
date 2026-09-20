<script setup>
import { computed, onMounted, ref } from 'vue'
import { getExperimentSummary, getHistory, uploadUrl } from '../api.js'
import { t } from '../i18n/useLanguage'

const loading = ref(true)
const error = ref('')
const summary = ref(null)
const history = ref([])

const timeline = computed(() => summary.value?.timeline || [])

function item(id) {
  return timeline.value.find((x) => x.experiment_id === id) || null
}

function score(value) {
  if (value === null || value === undefined) return '—'
  const num = Number(value)
  return Number.isNaN(num) ? '—' : String(num)
}

function imageFor(id) {
  const rec = history.value.find((i) => (i.notes || '').includes(id))
  const fromTimeline = item(id)?.result_image_path
  return uploadUrl(fromTimeline || rec?.image_path)
}

const flow = [
  'Baseline',
  'Single-variable experiments',
  'Experience learning',
  'Minimal change',
  'Closed-loop validation',
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [summaryData, historyData] = await Promise.all([
      getExperimentSummary(),
      getHistory(100),
    ])
    summary.value = summaryData
    history.value = historyData.items || []
  } catch (e) {
    error.value = e.message || 'load failed'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="offline">
    <header class="head">
      <span class="eyebrow">Offline</span>
      <h1 class="section-title">{{ t('offline.title') }}</h1>
      <p class="lead">{{ t('offline.subtitle') }}</p>
      <p class="muted small">{{ t('offline.note') }}</p>
    </header>

    <p v-if="loading" class="muted">…</p>
    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="summary">
      <!-- flow -->
      <section class="flow">
        <template v-for="(step, i) in flow" :key="step">
          <span class="flow-step">{{ step }}</span>
          <span v-if="i < flow.length - 1" class="flow-arrow">→</span>
        </template>
      </section>

      <!-- REAL-001 -->
      <section class="card">
        <div class="card-main">
          <span class="badge badge-neutral">Baseline</span>
          <h2 class="card-title">REAL-001</h2>
          <p class="card-sub">stringing · {{ score(item('REAL-001')?.quality_score) }}</p>
        </div>
        <img v-if="imageFor('REAL-001')" class="card-img" :src="imageFor('REAL-001')" alt="REAL-001" />
      </section>

      <!-- REAL-002 / 003 -->
      <div class="two">
        <section class="card small">
          <span class="badge badge-warning">Single-variable</span>
          <h2 class="card-title">REAL-002</h2>
          <p class="card-sub">temp decrease · {{ score(item('REAL-002')?.quality_score) }}</p>
        </section>
        <section class="card small">
          <span class="badge badge-danger">Single-variable</span>
          <h2 class="card-title">REAL-003</h2>
          <p class="card-sub">retraction increase · {{ score(item('REAL-003')?.quality_score) }}</p>
        </section>
      </div>

      <!-- REAL-005 -->
      <section class="card">
        <div class="card-main">
          <span class="badge badge-success">Improvement trend</span>
          <h2 class="card-title">REAL-005</h2>
          <p class="card-sub">cooling increase · {{ score(item('REAL-005')?.quality_score) }}</p>
        </div>
      </section>

      <!-- REAL-006 -->
      <section class="card key">
        <div class="card-main">
          <span class="badge badge-purple">System optimization</span>
          <h2 class="card-title">REAL-006</h2>
          <p class="card-sub">
            {{ score(item('REAL-006')?.quality_before) }} →
            <b>{{ score(item('REAL-006')?.quality_after) }}</b>
            · verified=true
          </p>
          <p class="card-note">{{ t('home.ba.note') }}</p>
        </div>
        <img v-if="imageFor('REAL-006')" class="card-img" :src="imageFor('REAL-006')" alt="REAL-006" />
      </section>
    </template>
  </main>
</template>

<style scoped>
.offline {
  max-width: 960px;
  margin: 0 auto;
  padding: 3.5rem 2rem 5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.head {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.head .lead {
  margin: 0;
}

.small {
  font-size: 0.85rem;
}

.flow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface);
}

.flow-step {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  background: rgba(16, 18, 24, 0.04);
  border-radius: 999px;
  padding: 0.3rem 0.7rem;
}

.flow-arrow {
  color: #d5dae2;
}

.card {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 1.25rem 1.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}

.card.small {
  flex-direction: column;
  align-items: flex-start;
  gap: 0.4rem;
}

.card.key {
  border-color: rgba(139, 92, 246, 0.3);
  background: linear-gradient(180deg, #fbfbff, #f5f6fc);
  box-shadow: var(--shadow-md);
}

.card-main {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  flex: 1;
}

.card-title {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
}

.card-sub {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.card-sub b {
  color: var(--blue-bright);
}

.card-note {
  margin: 0.2rem 0 0;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.card-img {
  width: 140px;
  height: 110px;
  object-fit: cover;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  flex-shrink: 0;
}

.two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

.error {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  background: var(--danger-soft);
  color: var(--danger);
}

@media (max-width: 640px) {
  .two {
    grid-template-columns: 1fr;
  }
  .card {
    flex-direction: column;
    align-items: flex-start;
  }
  .card-img {
    width: 100%;
    height: 180px;
  }
}
</style>
