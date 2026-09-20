<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getHistoryDetail, saveExperiment, saveHistoryResult, uploadUrl } from '../api.js'
import ImageDropUpload from '../components/ImageDropUpload.vue'
import { defectText, severityText, t, warningText } from '../i18n/useLanguage'

const props = defineProps({
  id: { type: [String, Number], required: true },
})

const router = useRouter()

const loading = ref(true)
const error = ref('')
const record = ref(null)

function sourceLabel(source) {
  if (source === 'simulated') return t('hist.source.simulated')
  if (source === 'external') return t('hist.source.external')
  return t('hist.source.real')
}

function sourceClass(source) {
  if (source === 'simulated') return 'sim'
  if (source === 'external') return 'ext'
  return 'real'
}

const ORIGINAL_PARAMS = [
  { key: 'nozzle_temp', labelKey: 'diag.nozzle', unit: '℃' },
  { key: 'bed_temp', labelKey: 'diag.bed', unit: '℃' },
  { key: 'print_speed', labelKey: 'diag.speed', unit: 'mm/s' },
  { key: 'fan_speed', labelKey: 'diag.fan', unit: '%' },
  { key: 'layer_height', labelKey: 'diag.layer', unit: 'mm' },
  { key: 'retraction', labelKey: 'diag.retraction', unit: 'mm' },
]

const RECOMMENDED_PARAMS = [
  { key: 'recommended_nozzle_temp', labelKey: 'diag.nozzle', unit: '℃' },
  { key: 'recommended_bed_temp', labelKey: 'diag.bed', unit: '℃' },
  { key: 'recommended_print_speed', labelKey: 'diag.speed', unit: 'mm/s' },
  { key: 'recommended_fan_speed', labelKey: 'diag.fan', unit: '%' },
  { key: 'recommended_retraction', labelKey: 'diag.retraction', unit: 'mm' },
]

const resultForm = reactive({
  quality_before: '',
  quality_after: '',
  result_status: 'unverified',
  notes: '',
})

const resultImageFile = ref(null)
const resultImagePreview = ref('')
const saving = ref(false)
const saveError = ref('')
const savedMessage = ref('')

const originalImage = computed(() => uploadUrl(record.value?.image_path))
const resultImage = computed(() => uploadUrl(record.value?.result_image_path))

// ---- 实验记录（与“系统优化验证”独立）----
const experimentForm = reactive({
  experiment_id: '',
  experiment_type: 'baseline',
  reference_record_id: '',
  quality_score: '',
  notes: '',
})

const experimentImageFile = ref(null)
const experimentImagePreview = ref('')
const experimentSaving = ref(false)
const experimentError = ref('')
const experimentMessage = ref('')

const experiments = computed(() => record.value?.experiments || [])

function experimentImageUrl(path) {
  return uploadUrl(path)
}

function experimentTypeLabel(type) {
  return t(`type.${type}`)
}

async function submitExperiment() {
  experimentSaving.value = true
  experimentError.value = ''
  experimentMessage.value = ''
  try {
    const created = await saveExperiment(
      props.id,
      { ...experimentForm },
      experimentImageFile.value,
    )
    if (record.value) {
      record.value.experiments = [created, ...(record.value.experiments || [])]
    }
    experimentMessage.value = t('hist.expSavedMsg')
    experimentForm.experiment_id = ''
    experimentForm.reference_record_id = ''
    experimentForm.quality_score = ''
    experimentForm.notes = ''
    experimentImageFile.value = null
  } catch (e) {
    experimentError.value = t('hist.saveError')
  } finally {
    experimentSaving.value = false
  }
}

function formatConfidence(value) {
  const num = Number(value)
  if (value === null || value === undefined || Number.isNaN(num)) return '—'
  return `${Math.min(Math.round(num * 100), 99)}%`
}

function formatTime(value) {
  if (!value) return '—'
  return String(value).replace('T', ' ')
}

