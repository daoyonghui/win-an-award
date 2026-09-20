<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getExperimentSummary, getHistory, uploadUrl } from '../api.js'
import { t } from '../i18n/useLanguage'
import { demoMode } from '../settings'

const router = useRouter()

const summary = ref(null)
const history = ref([])
const loading = ref(true)
const loadError = ref('')

// 精品展示图：将图片放入 frontend/src/assets/showcase/ 即自动加载
const showcaseModules = import.meta.glob('../assets/showcase/*.{jpg,jpeg,png,webp}', {
  eager: true,
  import: 'default',
})

const showcase = computed(() => {
  const entries = Object.entries(showcaseModules)
  const order = ['showcase-hero', 'showcase-2', 'showcase-3']
  const picked = []
  for (const name of order) {
    const found = entries.find(([path]) => path.includes(name))
    if (found) picked.push(found[1])
  }
  if (!picked.length) entries.forEach(([, url]) => picked.push(url))
  return picked
})

const heroShowcase = computed(() => showcase.value[0] || null)

const closedLoop = computed(() =>
  (summary.value?.timeline || []).find((item) => item.type === 'system_optimization'),
)
const baseline = computed(() =>
  (summary.value?.timeline || []).find((item) => item.type === 'baseline'),
)

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

function score(value) {
  if (value === null || value === undefined) return '—'
  const num = Number(value)
  return Number.isNaN(num) ? '—' : String(num)
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [summaryData, historyData] = await Promise.all([
      getExperimentSummary(),
      getHistory(100),
    ])
    summary.value = summaryData
    history.value = historyData.items || []
  } catch (e) {
    loadError.value = e.message || 'load failed'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="home">
    <div v-if="demoMode" class="demo-bar">
      <span class="demo-badge">{{ t('demo.badge') }}</span>
      <router-link class="demo-link" to="/demo-offline">
        {{ t('nav.demoOffline') }} →
      </router-link>
    </div>

    <!-- Hero -->
    <section class="hero">
      <div class="hero-left hero-stagger">
        <span class="eyebrow">{{ t('home.eyebrow') }}</span>
        <h1 class="display">PrintMind</h1>
        <p class="hero-sub">
          {{ t('home.subtitle.pre') }}<span class="grad-text">{{ t('home.subtitle.highlight') }}</span>
        </p>
        <p class="hero-desc">{{ t('home.desc') }}</p>
        <div class="hero-actions">
          <button class="btn btn-primary btn-lg" type="button" @click="router.push('/diagnose')">
            {{ t('home.cta.diagnose') }}
          </button>
          <button class="btn btn-lg" type="button" @click="router.push('/experiment-summary')">
            {{ t('home.cta.experiments') }}
          </button>
        </div>
      </div>

      <div class="hero-right">
        <div class="showcase">
          <img v-if="heroShowcase" class="fade-in" :src="heroShowcase" alt="3D print showcase" />
          <div v-else class="showcase-empty">
            <svg class="cube" viewBox="0 0 140 120" aria-hidden="true">
              <defs>
                <linearGradient id="pmCube" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stop-color="#3b82f6" />
                  <stop offset="1" stop-color="#9b5cff" />
                </linearGradient>
              </defs>
              <g fill="none" stroke="url(#pmCube)" stroke-width="2.4" stroke-linejoin="round">
                <path d="M70 26 118 50 70 74 22 50Z" />
                <path d="M22 50 22 60 70 84 118 60 118 50" />
                <path d="M70 74 70 84" />
                <path d="M70 90 118 66 70 42 22 66Z" opacity=".45" />
                <path d="M22 66 22 76 70 100 118 76 118 66" opacity=".45" />
              </g>
            </svg>
            <span class="showcase-empty-title">{{ t('home.showcase.placeholder') }}</span>
            <span class="showcase-empty-hint">{{ t('home.showcase.subtitle') }}</span>
          </div>
          <span class="hero-float f1">{{ t('home.float1') }}</span>
          <span class="hero-float f3 glass">
            <i class="float-dot"></i>{{ t('home.float3') }}
          </span>
        </div>
      </div>
    </section>

    <!-- 三步使用方法 -->
    <section class="section">
      <h2 class="section-title">{{ t('home.steps.title') }}</h2>
      <div class="steps">
        <div class="step">
          <span class="icon-dot blue">01</span>
          <span class="step-title">{{ t('home.step1.title') }}</span>
          <span class="step-desc">{{ t('home.step1.desc') }}</span>
        </div>
        <span class="step-arrow">→</span>
        <div class="step">
          <span class="icon-dot purple">02</span>
          <span class="step-title">{{ t('home.step2.title') }}</span>
          <span class="step-desc">{{ t('home.step2.desc') }}</span>
        </div>
        <span class="step-arrow">→</span>
        <div class="step">
          <span class="icon-dot cyan">03</span>
          <span class="step-title">{{ t('home.step3.title') }}</span>
          <span class="step-desc">{{ t('home.step3.desc') }}</span>
        </div>
      </div>
    </section>

    <!-- Before / After -->
    <section class="section">
      <h2 class="section-title">{{ t('home.ba.title') }}</h2>
      <div class="ba">
        <figure class="ba-figure">
          <div class="ba-image">
            <img v-if="beforeImage" class="fade-in" :src="beforeImage" alt="before" />
            <div v-else class="ba-placeholder">{{ t('home.ba.baseline') }}</div>
          </div>
          <figcaption>
            <span class="badge badge-neutral">{{ t('home.ba.baseline') }}</span>
            <span class="ba-name">{{ baseline?.experiment_id || 'REAL-001' }}</span>
            <span class="score-badge neutral">{{ score(closedLoop?.quality_before ?? 65) }}</span>
          </figcaption>
        </figure>

        <div class="ba-mid"><span class="ba-arrow">→</span></div>

        <figure class="ba-figure">
          <div class="ba-image">
            <img v-if="afterImage" class="fade-in" :src="afterImage" alt="after" />
            <div v-else class="ba-placeholder">{{ t('home.ba.closed') }}</div>
          </div>
          <figcaption>
            <span class="badge badge-purple">{{ t('home.ba.closed') }}</span>
            <span class="ba-name">{{ closedLoop?.experiment_id || 'REAL-006' }}</span>
            <span class="score-badge gradient">{{ score(closedLoop?.quality_after ?? 78) }}</span>
          </figcaption>
        </figure>
      </div>
      <p class="ba-note">{{ t('home.ba.note') }}</p>
      <ul class="ba-checks">
        <li><i class="check"></i>{{ t('home.ba.s1') }}</li>
        <li><i class="check"></i>{{ t('home.ba.s2') }}</li>
        <li><i class="check"></i>{{ t('home.ba.s4') }}</li>
      </ul>
    </section>

    <!-- 核心能力 -->
    <section class="section">
      <h2 class="section-title">{{ t('home.cap.title') }}</h2>
      <div class="caps">
        <div class="cap">
          <span class="icon-dot blue">◉</span>
          <span class="cap-title">{{ t('home.cap1.title') }}</span>
          <span class="cap-desc">{{ t('home.cap1.desc') }}</span>
        </div>
        <div class="cap">
          <span class="icon-dot purple">✦</span>
          <span class="cap-title">{{ t('home.cap2.title') }}</span>
          <span class="cap-desc">{{ t('home.cap2.desc') }}</span>
        </div>
        <div class="cap">
          <span class="icon-dot cyan">↻</span>
          <span class="cap-title">{{ t('home.cap3.title') }}</span>
          <span class="cap-desc">{{ t('home.cap3.desc') }}</span>
        </div>
        <div class="cap">
          <span class="icon-dot purple">✓</span>
          <span class="cap-title">{{ t('home.cap4.title') }}</span>
          <span class="cap-desc">{{ t('home.cap4.desc') }}</span>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta">
      <h2 class="cta-title">{{ t('home.cta.title') }}</h2>
      <p class="cta-desc">{{ t('home.cta.desc') }}</p>
      <div class="cta-actions">
        <button class="btn btn-primary btn-lg" type="button" @click="router.push('/diagnose')">
          {{ t('home.cta.diagnose') }}
        </button>
        <button class="btn btn-lg" type="button" @click="router.push('/experiment-summary')">
          {{ t('home.cta.experiments') }}
        </button>
      </div>
    </section>

    <p v-if="loading" class="muted center">…</p>
  </main>
</template>

<style scoped>
.home {
  max-width: 1120px;
  margin: 0 auto;
  padding: 3.5rem 2rem 6rem;
  display: flex;
  flex-direction: column;
  gap: 4.25rem;
}

.demo-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: -2rem;
  padding: 0.6rem 0.9rem;
  border: 1px dashed rgba(99, 102, 255, 0.35);
  border-radius: var(--radius-md);
  background: rgba(99, 102, 255, 0.05);
}

