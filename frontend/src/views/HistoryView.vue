<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getHistory } from '../api.js'
import { defectText, severityText, t } from '../i18n/useLanguage'

const router = useRouter()

const loading = ref(true)
const error = ref('')
const items = ref([])
const stats = ref({ total: 0, verified: 0 })
const filter = ref('all')

function sourceLabel(source) {
  if (source === 'simulated') return t('hist.source.simulated')
  if (source === 'external') return t('hist.source.external')
  return t('hist.source.real')
}

function sourceClass(source) {
  if (source === 'simulated') return 'badge-warning'
  if (source === 'external') return 'badge-purple'
  return 'badge-success'
}

const filters = computed(() => [
  { key: 'all', label: t('hist.filter.all') },
  { key: 'real', label: t('hist.filter.real') },
  { key: 'external', label: t('hist.filter.external') },
  { key: 'simulated', label: t('hist.filter.simulated') },
])

const filtered = computed(() => {
  if (filter.value === 'all') return items.value
  return items.value.filter((i) => i.data_source === filter.value)
})

function formatConfidence(value) {
  const num = Number(value)
  if (value === null || value === undefined || Number.isNaN(num)) return '—'
  return `${Math.min(Math.round(num * 100), 99)}%`
}

function formatTime(value) {
  if (!value) return '—'
  return String(value).replace('T', ' ')
}

function paramSummary(item) {
  const parts = [
    `${item.nozzle_temp ?? '—'}℃`,
    `床 ${item.bed_temp ?? '—'}`,
    `速 ${item.print_speed ?? '—'}`,
    `风 ${item.fan_speed ?? '—'}`,
    `回 ${item.retraction ?? '—'}`,
  ]
  return parts.join(' · ')
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await getHistory(100)
    items.value = data.items || []
    stats.value = data.stats || { total: 0, verified: 0 }
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="page">
    <header class="head">
      <div>
        <span class="eyebrow">History</span>
        <h1 class="section-title">{{ t('hist.title') }}</h1>
        <p class="lead">{{ t('hist.subtitle') }}</p>
      </div>
      <div class="head-stats">
        <span class="badge badge-neutral">{{ stats.total }} {{ t('hist.records') }}</span>
        <span class="badge badge-accent">{{ stats.verified }} {{ t('hist.closed') }}</span>
      </div>
    </header>

    <div class="filters">
      <button
        v-for="f in filters"
        :key="f.key"
        class="filter-chip"
        :class="{ active: filter === f.key }"
        type="button"
        @click="filter = f.key"
      >
        {{ f.label }}
      </button>
    </div>

    <p v-if="loading" class="muted">加载中……</p>
    <p v-if="error" class="error">{{ error }}</p>

    <ul v-if="!loading && !error" class="activity">
      <li
        v-for="item in filtered"
        :key="item.id"
        class="activity-row"
        @click="router.push(`/history/${item.id}`)"
      >
        <div class="act-main">
          <span class="act-time">{{ formatTime(item.created_at) }}</span>
          <span class="act-defect">
            {{ defectText(item.defect) }}
          </span>
          <span class="badge" :class="sourceClass(item.data_source)">
            {{ sourceLabel(item.data_source) }}
          </span>
          <span v-if="item.verified" class="badge badge-purple">{{ t('hist.closed') }}</span>
        </div>
        <div class="act-sub">
          <span class="severity" :data-level="item.severity">
            {{ severityText(item.severity) }}
          </span>
          <span class="dot">·</span>
          <span>{{ formatConfidence(item.confidence) }}</span>
          <span class="dot">·</span>
          <span class="act-params">{{ paramSummary(item) }}</span>
        </div>
        <span class="act-go">{{ t('hist.view') }} →</span>
      </li>
      <li v-if="!filtered.length" class="muted empty">{{ t('hist.empty') }}</li>
    </ul>
  </main>
</template>

<style scoped>
.page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 3rem 2rem 5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.head .lead {
  margin: 0.4rem 0 0;
}

.head-stats {
  display: flex;
  gap: 0.5rem;
}

.filters {
  display: flex;
  gap: 0.4rem;
}

.filter-chip {
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  border: 1px solid var(--border-strong);
  background: var(--surface);
  color: var(--text-2);
  font-size: 0.88rem;
  font-family: inherit;
  cursor: pointer;
  transition:
    background 0.18s var(--ease),
    color 0.18s var(--ease),
    border-color 0.18s var(--ease);
}

.filter-chip:hover {
  color: var(--text);
  border-color: #cfd4dd;
}

.filter-chip.active {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.activity {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--border);
}

.activity-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.4rem 1rem;
  padding: 1.15rem 0.75rem;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.18s var(--ease);
}

.activity-row:hover {
  background: rgba(76, 99, 255, 0.05);
}

.act-main {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  flex-wrap: wrap;
}

.act-time {
  font-variant-numeric: tabular-nums;
  color: var(--text-3);
  font-size: 0.88rem;
}

.act-defect {
  font-weight: 700;
  font-size: 1.05rem;
}

.act-sub {
  grid-column: 1;
  display: flex;
  align-items: center;
  gap: 0.45rem;
  color: var(--text-3);
  font-size: 0.85rem;
}

.severity[data-level='low'] {
  color: var(--success);
}
.severity[data-level='medium'] {
  color: var(--warning);
}
.severity[data-level='high'] {
  color: var(--danger);
}

.dot {
  color: var(--border-strong);
}

.act-params {
  font-variant-numeric: tabular-nums;
}

.act-go {
  grid-row: 1 / span 2;
  align-self: center;
  color: var(--accent-strong);
  font-size: 0.9rem;
  white-space: nowrap;
}

.empty {
  padding: 2rem 0;
  text-align: center;
}

.error {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  background: var(--danger-soft);
  color: var(--danger);
}

@media (max-width: 720px) {
  .activity-row {
    grid-template-columns: 1fr;
  }
  .act-go {
    grid-row: auto;
  }
}
</style>