async function submitResult() {
  saving.value = true
  saveError.value = ''
  savedMessage.value = ''
  try {
    const payload = {
      quality_before: resultForm.quality_before,
      quality_after: resultForm.quality_after,
      defect_improved:
        resultForm.result_status === 'yes'
          ? true
          : resultForm.result_status === 'no'
            ? false
            : null,
      notes: resultForm.notes,
    }
    record.value = await saveHistoryResult(props.id, payload, resultImageFile.value)
    savedMessage.value = t('hist.savedMsg')
  } catch (e) {
    saveError.value = t('hist.saveError')
  } finally {
    saving.value = false
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    record.value = await getHistoryDetail(props.id)
    if (record.value?.quality_before !== null && record.value?.quality_before !== undefined) {
      resultForm.quality_before = record.value.quality_before
    }
    if (record.value?.quality_after !== null && record.value?.quality_after !== undefined) {
      resultForm.quality_after = record.value.quality_after
    }
    if (record.value?.defect_improved === true) {
      resultForm.result_status = 'yes'
    } else if (record.value?.defect_improved === false) {
      resultForm.result_status = 'no'
    } else {
      resultForm.result_status = 'unverified'
    }
    if (record.value?.notes) resultForm.notes = record.value.notes
  } catch (e) {
    error.value = t('hist.loadError')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="page">
    <header class="page-header">
      <button class="back-btn" type="button" @click="router.push('/history')">
        {{ t('hist.back') }}
      </button>
      <h1>{{ t('hist.detail.title') }}</h1>
      <p class="hint">
        {{ t('hist.record') }} #{{ id }} · {{ formatTime(record?.created_at) }}
        <span v-if="record" class="tag" :class="sourceClass(record.data_source)">
          {{ sourceLabel(record.data_source) }}
        </span>
      </p>
    </header>

    <p v-if="loading" class="muted">{{ t('hist.loading') }}</p>
    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="record">
      <div v-if="record.warning" class="warning-card">
        <span class="warning-icon">!</span>
        <span>{{ warningText(record.warning) }}</span>
      </div>

      <!-- 第一次打印 -->
      <section class="panel surface">
        <h2 class="panel-title">{{ t('hist.firstPrint') }}</h2>

        <div class="two-col">
          <div class="col">
            <h3 class="sub-title">{{ t('hist.originalImage') }}</h3>
            <img v-if="originalImage" class="photo" :src="originalImage" alt="print" />
            <p v-else class="muted">{{ t('hist.noImage') }}</p>
          </div>

          <div class="col">
            <h3 class="sub-title">{{ t('hist.defectDiag') }}</h3>
            <div class="kv"><span>{{ t('hist.defect') }}</span><b>{{ defectText(record.defect) }}</b></div>
            <div class="kv">
              <span>{{ t('hist.severity') }}</span>
              <b class="severity" :data-level="record.severity">
                {{ severityText(record.severity) }}
              </b>
            </div>
            <div class="kv"><span>{{ t('hist.confidence') }}</span><b>{{ formatConfidence(record.confidence) }}</b></div>
          </div>
        </div>

        <h3 class="sub-title">{{ t('hist.originalParams') }}</h3>
        <table class="param-table">
          <tbody>
            <tr v-for="p in ORIGINAL_PARAMS" :key="p.key">
              <td>{{ t(p.labelKey) }}</td>
              <td class="right">{{ record[p.key] }} {{ p.unit }}</td>
            </tr>
          </tbody>
        </table>

        <p v-if="record.explanation" class="explanation">{{ record.explanation }}</p>
      </section>

      <!-- 系统推荐 -->
      <section class="panel surface">
        <h2 class="panel-title">{{ t('hist.recommended') }}</h2>
        <table class="param-table">
          <tbody>
            <tr v-for="p in RECOMMENDED_PARAMS" :key="p.key">
              <td>{{ t(p.labelKey) }}</td>
              <td class="right rec">{{ record[p.key] }} {{ p.unit }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- 实验记录 -->
      <section class="panel surface">
        <h2 class="panel-title">{{ t('hist.experiments') }}</h2>

        <div class="form-grid">
          <div class="field">
            <label>{{ t('hist.expId') }}</label>
            <input v-model="experimentForm.experiment_id" type="text" placeholder="REAL-001" />
          </div>
          <div class="field">
            <label>{{ t('hist.expType') }}</label>
            <select v-model="experimentForm.experiment_type">
              <option value="baseline">{{ t('type.baseline') }}</option>
              <option value="single_variable">{{ t('type.single_variable') }}</option>
              <option value="repeatability">{{ t('type.repeatability') }}</option>
              <option value="manual_comparison">{{ t('type.manual_comparison') }}</option>
            </select>
          </div>
          <div class="field">
            <label>{{ t('hist.expRef') }}</label>
            <input v-model="experimentForm.reference_record_id" type="number" step="1" min="1" />
          </div>
          <div class="field">
            <label>{{ t('hist.expScore') }}</label>
            <input v-model="experimentForm.quality_score" type="number" step="1" min="0" max="100" />
          </div>
        </div>

        <div class="field">
          <label>{{ t('hist.expImage') }}</label>
          <ImageDropUpload v-model="experimentImageFile" v-model:preview="experimentImagePreview" />
        </div>

        <div class="field">
          <label>{{ t('hist.notes') }}</label>
          <textarea v-model="experimentForm.notes" rows="2"></textarea>
        </div>

        <button
          class="btn btn-primary"
          type="button"
          :disabled="experimentSaving"
          @click="submitExperiment"
        >
          {{ experimentSaving ? t('diag.analyzing') : t('hist.expSave') }}
        </button>

        <p v-if="experimentError" class="error inline">{{ experimentError }}</p>
        <p v-if="experimentMessage" class="success inline">{{ experimentMessage }}</p>

        <div v-if="experiments.length" class="experiment-list">
          <h3 class="sub-title">{{ t('hist.expSaved') }}</h3>
          <ul class="exp-list">
            <li v-for="exp in experiments" :key="exp.id" class="exp-item">
              <div class="exp-head">
                <span class="exp-type">{{ experimentTypeLabel(exp.experiment_type) }}</span>
                <span v-if="exp.experiment_id" class="exp-id">{{ exp.experiment_id }}</span>
                <span class="exp-time">{{ formatTime(exp.created_at) }}</span>
              </div>
              <div class="exp-body">
                <span v-if="exp.quality_score !== null && exp.quality_score !== undefined">
                  {{ t('hist.expScore') }}：<b>{{ exp.quality_score }}</b>
                </span>
                <span v-if="exp.reference_record_id">#{{ exp.reference_record_id }}</span>
              </div>
              <p v-if="exp.notes" class="exp-notes">{{ exp.notes }}</p>
              <img
                v-if="exp.result_image_path"
                class="photo small"
                :src="experimentImageUrl(exp.result_image_path)"
                alt="experiment"
              />
            </li>
          </ul>
        </div>
        <p v-else class="muted">{{ t('hist.expNone') }}</p>
      </section>

      <!-- 系统优化验证 -->
      <section class="panel surface">
        <h2 class="panel-title">{{ t('hist.verifyTitle') }}</h2>
        <p class="panel-desc">{{ t('hist.verifyDesc') }}</p>

        <div class="field">
          <label>{{ t('hist.verifyImage') }}</label>
          <ImageDropUpload v-model="resultImageFile" v-model:preview="resultImagePreview" />
          <img
            v-if="!resultImagePreview && resultImage"
            class="photo small"
            :src="resultImage"
            alt="result"
          />
        </div>

        <div class="form-grid">
          <div class="field">
            <label>{{ t('hist.verifyBefore') }}</label>
            <input v-model="resultForm.quality_before" type="number" step="1" min="0" max="100" />
          </div>
          <div class="field">
            <label>{{ t('hist.verifyAfter') }}</label>
            <input v-model="resultForm.quality_after" type="number" step="1" min="0" max="100" />
          </div>
        </div>

        <div class="field">
          <label>{{ t('hist.verifyImproved') }}</label>
          <div class="radio-row">
            <label class="radio">
              <input v-model="resultForm.result_status" type="radio" value="unverified" />
              {{ t('hist.verifyUnverified') }}
            </label>
            <label class="radio">
              <input v-model="resultForm.result_status" type="radio" value="yes" /> {{ t('hist.yes') }}
            </label>
            <label class="radio">
              <input v-model="resultForm.result_status" type="radio" value="no" /> {{ t('hist.no') }}
            </label>
          </div>
          <p class="field-hint">{{ t('hist.verifyHint') }}</p>
        </div>

        <div class="field">
          <label>{{ t('hist.notes') }}</label>
          <textarea v-model="resultForm.notes" rows="3"></textarea>
        </div>

        <button class="btn btn-primary" type="button" :disabled="saving" @click="submitResult">
          {{ saving ? t('diag.analyzing') : t('hist.verifySave') }}
        </button>

        <p v-if="saveError" class="error inline">{{ saveError }}</p>
        <p v-if="savedMessage" class="success inline">{{ savedMessage }}</p>
      </section>

      <!-- 优化结果 -->
      <section class="panel surface">
        <h2 class="panel-title">{{ t('hist.resultTitle') }}</h2>
        <div class="result-box">
          <div class="result-line">
            {{ t('hist.resultStatus') }}：
            <b v-if="record.verified" :class="record.defect_improved ? 'good' : 'bad'">
              {{ record.defect_improved ? t('hist.resultYes') : t('hist.resultNo') }}
            </b>
            <b v-else>{{ t('hist.resultUnverified') }}</b>
          </div>

          <div v-if="record.verified" class="result-line">
            {{ t('hist.resultScore') }}
            <b>{{ record.quality_before ?? '—' }} → {{ record.quality_after ?? '—' }}</b>
          </div>
          <div
            v-else-if="record.quality_before !== null && record.quality_before !== undefined"
            class="result-line"
          >
            {{ t('hist.resultBaseline') }}<b>{{ record.quality_before }}</b>
          </div>

          <div v-if="record.notes" class="result-line">{{ t('hist.resultNotes') }}{{ record.notes }}</div>
          <img v-if="resultImage" class="photo small" :src="resultImage" alt="result" />

          <p
            v-if="
              !record.verified &&
              !record.notes &&
              (record.quality_before === null || record.quality_before === undefined) &&
              !resultImage
            "
            class="muted"
          >
            {{ t('hist.resultNone') }}
          </p>
        </div>
      </section>
    </template>
  </main>
</template>

<style scoped>
.page {
  max-width: 860px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  position: relative;
  text-align: center;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  margin: 0 0 0.25rem;
}

.hint {
  color: var(--text-3);
  font-size: 0.9rem;
  margin: 0;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 0;
  background: none;
  border: none;
  color: var(--accent-strong);
  cursor: pointer;
  font-size: 0.95rem;
  padding: 0.25rem 0;
}

.warning-card {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.85rem 1rem;
  margin-bottom: 1rem;
  border: 1px solid rgba(201, 138, 46, 0.24);
  border-left: 4px solid var(--warning);
  border-radius: var(--radius-sm);
  background: var(--warning-soft);
  color: var(--warning);
  font-size: 0.9rem;
}

.warning-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.1rem;
  height: 1.1rem;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--warning);
  color: #fff;
  font-weight: 700;
  font-size: 0.75rem;
}

.panel {
  padding: 1.25rem;
  margin-bottom: 1.25rem;
}

.panel-title {
  margin: 0 0 1rem;
  font-size: 1.15rem;
}

.panel-desc {
  margin: -0.5rem 0 1rem;
  font-size: 0.85rem;
  color: var(--text-3);
}

.sub-title {
  margin: 0.75rem 0 0.5rem;
  font-size: 0.95rem;
  color: var(--text-2);
}

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

.photo {
  width: 100%;
  max-height: 260px;
  object-fit: contain;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: #f6f8fa;
}

.photo.small {
  max-height: 200px;
  margin-top: 0.5rem;
}

.kv {
  display: flex;
  justify-content: space-between;
  padding: 0.4rem 0;
  border-bottom: 1px dashed var(--border);
}

.kv span {
  color: var(--text-3);
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

.tag {
  display: inline-block;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  font-size: 0.75rem;
}

.tag.real {
  background: var(--success-soft);
  color: var(--success);
}

.tag.sim {
  background: var(--warning-soft);
  color: var(--warning);
}

.tag.ext {
  background: #eef1f4;
  color: #555;
}

.param-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
  margin-bottom: 0.5rem;
}

.param-table td {
  padding: 0.45rem 0.6rem;
  border-bottom: 1px solid var(--border);
  color: var(--text-2);
}

.right {
  text-align: right;
}

.rec {
  color: var(--accent-strong);
  font-weight: 600;
}

.explanation {
  color: var(--text-2);
  line-height: 1.7;
  margin: 0.5rem 0 0;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  color: var(--text-2);
}

.field input[type='number'],
.field input[type='text'],
.field select,
.field textarea {
  padding: 0.5rem 0.6rem;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  font-size: 0.95rem;
  font-family: inherit;
  background: var(--surface);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.radio-row {
  display: flex;
  gap: 1.5rem;
}

.radio {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  cursor: pointer;
}

.field-hint {
  margin: 0.4rem 0 0;
  font-size: 0.8rem;
  color: var(--text-3);
}

.experiment-list {
  margin-top: 1.25rem;
}

.exp-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.exp-item {
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  margin-bottom: 0.6rem;
}

.exp-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}

.exp-type {
  font-weight: 600;
  color: var(--accent-strong);
  font-size: 0.9rem;
}

.exp-id {
  font-size: 0.82rem;
  color: var(--text-2);
  background: #eef1f4;
  border-radius: 999px;
  padding: 0.1rem 0.5rem;
}

.exp-time {
  margin-left: auto;
  font-size: 0.78rem;
  color: var(--text-3);
}

.exp-body {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--text-2);
}

.exp-notes {
  margin: 0.35rem 0 0;
  font-size: 0.85rem;
  color: var(--text-3);
}

.result-box {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  color: var(--text);
}

.result-line b {
  font-size: 1.05rem;
}

.good {
  color: var(--success);
}

.bad {
  color: var(--danger);
}

.muted {
  color: var(--text-3);
}

.error {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  background: var(--danger-soft);
  color: var(--danger);
}

.error.inline,
.success.inline {
  margin: 0.75rem 0 0;
}

.success {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  background: var(--success-soft);
  color: var(--success);
}

@media (max-width: 620px) {
  .two-col,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