.demo-badge {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--blue-bright);
  background: rgba(99, 102, 255, 0.14);
  border-radius: 999px;
  padding: 0.22rem 0.65rem;
}

.demo-link {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--blue-bright);
  text-decoration: none;
}

.demo-link:hover {
  text-decoration: underline;
}

.hero {
  position: relative;
  z-index: 0;
  display: grid;
  grid-template-columns: 46fr 54fr;
  gap: 3rem;
  align-items: center;
  min-height: 680px;
}

.hero::before {
  content: '';
  position: absolute;
  inset: -60px -10% -30px -10%;
  z-index: -1;
  pointer-events: none;
  background:
    radial-gradient(36rem 24rem at 8% 14%, rgba(59, 130, 246, 0.12), transparent 62%),
    radial-gradient(32rem 22rem at 88% 6%, rgba(139, 92, 246, 0.1), transparent 62%),
    radial-gradient(28rem 20rem at 92% 96%, rgba(20, 200, 176, 0.09), transparent 62%);
  filter: blur(12px);
}

.hero::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -14px;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(99, 102, 255, 0.22),
    rgba(20, 200, 176, 0.18),
    transparent
  );
}

.hero-left {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.hero-left .eyebrow {
  align-self: flex-start;
  font-size: 0.72rem;
  padding: 0.24rem 0.7rem;
}

.hero-sub {
  margin: 0.4rem 0 0;
  font-size: clamp(22px, 2.6vw, 32px);
  color: var(--text-main);
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: -0.015em;
}

.hero-sub .grad-text {
  font-weight: 800;
}

.hero-desc {
  margin: 0;
  color: #475569;
  max-width: 520px;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  gap: 0.8rem;
  margin-top: 0.75rem;
  flex-wrap: wrap;
}

.showcase {
  border-radius: 30px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: #f2f4f8;
  box-shadow: 0 18px 44px rgba(47, 80, 200, 0.1), 0 6px 16px rgba(16, 18, 24, 0.05);
}

.showcase img {
  display: block;
  width: 100%;
  aspect-ratio: 5 / 4;
  object-fit: cover;
}

.showcase-empty {
  aspect-ratio: 5 / 4;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.7rem;
  text-align: center;
  padding: 2rem;
  background: linear-gradient(
    160deg,
    rgba(59, 130, 246, 0.05) 0%,
    rgba(139, 92, 246, 0.06) 60%,
    rgba(20, 200, 176, 0.05) 100%
  );
}

.cube {
  width: 118px;
  height: auto;
}

.showcase-empty-title {
  font-size: 1.12rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text-main);
}

