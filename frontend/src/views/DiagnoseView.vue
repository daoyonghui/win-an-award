<script setup>
import { computed, reactive, ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { diagnose, getHistory, uploadUrl } from '../api.js'
import ImageDropUpload from '../components/ImageDropUpload.vue'
import { demoMode, showTips, setShowTips } from '../settings'
import {
  defectText,
  directionText,
  effectText,
  factorText,
  friendlyError,
  lang,
  severityText,
  t,
  warningText,
} from '../i18n/useLanguage'

const router = useRouter()

const form = reactive({
  material: 'PETG',
  data_source: 'real',
  nozzle_temp: 245,
  bed_temp: 80,
  print_speed: 150,
  fan_speed: 60,
  layer_height: 0.2,
  retraction: 0.8,
  symptom: '',
})

const loading = ref(false)
const error = ref('')
const result = ref(null)
const advancedOpen = ref(false)
const showDetails = ref(false)

const imageFile = ref(null)
const imagePreview = ref('')

const uploadRef = ref(null)
const demoLoading = ref(false)
const demoMessage = ref('')
const showFallbackDetail = ref(false)

const FALLBACK_LABELS = {
  timeout: { zh: '请求超时', en: 'Request timed out' },
  network_error: { zh: '网络异常', en: 'Network error' },
  http_4xx: { zh: '服务请求失败', en: 'Request failed' },
  http_5xx: { zh: '服务端异常', en: 'Server error' },
  invalid_model_response: { zh: '模型返回格式异常', en: 'Invalid model response' },
  json_parse_error: { zh: '模型结果解析失败', en: 'Model output could not be parsed' },
  analysis_failed: { zh: '视觉分析异常', en: 'Vision analysis error' },
  vision_not_configured: { zh: '视觉模型未配置', en: 'Vision model not configured' },
  defect_unknown: { zh: '视觉模型无法归类', en: 'Vision model could not classify' },
  no_image: { zh: '未上传图片', en: 'No image uploaded' },
}

function fallbackLabel(reason) {
  const item = FALLBACK_LABELS[reason]
  if (!item) return reason || ''
  return lang.value === 'zh' ? item.zh : item.en
}

async function loadReal001Demo() {
  demoLoading.value = true
  demoMessage.value = ''
  try {
    const data = await getHistory(100)
    const items = data.items || []
    const baseline =
      items.find((i) => i.data_source === 'real' && (i.notes || '').trim().startsWith('REAL-001')) ||
      items.find((i) => i.data_source === 'real' && (i.notes || '').includes('REAL-001')) ||
      items.slice().reverse().find((i) => i.data_source === 'real')
    if (!baseline) throw new Error('no baseline record')

    form.data_source = 'real'
    form.material = baseline.material || 'PETG'
    if (baseline.nozzle_temp != null) form.nozzle_temp = baseline.nozzle_temp
    if (baseline.bed_temp != null) form.bed_temp = baseline.bed_temp
    if (baseline.print_speed != null) form.print_speed = baseline.print_speed
    if (baseline.fan_speed != null) form.fan_speed = baseline.fan_speed
    if (baseline.layer_height != null) form.layer_height = baseline.layer_height
    if (baseline.retraction != null) form.retraction = baseline.retraction
    form.symptom = ''

    if (baseline.image_path) {
      const res = await fetch(uploadUrl(baseline.image_path))
      const blob = await res.blob()
      const file = new File([blob], baseline.image_path, {
        type: blob.type || 'image/jpeg',
      })
      uploadRef.value?.setFile(file)
    }
    demoMessage.value = t('demo.loaded')
  } catch (e) {
    demoMessage.value = t('demo.loadFailed')
  } finally {
    demoLoading.value = false
  }
}

const isExternal = computed(() => form.data_source === 'external')

// ---- flow ----
const FLOW_KEYS = ['flow.upload', 'flow.vision', 'flow.rule', 'flow.optimize', 'flow.done']
const STEP_KEYS = ['flow.step1', 'flow.step2', 'flow.step3', 'flow.done.msg']
const currentStep = ref(-1)
let stepTimer = null

const activeNode = computed(() =>
  currentStep.value < 0 ? -1 : Math.min(currentStep.value + 1, FLOW_KEYS.length - 1),
)
const statusText = computed(() => {
  if (loading.value) return t(STEP_KEYS[currentStep.value] || STEP_KEYS[0])
  if (result.value) return t(STEP_KEYS[STEP_KEYS.length - 1])
  return ''
})

function startFlow() {
  if (stepTimer) clearInterval(stepTimer)
  currentStep.value = 0
  stepTimer = setInterval(() => {
    if (currentStep.value < STEP_KEYS.length - 2) currentStep.value += 1
  }, 700)
}
function clearFlowTimer() {
  if (stepTimer) {
    clearInterval(stepTimer)
    stepTimer = null
  }
}
onBeforeUnmount(clearFlowTimer)

// ---- params ----
const PARAM_META = [
  { key: 'nozzle_temp', labelKey: 'diag.nozzle', unit: '℃', digits: 0 },
  { key: 'bed_temp', labelKey: 'diag.bed', unit: '℃', digits: 0 },
  { key: 'print_speed', labelKey: 'diag.speed', unit: 'mm/s', digits: 0 },
  { key: 'fan_speed', labelKey: 'diag.fan', unit: '%', digits: 0 },
  { key: 'retraction', labelKey: 'diag.retraction', unit: 'mm', digits: 1 },
]

function paramLabel(meta) {
  return t(meta.labelKey)
}
function formatConfidence(value) {
  const num = Number(value)
  if (value === null || value === undefined || Number.isNaN(num)) return '—'
  return `${Math.min(Math.round(num * 100), 99)}%`
}
function riskPercent(value) {
  const num = Number(value)
  if (Number.isNaN(num)) return 0
  return Math.round(Math.min(Math.max(num, 0), 1) * 100)
}
function currentValue(key) {
  const raw = form[key]
  if (raw === '' || raw === null || raw === undefined) return null
  return Number(raw)
}
function recommendedValue(key) {
  return (result.value?.recommended_parameters || {})[key]
}
function formatNumber(value, digits) {
  if (value === '' || value === null || value === undefined) return '—'
  const num = Number(value)
  if (Number.isNaN(num)) return '—'
  return digits > 0 ? num.toFixed(digits) : String(Math.round(num))
}
function changeLabel(meta) {
  const cur = currentValue(meta.key)
  const rec = Number(recommendedValue(meta.key))
  if (cur === null || Number.isNaN(rec)) return '—'
  const diff = rec - cur
  if (Math.abs(diff) < 1e-9) return t('res.keep')
  const delta = Math.abs(diff)
  const deltaText = meta.digits > 0 ? delta.toFixed(meta.digits) : String(Math.round(delta))
  return diff > 0 ? `↑ ${deltaText}` : `↓ ${deltaText}`
}
function isChanged(meta) {
  const cur = currentValue(meta.key)
  const rec = Number(recommendedValue(meta.key))
  if (cur === null || Number.isNaN(rec)) return false
  return Math.abs(rec - cur) > 1e-9
}

const experienceImproved = computed(() =>
  (result.value?.experience_summary || []).filter((i) => i.effect === 'improved'),
)
const experienceWorsened = computed(() =>
  (result.value?.experience_summary || []).filter((i) => i.effect === 'worsened'),
)
const primaryMeta = computed(() => PARAM_META.find((m) => isChanged(m)) || null)
const primaryChange = computed(() => {
  const meta = primaryMeta.value
  if (!meta) return null
  return {
    label: paramLabel(meta),
    from: formatNumber(currentValue(meta.key), meta.digits),
    to: formatNumber(recommendedValue(meta.key), meta.digits),
    unit: meta.unit,
  }
})
const unchangedParams = computed(() => PARAM_META.filter((m) => !isChanged(m)))

const primaryInsight = computed(() => {
  const meta = primaryMeta.value
  if (!meta) return null
  return (result.value?.experience_summary || []).find((i) => i.factor === meta.key) || null
})

const whyText = computed(() => {
  const insight = primaryInsight.value
  if (!insight) return t('res.why.fallback')
  if (lang.value === 'zh') {
    return `当前 P1S + PETG HF 的真实实验中，${factorText(insight.factor)}${directionText(
      insight.direction,
    )}表现出${effectText(insight.effect)}。`
  }
  return `In real P1S + PETG HF experiments, ${directionText(insight.direction)} ${factorText(
    insight.factor,
  )} showed ${effectText(insight.effect)}.`
})

const reasonConclusion = computed(() => {
  const labels = PARAM_META.filter((m) => isChanged(m)).map((m) => paramLabel(m))
  if (labels.length) return t('res.basis.therefore', { params: labels.join(' / ') })
  return t('res.basis.therefore.none')
})

function validate() {
  const nozzle = Number(form.nozzle_temp)
  const bed = Number(form.bed_temp)
  if (Number.isNaN(nozzle) || nozzle < 180) return t('err.nozzle_min')
  if (nozzle > 300) return t('err.nozzle_max')
  if (Number.isNaN(bed) || bed < 20) return t('err.bed_min')
  if (bed > 120) return t('err.bed_max')
  return ''
}

async function runDiagnosis() {
  const invalid = validate()
  if (invalid) {
    error.value = invalid
    return
  }

  loading.value = true
  error.value = ''
  result.value = null
  showDetails.value = false
  startFlow()

  const payload = {
    material: form.material,
    data_source: form.data_source,
    nozzle_temp: Number(form.nozzle_temp),
    bed_temp: Number(form.bed_temp),
    print_speed: Number(form.print_speed),
    fan_speed: Number(form.fan_speed),
    layer_height: Number(form.layer_height),
    retraction:
      form.retraction === '' || form.retraction === null ? null : Number(form.retraction),
    symptom: form.symptom,
  }

  try {
    result.value = await diagnose(payload, imageFile.value)
    clearFlowTimer()
    currentStep.value = STEP_KEYS.length - 1
  } catch (e) {
    clearFlowTimer()
    currentStep.value = -1
    error.value = friendlyError(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="diagnose">
    <header class="page-head">
      <button class="back-btn" type="button" @click="router.push('/')">← {{ t('nav.home') }}</button>
      <h1 class="section-title">{{ t('diag.title') }}</h1>
      <p class="lead">{{ t('diag.lead') }}</p>
    </header>

    <div v-if="showTips" class="firstuse glass">
      <span>{{ t('diag.firstuse') }}</span>
      <button class="btn" type="button" @click="setShowTips(false)">{{ t('diag.gotit') }}</button>
    </div>

    <div v-if="demoMode" class="demo-bar">
      <span class="demo-badge">{{ t('demo.badge') }}</span>
      <button class="btn" type="button" :disabled="demoLoading" @click="loadReal001Demo">
        {{ demoLoading ? t('demo.loading') : t('demo.loadReal001') }}
      </button>
      <span v-if="demoMessage" class="demo-msg">{{ demoMessage }}</span>
    </div>

    <form class="input-stage" @submit.prevent="runDiagnosis">
      <div class="stage-media surface">
        <ImageDropUpload ref="uploadRef" v-model="imageFile" v-model:preview="imagePreview" />
        <p v-if="isExternal" class="notice">{{ t('diag.external.notice') }}</p>
      </div>

      <div class="stage-form">
        <div class="group">
          <span class="group-title">{{ t('diag.basic') }}</span>
          <label class="field">
            <span>{{ t('diag.material') }}</span>
            <input v-model="form.material" type="text" readonly />
            <small class="help">{{ t('diag.help.material') }}</small>
          </label>
          <label class="field">
            <span>{{ t('diag.nozzle') }}</span>
            <input v-model.number="form.nozzle_temp" type="number" step="1" />
            <small class="help">{{ t('diag.help.nozzle') }}</small>
          </label>
          <label class="field">
            <span>{{ t('diag.bed') }}</span>
            <input v-model.number="form.bed_temp" type="number" step="1" />
            <small class="help">{{ t('diag.help.bed') }}</small>
          </label>
          <label class="field">
            <span>{{ t('diag.fan') }}</span>
            <input v-model.number="form.fan_speed" type="number" step="1" />
            <small class="help">{{ t('diag.help.fan') }}</small>
          </label>
        </div>

        <button class="advanced-toggle" type="button" @click="advancedOpen = !advancedOpen">
          {{ advancedOpen ? t('diag.advanced.hide') : t('diag.advanced') }}
          <span class="chev" :class="{ open: advancedOpen }">↓</span>
        </button>

        <div v-if="advancedOpen" class="group advanced">
          <label class="field">
            <span>{{ t('diag.speed') }}</span>
            <input v-model.number="form.print_speed" type="number" step="1" />
            <small class="help">{{ t('diag.help.speed') }}</small>
          </label>
          <label class="field">
            <span>{{ t('diag.layer') }}</span>
            <input v-model.number="form.layer_height" type="number" step="0.01" />
            <small class="help">{{ t('diag.help.layer') }}</small>
          </label>
          <label class="field">
            <span>{{ t('diag.retraction') }}</span>
            <input v-model.number="form.retraction" type="number" step="0.1" />
            <small class="help">{{ t('diag.help.retraction') }}</small>
          </label>
          <label class="field">
            <span>{{ t('diag.source') }}</span>
            <select v-model="form.data_source">
              <option value="real">{{ t('diag.source.real') }}</option>
              <option value="simulated">{{ t('diag.source.simulated') }}</option>
              <option value="external">{{ t('diag.source.external') }}</option>
            </select>
            <small class="help">{{ t('diag.help.source') }}</small>
          </label>
          <label class="field">
            <span>{{ t('diag.symptom') }}</span>
            <textarea v-model="form.symptom" rows="2" :placeholder="t('diag.symptom.placeholder')"></textarea>
          </label>
          <p v-if="isExternal" class="notice">{{ t('diag.external.params') }}</p>
        </div>

        <p class="unknown-hint">{{ t('diag.help.unknown') }}</p>

        <button class="btn btn-primary btn-lg submit-btn" type="submit" :disabled="loading">
          {{ loading ? t('diag.analyzing') : t('diag.submit') }}
        </button>
      </div>
    </form>

    <p v-if="error" class="error">{{ error }}</p>

    <section v-if="loading || result" class="flow glass">
      <div class="flow-steps">
        <div v-for="(key, i) in FLOW_KEYS" :key="key" class="flow-node">
          <span class="flow-dot" :class="{ done: i < activeNode, active: i === activeNode }">
            {{ i < activeNode ? '✓' : i + 1 }}
          </span>
          <span>{{ t(key) }}</span>
        </div>
      </div>
      <p class="flow-status">{{ statusText }}</p>
    </section>

    <!-- 结果：先只显示 问题 / 建议 / 为什么 -->
    <template v-if="result">
      <div v-if="result.fallback_used" class="fallback-banner">
        <template v-if="result.fallback_reason === 'no_image'">
          <span class="fb-dot neutral"></span>
          <span>{{ t('diag.fallback.noimage') }}</span>
        </template>
        <template v-else>
          <span class="fb-dot warn"></span>
          <div class="fb-body">
            <strong>{{ t('diag.fallback.title') }}</strong>
            <span class="fb-desc">{{ t('diag.fallback.desc') }}</span>
            <button class="fb-toggle" type="button" @click="showFallbackDetail = !showFallbackDetail">
              {{ t('diag.fallback.details') }}
            </button>
            <span v-if="showFallbackDetail" class="fb-reason">
              {{ fallbackLabel(result.fallback_reason) }}
            </span>
          </div>
        </template>
      </div>
      <div v-else class="fusion-badge">{{ t('diag.aiFusion') }}</div>

      <section class="result-top fade-up">
        <div class="rcard surface">
          <span class="eyebrow">{{ t('res.problem') }}</span>
          <h2 class="defect-name">{{ defectText(result.defect) }}</h2>
          <p class="defect-code">{{ result.defect }}</p>
          <span class="badge" :class="`badge-sev-${result.severity}`">
            {{ t('res.severity') }} · {{ severityText(result.severity) }}
          </span>
        </div>

        <div class="rcard surface">
          <span class="eyebrow">{{ t('res.suggest') }}</span>
          <template v-if="primaryChange">
            <h2 class="change-factor">{{ primaryChange.label }}</h2>
            <p class="change-values">
              {{ primaryChange.from }}{{ primaryChange.unit }}
              <span class="change-arrow">→</span>
              <b>{{ primaryChange.to }}{{ primaryChange.unit }}</b>
            </p>
            <span class="badge badge-cyan">{{ t('res.onlyone') }}</span>
          </template>
          <template v-else>
            <h2 class="change-factor">{{ t('res.keepall') }}</h2>
          </template>
        </div>

        <div class="rcard surface">
          <span class="eyebrow">{{ t('res.why') }}</span>
          <p class="why-text"><span class="why-icon">✓</span>{{ whyText }}</p>
        </div>
      </section>

      <button class="btn details-toggle" type="button" @click="showDetails = !showDetails">
        {{ showDetails ? t('res.details.hide') : t('res.details') }}
        <span class="chev" :class="{ open: showDetails }">↓</span>
      </button>

      <template v-if="showDetails">
        <div class="details-grid">
          <section class="surface dcard">
            <h3 class="dtitle">{{ t('res.visual') }}</h3>
            <img v-if="imagePreview" class="dphoto fade-in" :src="imagePreview" alt="print" />
            <ul v-if="result.visual_evidence && result.visual_evidence.length" class="dlist">
              <li v-for="(ev, i) in result.visual_evidence" :key="i">{{ ev }}</li>
            </ul>
            <p v-else class="muted small">{{ t('res.visual.none') }}</p>
          </section>

          <section v-if="result.experience_used" class="surface dcard">
            <h3 class="dtitle">{{ t('res.experience') }}</h3>
            <p class="muted small">
              {{ t('res.experience.count') }}：{{ result.experience_count }}
            </p>
            <div class="exp-group">
              <span class="exp-head">{{ t('res.experience.improved') }}</span>
              <ul v-if="experienceImproved.length" class="dlist">
                <li v-for="i in experienceImproved" :key="i.factor + i.direction">
                  <span>{{ factorText(i.factor) }} {{ directionText(i.direction) }}</span>
                  <span class="pos">+{{ i.quality_delta }}</span>
                </li>
              </ul>
              <p v-else class="muted small">—</p>
            </div>
            <div class="exp-group">
              <span class="exp-head">{{ t('res.experience.worsened') }}</span>
              <ul v-if="experienceWorsened.length" class="dlist">
                <li v-for="i in experienceWorsened" :key="i.factor + i.direction">
                  <span>{{ factorText(i.factor) }} {{ directionText(i.direction) }}</span>
                  <span class="neg">{{ i.quality_delta }}</span>
                </li>
              </ul>
              <p v-else class="muted small">—</p>
            </div>
          </section>

          <section class="surface dcard">
            <h3 class="dtitle">{{ t('res.risk') }}</h3>
            <p class="muted small">{{ t('res.risk.note') }}</p>
            <ul class="dlist">
              <li v-for="cause in result.possible_causes" :key="cause.cause">
                <span>{{ cause.cause }}</span>
                <span class="risk">{{ riskPercent(cause.risk_score) }}</span>
              </li>
              <li v-if="!result.possible_causes || !result.possible_causes.length" class="muted">
                —
              </li>
            </ul>
          </section>

          <section class="surface dcard">
            <h3 class="dtitle">{{ t('res.basis') }}</h3>
            <ul class="reason-chain">
              <li v-for="item in result.experience_summary" :key="item.factor + item.direction">
                <span class="mark" :class="item.effect === 'improved' ? 'ok' : 'no'">
                  {{ item.effect === 'improved' ? '✓' : '×' }}
                </span>
                <span>{{ factorText(item.factor) }} {{ directionText(item.direction) }}</span>
                <span class="delta" :class="item.quality_delta > 0 ? 'pos' : 'neg'">
                  {{ item.quality_delta > 0 ? '+' : '' }}{{ item.quality_delta }}
                </span>
              </li>
              <li v-if="!result.experience_summary || !result.experience_summary.length" class="muted">
                —
              </li>
            </ul>
            <p class="therefore">{{ reasonConclusion }}</p>
          </section>

          <section class="surface dcard">
            <h3 class="dtitle">{{ t('res.unchanged') }}</h3>
            <ul class="dlist">
              <li v-for="meta in unchangedParams" :key="meta.key">
                <span>{{ paramLabel(meta) }}</span>
                <span class="muted">
                  {{ formatNumber(currentValue(meta.key), meta.digits) }} →
                  {{ formatNumber(recommendedValue(meta.key), meta.digits) }}
                </span>
              </li>
            </ul>
          </section>

          <section class="surface dcard">
            <h3 class="dtitle">{{ t('res.notes') }}</h3>
            <div v-if="result.warning" class="warning-card">{{ warningText(result.warning) }}</div>
            <ul class="notes">
              <li v-if="!imagePreview">{{ t('res.note.noimage') }}</li>
              <li>{{ t('res.note.condition') }}</li>
              <li>{{ t('res.note.review') }}</li>
            </ul>
          </section>
        </div>
      </template>

      <button
        v-if="demoMode"
        class="btn btn-primary demo-closedloop"
        type="button"
        @click="router.push('/experiment-summary')"
      >
        {{ t('demo.viewClosedLoop') }}
      </button>
    </template>
  </main>
</template>

<style scoped>
.diagnose {
  max-width: 1080px;
  margin: 0 auto;
  padding: 3rem 2rem 5rem;
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

.page-head {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.page-head .lead {
  margin: 0;
  max-width: 40rem;
}

.back-btn {
  align-self: flex-start;
  background: none;
  border: none;
  color: var(--accent-strong);
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0;
}

.firstuse {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1.1rem;
  border-radius: var(--radius-md);
  font-size: 0.92rem;
  color: var(--text-2);
}

.input-stage {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  align-items: start;
}

.stage-media {
  padding: 1.25rem;
  position: sticky;
  top: 90px;
}

.stage-form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.group {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.group-title {
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-3);
  font-weight: 600;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.92rem;
  color: var(--text-2);
}

.field input,
.field select,
.field textarea {
  padding: 0.62rem 0.7rem;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  font-size: 0.98rem;
  font-family: inherit;
  background: var(--surface);
  color: var(--text);
}

.field input:focus-visible,
.field select:focus-visible,
.field textarea:focus-visible {
  outline: 3px solid rgba(91, 108, 255, 0.35);
  outline-offset: 1px;
  border-color: var(--accent);
}

.field input[readonly] {
  background: #f4f5f7;
  color: var(--text-3);
}

.help {
  font-size: 0.78rem;
  color: var(--text-3);
}

.advanced-toggle {
  align-self: flex-start;
  background: none;
  border: none;
  color: var(--accent-strong);
  font-family: inherit;
  font-size: 0.9rem;
  cursor: pointer;
  padding: 0.2rem 0;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.chev {
  display: inline-block;
  transition: transform 0.2s var(--ease);
}

.chev.open {
  transform: rotate(180deg);
}

.unknown-hint {
  margin: 0;
  font-size: 0.82rem;
  color: var(--text-3);
}

.notice {
  margin: 0.75rem 0 0;
  padding: 0.6rem 0.8rem;
  border-radius: var(--radius-sm);
  background: var(--warning-soft);
  border: 1px solid rgba(201, 138, 46, 0.24);
  color: var(--warning);
  font-size: 0.85rem;
}

.submit-btn {
  width: 100%;
}

/* flow */
.flow {
  border-radius: var(--radius-lg);
  padding: 1rem 1.3rem;
}

.flow-steps {
  display: flex;
  gap: 1.4rem;
  flex-wrap: wrap;
}

.flow-node {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.88rem;
  color: var(--text-3);
}

.flow-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.35rem;
  height: 1.35rem;
  border-radius: 50%;
  border: 1px solid var(--border-strong);
  font-size: 0.7rem;
}

.flow-dot.done {
  background: var(--success-soft);
  border-color: rgba(62, 155, 107, 0.3);
  color: var(--success);
}

.flow-dot.active {
  background: var(--accent-soft);
  border-color: rgba(91, 108, 255, 0.4);
  color: var(--accent-strong);
  font-weight: 700;
}

.flow-status {
  margin: 0.7rem 0 0;
  font-size: 0.88rem;
  color: var(--accent-strong);
}

/* result top */
.result-top {
  display: grid;
  grid-template-columns: 1fr 1fr 1.2fr;
  gap: 1.25rem;
}

.rcard {
  padding: 1.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  justify-content: center;
}

.defect-name {
  margin: 0;
  font-size: clamp(32px, 4vw, 48px);
  letter-spacing: -0.03em;
  font-weight: 700;
}

.defect-code {
  margin: 0;
  color: var(--text-3);
  font-size: 0.9rem;
}

.change-factor {
  margin: 0;
  font-size: clamp(24px, 2.6vw, 34px);
  letter-spacing: -0.02em;
  font-weight: 700;
}

.change-values {
  margin: 0;
  font-size: clamp(26px, 3vw, 40px);
  font-weight: 700;
  letter-spacing: -0.02em;
}

.change-values b {
  background: var(--grad-main);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.change-arrow {
  color: var(--purple);
  margin: 0 0.25rem;
  font-weight: 700;
}

.why-text {
  margin: 0;
  color: var(--text-2);
  line-height: 1.8;
}

.why-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  margin-right: 0.5rem;
  border-radius: 50%;
  background: var(--cyan-soft-2);
  color: var(--cyan);
  font-size: 0.7rem;
  font-weight: 700;
  vertical-align: middle;
}

.badge-sev-low {
  color: var(--success);
  background: var(--success-soft);
  border-color: rgba(62, 155, 107, 0.22);
}
.badge-sev-medium {
  color: var(--warning);
  background: var(--warning-soft);
  border-color: rgba(201, 138, 46, 0.24);
}
.badge-sev-high {
  color: var(--danger);
  background: var(--danger-soft);
  border-color: rgba(199, 92, 92, 0.22);
}

.details-toggle {
  align-self: center;
}

.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

.dcard {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.dtitle {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
}

.dphoto {
  width: 100%;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  object-fit: cover;
  max-height: 220px;
}

.dlist {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.92rem;
  color: var(--text-2);
}

.dlist li {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
}

.exp-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.exp-head {
  font-size: 0.82rem;
  color: var(--text-3);
}

.pos {
  color: var(--success);
  font-weight: 700;
}
.neg {
  color: var(--danger);
  font-weight: 700;
}

.risk {
  color: var(--accent-strong);
  font-weight: 700;
}

.reason-chain {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.reason-chain li {
  display: grid;
  grid-template-columns: 20px 1fr auto;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.92rem;
}

.mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 700;
}

.mark.ok {
  background: var(--success-soft);
  color: var(--success);
}
.mark.no {
  background: var(--danger-soft);
  color: var(--danger);
}

.delta {
  font-weight: 700;
}

.therefore {
  margin: 0.4rem 0 0;
  padding: 0.65rem 0.85rem;
  border-radius: var(--radius-sm);
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-weight: 600;
  font-size: 0.9rem;
}

.warning-card {
  padding: 0.7rem 0.9rem;
  border-radius: var(--radius-sm);
  background: var(--warning-soft);
  border: 1px solid rgba(201, 138, 46, 0.24);
  color: var(--warning);
  font-size: 0.88rem;
}

.notes {
  margin: 0;
  padding-left: 1.1rem;
  color: var(--text-2);
  line-height: 1.8;
  font-size: 0.88rem;
}

.small {
  font-size: 0.84rem;
}

.error {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  background: var(--danger-soft);
  color: var(--danger);
}

.demo-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
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

.demo-msg {
  font-size: 0.85rem;
  color: var(--text-2);
}

.fusion-badge {
  align-self: flex-start;
  font-size: 0.8rem;
  font-weight: 700;
  color: #0f9d8a;
  background: var(--cyan-soft-2);
  border: 1px solid rgba(20, 200, 176, 0.3);
  border-radius: 999px;
  padding: 0.28rem 0.75rem;
}

.fallback-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.85rem 1rem;
  border: 1px solid rgba(245, 158, 11, 0.35);
  border-left: 4px solid var(--warning);
  border-radius: var(--radius-md);
  background: var(--warning-soft);
  color: #8a6100;
  font-size: 0.9rem;
}

.fb-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 0.35rem;
  flex-shrink: 0;
}

.fb-dot.warn {
  background: var(--warning);
}

.fb-dot.neutral {
  background: var(--text-muted);
}

.fb-body {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.fb-desc {
  color: #9a6b12;
  font-size: 0.85rem;
}

.fb-toggle {
  align-self: flex-start;
  background: none;
  border: none;
  padding: 0;
  color: #8a6100;
  text-decoration: underline;
  cursor: pointer;
  font-size: 0.8rem;
}

.fb-reason {
  font-size: 0.82rem;
  color: #9a6b12;
}

.demo-closedloop {
  align-self: center;
}

@media (max-width: 900px) {
  .input-stage,
  .details-grid {
    grid-template-columns: 1fr;
  }
  .stage-media {
    position: static;
  }
  .result-top {
    grid-template-columns: 1fr;
  }
}
</style>
