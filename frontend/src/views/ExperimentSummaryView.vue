<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getExperimentSummary, getHistory, uploadUrl } from '../api.js'
import { t, translateConclusion, lang } from '../i18n/useLanguage'

const router = useRouter()

const loading = ref(true)
const error = ref('')
const data = ref(null)
const history = ref([])
const hovered = ref(null)
const showAll = ref(false)

const TYPE_COLORS = {
  baseline: '#98a2b3',
  single_variable: '#f59e0b',
  repeatability: '#3b82f6',
  system_optimization: '#8b5cf6',
  manual_comparison: '#98a2b3',
}

const metrics = computed(() => data.value?.metrics || {})
const timeline = computed(() => data.value?.timeline || [])
const candidate = computed(() => data.value?.candidate_parameters || null)
const conclusions = computed(() => data.value?.conclusions || [])
const insights = computed(() => data.value?.insights || [])

const closedLoop = computed(() => timeline.value.find((t) => t.type === 'system_optimization'))

const verifiedRecord = computed(() => history.value.find((i) => i.verified === true))
const baselineRecord = computed(() =>
  history.value.find(
    (i) => i.data_source === 'real' && (i.notes || '').trim().startsWith('REAL-001'),
  ) ||
  history.value.find(
    (i) => i.data_source === 'real' && (i.notes || '').includes('REAL-001'),
  ),
)
const beforeImage = computed(() =>
  uploadUrl(baselineRecord.value?.image_path || verifiedRecord.value?.image_path),
)
const afterImage = computed(() => uploadUrl(verifiedRecord.value?.result_image_path))

const chart = computed(() => {
  const items = timeline.value.filter((t) => t.quality_score != null)
  if (!items.length) return null

  const W = 900
  const H = 340
  const padL = 48
  const padR = 32
  const padT = 32
  const padB = 64
  const n = items.length

  const scores = items.map((t) => Number(t.quality_score))
  let min = Math.min(...scores)
  let max = Math.max(...scores)
  min = Math.floor((min - 5) / 5) * 5
  max = Math.ceil((max + 5) / 5) * 5
  if (max === min) max = min + 10

  const xAt = (i) => (n === 1 ? (padL + W - padR) / 2 : padL + ((W - padL - padR) * i) / (n - 1))
  const yAt = (v) => padT + (H - padT - padB) * (1 - (v - min) / (max - min))

  const points = items.map((item, i) => ({
    x: xAt(i),
    y: yAt(Number(item.quality_score)),
    score: Number(item.quality_score),
    id: item.experiment_id,
    label: itemLabel(item),
    type: item.type,
    color: TYPE_COLORS[item.type] || '#8a94a3',
    key: item.type === 'system_optimization',
  }))

  const grid = []
  const steps = 4
  for (let k = 0; k <= steps; k += 1) {
    const value = min + ((max - min) * k) / steps
    grid.push({ value: Math.round(value), y: yAt(value) })
  }

  return {
    W,
    H,
    padL,
    padR,
    padB,
    points,
    grid,
    polyline: points.map((p) => `${p.x},${p.y}`).join(' '),
  }
})

const tooltip = computed(() => {
  if (hovered.value === null || !chart.value) return null
  const p = chart.value.points[hovered.value]
  const w = 168
  const h = 52
  const x = Math.min(Math.max(p.x - w / 2, 4), chart.value.W - w - 4)
  const y = p.y - h - 12 < 4 ? p.y + 14 : p.y - h - 12
  return { ...p, x, y, w, h }
})

const onelineText = computed(() =>
  t('exp.oneline', {
    baseline: score(metrics.value.baseline_score),
    after: score(closedLoop.value?.quality_after),
    max: score(metrics.value.max_experiment_score),
  }),
)

function typeColor(type) {
  return TYPE_COLORS[type] || '#8a94a3'
}

function typeLabel(type) {
  return t(`type.${type}`)
}

function itemLabel(item) {
  if (item.type === 'system_optimization') return t('type.system_optimization')
  if (item.display_label && item.display_label !== item.type_label) return t('type.exploration')
  return t(`type.${item.type}`)
}

function score(value) {
  if (value === null || value === undefined) return '—'
  const num = Number(value)
  return Number.isNaN(num) ? '—' : String(num)
}