.showcase-empty-hint {
  font-size: 0.85rem;
  color: var(--text-muted);
  max-width: 20rem;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

.steps {
  display: flex;
  align-items: flex-start;
  gap: 1.25rem;
}

.step {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1.25rem;
  border-radius: var(--radius-md);
  transition:
    transform 0.3s var(--spring-soft),
    background 0.2s var(--ease);
}

.step:hover {
  transform: translateY(-3px);
  background: rgba(59, 130, 246, 0.04);
}

.step:hover .icon-dot {
  transform: scale(1.08);
}

.step-arrow {
  align-self: center;
  color: #d5dae2;
  font-size: 1rem;
}

.step-title {
  font-size: 1.1rem;
  font-weight: 700;
}

.step-desc {
  color: var(--text-3);
  font-size: 0.9rem;
}

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

.ba-name {
  color: var(--text-3);
  font-size: 0.88rem;
}

.ba-score {
  margin-left: auto;
  font-size: 1.4rem;
  font-weight: 700;
}

.ba-mid {
  display: flex;
  align-items: center;
  justify-content: center;
}

.ba-arrow {
  font-size: 2.4rem;
  color: var(--purple);
  font-weight: 800;
}

.ba-note {
  margin: 0;
  color: var(--text-2);
  font-size: 0.95rem;
  max-width: 60rem;
}

.score-badge {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 4rem;
  height: 4rem;
  padding: 0 1.1rem;
  border-radius: 999px;
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.score-badge.neutral {
  background: #eef1f5;
  color: #5f6b7a;
  border: 1px solid var(--border-strong);
}

.score-badge.gradient {
  background: var(--grad-main);
  color: #fff;
  box-shadow: 0 14px 30px rgba(124, 58, 237, 0.4);
}

.ba-checks {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem 1.5rem;
}

.ba-checks li {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.92rem;
  color: var(--text-2);
}

.check {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--cyan-soft-2);
  color: var(--cyan);
  font-size: 0.7rem;
  font-weight: 700;
}

.check::before {
  content: '✓';
}

.hero-float {
  position: absolute;
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 999px;
  padding: 0.28rem 0.66rem;
  box-shadow: 0 2px 8px rgba(16, 18, 24, 0.05);
}

.hero-float.f1 {
  top: 16px;
  left: 16px;
}

.hero-float.f3 {
  left: 16px;
  bottom: 16px;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  color: var(--text-secondary);
}

.float-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--cyan);
  box-shadow: 0 0 0 3px var(--cyan-soft-2);
}

.caps {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}

.cap {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem;
  border-radius: var(--radius-md);
  transition:
    transform 0.3s var(--spring-soft),
    background 0.2s var(--ease);
}

.cap:hover {
  transform: translateY(-3px);
  background: rgba(139, 92, 246, 0.04);
}

.cap:hover .icon-dot {
  transform: scale(1.08);
}

.cap-title {
  font-size: 1.05rem;
  font-weight: 700;
}

.cap-desc {
  color: var(--text-3);
  font-size: 0.9rem;
}

.cta {
  text-align: center;
  padding: 4rem 2rem;
  border-radius: var(--radius-xl);
  background: linear-gradient(180deg, #fbfbfe, #f3f4fa);
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
}

.cta-title {
  margin: 0;
  font-size: clamp(24px, 3vw, 34px);
  letter-spacing: -0.02em;
}

.cta-desc {
  margin: 0;
  color: var(--text-2);
  max-width: 34rem;
}

.cta-actions {
  display: flex;
  gap: 0.8rem;
  margin-top: 1rem;
  flex-wrap: wrap;
  justify-content: center;
}

.center {
  text-align: center;
}

@media (max-width: 900px) {
  .home {
    gap: 4rem;
  }
  .hero {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  .steps,
  .caps {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }
  .steps {
    flex-direction: column;
    gap: 0.4rem;
  }
  .step-arrow {
    transform: rotate(90deg);
    align-self: center;
  }
  .ba {
    grid-template-columns: 1fr;
  }
  .ba-mid {
    justify-content: center;
  }
  .cta {
    padding: 3rem 1.5rem;
  }
}

@media (max-width: 560px) {
  .caps {
    grid-template-columns: 1fr;
  }
}
</style>