function imageUrl(path) {
  return uploadUrl(path)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [summaryData, historyData] = await Promise.all([
      getExperimentSummary(),
      getHistory(100),
    ])
    data.value = summaryData
    history.value = historyData.items || []
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
    <p v-if="loading" class="muted">加载中……</p>
    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="data">
      <!-- 1. 顶部 -->
      <header class="head">
        <div>
          <span class="eyebrow">{{ t('exp.eyebrow') }}</span>
          <h1 class="section-title">{{ t('exp.title') }}</h1>
          <p class="lead">{{ t('exp.subtitle') }}</p>
        </div>
        <div class="head-tags">
          <span class="badge badge-neutral">
            {{ metrics.experiment_records }} {{ t('exp.experiments') }}
          </span>
          <span class="badge badge-accent">
            {{ metrics.closed_loop_verified }} {{ t('exp.closed') }}
          </span>
        </div>
      </header>

      <!-- 2. 一句话结论 -->
      <section class="oneline surface">
        <p>{{ onelineText }}</p>
      </section>

      <!-- 3. 关键指标 -->
      <section class="metrics">
        <div class="metric">
          <span class="stat-number">{{ score(metrics.baseline_score) }}</span>
          <span class="metric-label">{{ t('exp.metric.baseline') }}</span>
        </div>
        <div class="metric">
          <span class="stat-number">
            <template v-if="closedLoop">
              {{ score(closedLoop.quality_before) }} → {{ score(closedLoop.quality_after) }}
            </template>
            <template v-else>—</template>
          </span>
          <span class="metric-label">{{ t('exp.metric.closed') }}</span>
        </div>
        <div class="metric">
          <span class="stat-number">{{ score(metrics.max_experiment_score) }}</span>
          <span class="metric-label">{{ t('exp.metric.max') }}</span>
        </div>
        <div class="metric">
          <span class="stat-number">{{ metrics.repeatability_count }}</span>
          <span class="metric-label">{{ t('exp.metric.repeat') }}</span>
        </div>
      </section>

      <!-- 4. 质量趋势 -->
      <section class="block">
        <div class="section-head">
          <h2 class="section-title">{{ t('exp.trend') }}</h2>
          <div class="legend">
            <span v-for="t in ['baseline', 'single_variable', 'repeatability', 'system_optimization']" :key="t" class="legend-item">
              <span class="legend-dot" :style="{ background: typeColor(t) }"></span>
              {{ typeLabel(t) }}
            </span>
          </div>
        </div>

        <div v-if="chart" class="chart-wrap">
          <svg :viewBox="`0 0 ${chart.W} ${chart.H}`" class="chart">
            <line
              v-for="g in chart.grid"
              :key="'g' + g.value"
              :x1="chart.padL"
              :x2="chart.W - chart.padR"
              :y1="g.y"
              :y2="g.y"
              class="grid-line"
            />
            <text
              v-for="g in chart.grid"
              :key="'t' + g.value"
              :x="chart.padL - 10"
              :y="g.y + 4"
              class="axis-text"
              text-anchor="end"
            >
              {{ g.value }}
            </text>

            <polyline :points="chart.polyline" class="trend-line" />

            <g v-for="(p, i) in chart.points" :key="p.id">
              <circle :cx="p.x" :cy="p.y" :r="p.key ? 7 : 5" :fill="p.color" />
              <text :x="p.x" :y="p.y - 12" class="point-score" text-anchor="middle">
                {{ p.score }}
              </text>
              <text
                :x="p.x"
                :y="chart.H - chart.padB + 22"
                class="axis-text"
                text-anchor="middle"
              >
                {{ p.id }}
              </text>
              <text
                :x="p.x"
                :y="chart.H - chart.padB + 40"
                class="axis-label"
                text-anchor="middle"
              >
                {{ p.label }}
              </text>
              <circle
                :cx="p.x"
                :cy="p.y"
                r="16"
                fill="transparent"
                @mouseenter="hovered = i"
                @mouseleave="hovered = null"
              />
            </g>

            <g v-if="tooltip" class="tooltip">
              <rect :x="tooltip.x" :y="tooltip.y" :width="tooltip.w" :height="tooltip.h" rx="10" />
              <text :x="tooltip.x + 12" :y="tooltip.y + 21" class="tip-title">
                {{ tooltip.id }}
              </text>
              <text :x="tooltip.x + 12" :y="tooltip.y + 40" class="tip-sub">
                {{ tooltip.label }} · {{ tooltip.score }}
              </text>
            </g>
          </svg>
        </div>
      </section>

      <!-- 5. 实验演化故事 -->
      <section class="block">
        <div class="section-head">
          <h2 class="section-title">{{ t('exp.story') }}</h2>
        </div>
        <ol class="story">
          <li
            v-for="item in timeline"
            :key="item.experiment_id"
            class="story-item"
            :class="{ 'story-key': item.type === 'system_optimization' }"
          >
            <span class="story-id">{{ item.experiment_id }}</span>
            <span class="story-label">{{ itemLabel(item) }}</span>
            <span class="story-score">{{ score(item.quality_score) }}</span>
          </li>
        </ol>
        <button class="btn" type="button" @click="showAll = !showAll">
          {{ showAll ? t('exp.hideall') : t('exp.showall') }}
        </button>
        <div v-if="showAll" class="all-table surface">
          <div v-for="item in timeline" :key="'row' + item.experiment_id" class="all-row">
            <span class="all-id">{{ item.experiment_id }}</span>
            <span class="all-type" :style="{ color: typeColor(item.type) }">
              {{ itemLabel(item) }}
            </span>
            <span class="all-score">{{ score(item.quality_score) }}</span>
            <img
              v-if="item.result_image_path"
              class="all-thumb"
              :src="imageUrl(item.result_image_path)"
              :alt="item.experiment_id"
            />
          </div>
        </div>
      </section>

      <!-- 6. Before / After -->
      <section class="block">
        <div class="section-head">
          <h2 class="section-title">{{ t('exp.ba') }}</h2>
        </div>
        <div class="ba">
          <figure class="ba-figure">
            <div class="ba-image">
              <img v-if="beforeImage" class="fade-in" :src="beforeImage" alt="闭环前" />
              <div v-else class="ba-placeholder">闭环前</div>
            </div>
            <figcaption>
              <span class="badge badge-neutral">{{ t('exp.ba.baseline') }}</span>
              <span class="ba-score">{{ score(metrics.baseline_score) }}</span>
            </figcaption>
          </figure>
          <div class="ba-mid">
            <span class="ba-arrow">→</span>
            <span v-if="closedLoop" class="ba-gain">
              +{{ Math.round((closedLoop.quality_after - closedLoop.quality_before) * 10) / 10 }}
            </span>
          </div>
          <figure class="ba-figure">
            <div class="ba-image">
              <img v-if="afterImage" class="fade-in" :src="afterImage" alt="闭环后" />
              <div v-else class="ba-placeholder">闭环后</div>
            </div>
            <figcaption>
              <span class="badge badge-accent">{{ t('exp.ba.closed') }}</span>
              <span class="ba-score">{{ score(closedLoop?.quality_after) }}</span>
            </figcaption>
          </figure>
        </div>
      </section>

      <!-- 7. 当前候选参数 -->
      <section v-if="candidate" class="block">
        <div class="section-head">
          <h2 class="section-title">{{ t('exp.candidate') }}</h2>
        </div>
        <div class="candidate surface">
          <div class="cand-item">
            <span class="cand-k">{{ t('exp.cand.printer') }}</span><span class="cand-v">{{ candidate.printer }}</span>
          </div>
          <div class="cand-item">
            <span class="cand-k">{{ t('exp.cand.material') }}</span>
            <span class="cand-v">{{ candidate.material_variant || candidate.material }}</span>
          </div>
          <div class="cand-item">
            <span class="cand-k">{{ t('exp.cand.color') }}</span><span class="cand-v">{{ candidate.color || '—' }}</span>
          </div>
          <div class="cand-item">
            <span class="cand-k">{{ t('exp.cand.nozzle') }}</span>
            <span class="cand-v">{{ score(candidate.nozzle_temp) }} ℃</span>
          </div>
          <div class="cand-item">
            <span class="cand-k">{{ t('exp.cand.bed') }}</span>
            <span class="cand-v">{{ score(candidate.bed_temp) }} ℃</span>
          </div>
          <div class="cand-item">
            <span class="cand-k">{{ t('exp.cand.speed') }}</span>
            <span class="cand-v">{{ score(candidate.print_speed) }} mm/s</span>
          </div>
          <div class="cand-item">
            <span class="cand-k">{{ t('exp.cand.fan') }}</span>
            <span class="cand-v">
              <template v-if="candidate.fan_speed_range">
                {{ score(candidate.fan_speed_range[0]) }}–{{ score(candidate.fan_speed_range[1]) }} %
              </template>
              <template v-else>—</template>
            </span>
          </div>
          <div class="cand-item">
            <span class="cand-k">{{ t('exp.cand.layer') }}</span>
            <span class="cand-v">{{ score(candidate.layer_height) }} mm</span>
          </div>
          <div class="cand-item">
            <span class="cand-k">{{ t('exp.cand.retraction') }}</span>
            <span class="cand-v">{{ score(candidate.retraction) }} mm</span>
          </div>
        </div>
      </section>

      <!-- 8. 实验结论与限制 -->
      <section class="block">
        <div class="section-head">
          <h2 class="section-title">{{ t('exp.conclusions') }}</h2>
        </div>
        <ol class="conclusions">
          <li v-for="(text, i) in conclusions" :key="i">{{ translateConclusion(text, lang) }}</li>
        </ol>
      </section>

      <section class="block">
        <div class="section-head">
          <h2 class="section-title">{{ t('exp.limits') }}</h2>
        </div>
        <p class="limitations">{{ t('exp.limits.text') }}</p>
      </section>
    </template>
  </main>
</template>

<style scoped>
.page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 3rem 2rem 5rem;
  display: flex;
  flex-direction: column;
  gap: 3.5rem;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.head .lead {
  margin: 0.5rem 0 0;
}

.head-tags {
  display: flex;
  gap: 0.5rem;
}

.oneline {
  padding: 1.25rem 1.5rem;
}

.oneline p {
  margin: 0;
  color: var(--text-2);
}

.oneline b {
  color: var(--text);
}

.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.metric-label {
  font-size: 0.9rem;
  color: var(--text-2);
}

.block {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.legend {
  display: flex;
  gap: 1rem;
  font-size: 0.82rem;
  color: var(--text-3);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.legend-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.chart-wrap {
  width: 100%;
}

.chart {
  width: 100%;
  height: auto;
  overflow: visible;
}

.grid-line {
  stroke: var(--border);
  stroke-width: 1;
}

.axis-text {
  font-size: 12px;
  fill: var(--text-3);
}

.axis-label {
  font-size: 11px;
  fill: var(--text-3);
}

.trend-line {
  fill: none;
  stroke: var(--accent);
  stroke-width: 2.5;
}

.point-score {
  font-size: 12px;
  font-weight: 700;
  fill: var(--text);
}

.tooltip rect {
  fill: rgba(17, 19, 24, 0.86);
}

.tip-title {
  fill: #fff;
  font-size: 12px;
  font-weight: 700;
}

.tip-sub {
  fill: rgba(255, 255, 255, 0.78);
  font-size: 11px;
}

/* story */
.story {
  list-style: none;
  margin: 0;
  padding: 0;
}

.story-item {
  display: grid;
  grid-template-columns: 130px 1fr 90px;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 0;
  border-bottom: 1px solid var(--border);
}

.story-item:last-child {
  border-bottom: none;
}

.story-id {
  font-weight: 700;
}

.story-label {
  color: var(--text-2);
  font-size: 0.92rem;
}

.story-score {
  text-align: right;
  font-weight: 700;
}

.story-key {
  background: var(--accent-soft);
  border-radius: var(--radius-sm);
  padding-left: 0.9rem;
  padding-right: 0.9rem;
}

.story-key .story-score {
  color: var(--accent-strong);
}

.all-table {
  padding: 0.5rem 1rem;
}

.all-row {
  display: grid;
  grid-template-columns: 110px 1fr 70px 72px;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
}

.all-row:last-child {
  border-bottom: none;
}

.all-id {
  font-weight: 600;
}

.all-type {
  font-size: 0.88rem;
}

.all-score {
  text-align: right;
  font-weight: 700;
}

.all-thumb {
  width: 64px;
  height: 46px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid var(--border);
}

/* before / after */
.ba {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1.5rem;
  align-items: center;
}

.ba-figure {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.ba-image {
  border-radius: var(--radius-xl);
  overflow: hidden;
  border: 1px solid var(--border);
  background: #f0f1f4;
  transition: transform 0.28s var(--ease);
}

.ba-image:hover {
  transform: scale(1.01);
}

.ba-image img {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
}

.ba-placeholder {
  aspect-ratio: 4 / 3;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-3);
}

.ba-figure figcaption {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.ba-score {
  margin-left: auto;
  font-size: 1.4rem;
  font-weight: 700;
}

.ba-mid {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
}

.ba-arrow {
  font-size: 1.6rem;
  color: var(--text-3);
}

.ba-gain {
  font-weight: 700;
  color: var(--success);
}

/* candidate */
.candidate {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem 2rem;
  padding: 1.75rem;
}

.cand-item {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.6rem;
}

.cand-k {
  color: var(--text-3);
  font-size: 0.88rem;
}

.cand-v {
  font-weight: 600;
}

.conclusions {
  margin: 0;
  padding-left: 1.2rem;
  line-height: 2;
  color: var(--text-2);
}

.limitations {
  margin: 0;
  color: var(--text-2);
  max-width: 60rem;
  line-height: 1.8;
}

.error {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  background: var(--danger-soft);
  color: var(--danger);
}

@media (max-width: 960px) {
  .page {
    gap: 2.5rem;
  }
  .metrics {
    grid-template-columns: repeat(2, 1fr);
  }
  .ba {
    grid-template-columns: 1fr;
  }
  .ba-mid {
    flex-direction: row;
    justify-content: center;
  }
  .candidate {
    grid-template-columns: 1fr;
  }
}
</style>
