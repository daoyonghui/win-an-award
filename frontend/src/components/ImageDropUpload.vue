<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { t } from '../i18n/useLanguage'

const props = defineProps({
  modelValue: { type: Object, default: null },
  title: { type: String, default: '' },
  hint: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'update:preview'])

const ALLOWED_TYPES = ['image/jpeg', 'image/png']
const MAX_IMAGE_SIZE = 10 * 1024 * 1024

const fileInput = ref(null)
const dragging = ref(false)
const error = ref('')
const previewUrl = ref('')

const displayTitle = computed(() => props.title || t('diag.upload.title'))
const displayHint = computed(() => props.hint || t('diag.upload.hint'))

function revokePreview() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
}

function setFile(file) {
  error.value = ''
  if (!file) return
  if (!ALLOWED_TYPES.includes(file.type)) {
    error.value = t('err.image_type')
    return
  }
  if (file.size > MAX_IMAGE_SIZE) {
    error.value = t('err.image_size')
    return
  }
  revokePreview()
  previewUrl.value = URL.createObjectURL(file)
  emit('update:modelValue', file)
  emit('update:preview', previewUrl.value)
}

function openPicker() {
  fileInput.value?.click()
}

function onFileChange(event) {
  setFile(event.target.files?.[0])
  event.target.value = ''
}

function onDrop(event) {
  event.preventDefault()
  dragging.value = false
  setFile(event.dataTransfer?.files?.[0])
}

function onDragEnter(event) {
  event.preventDefault()
  dragging.value = true
}

function onDragOver(event) {
  event.preventDefault()
  dragging.value = true
}

function onDragLeave(event) {
  event.preventDefault()
  dragging.value = false
}

function removeFile() {
  revokePreview()
  error.value = ''
  emit('update:modelValue', null)
  emit('update:preview', '')
}

watch(
  () => props.modelValue,
  (value) => {
    if (!value) {
      revokePreview()
      emit('update:preview', '')
    }
  },
)

onBeforeUnmount(revokePreview)

defineExpose({ setFile })
</script>

<template>
  <div class="drop-upload">
    <div
      v-if="!previewUrl"
      class="drop-zone"
      :class="{ dragging }"
      @click="openPicker"
      @dragenter="onDragEnter"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <p class="drop-title">{{ dragging ? t('diag.upload.drop') : displayTitle }}</p>
      <p class="drop-hint">{{ displayHint }}</p>
    </div>

    <div v-else class="drop-preview">
      <img class="fade-scale-in" :src="previewUrl" :alt="t('diag.upload.preview')" />
      <div class="drop-actions">
        <button type="button" class="ghost-btn" @click="openPicker">
          {{ t('diag.upload.reselect') }}
        </button>
        <button type="button" class="ghost-btn danger" @click="removeFile">
          {{ t('diag.upload.remove') }}
        </button>
      </div>
    </div>

    <input
      ref="fileInput"
      class="drop-input"
      type="file"
      accept=".jpg,.jpeg,.png,image/jpeg,image/png"
      @change="onFileChange"
    />

    <p v-if="error" class="drop-error">{{ error }}</p>
  </div>
</template>

<style scoped>
.drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 1.5rem 1rem;
  border: 2px dashed #ccd2da;
  border-radius: 10px;
  background: #fafbfc;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.drop-zone:hover,
.drop-zone.dragging {
  border-color: #1f6feb;
  background: #f0f6ff;
}

.drop-title {
  margin: 0;
  font-weight: 600;
  color: #333;
}

.drop-hint {
  margin: 0;
  font-size: 0.78rem;
  color: #999;
}

.drop-preview {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.drop-preview img {
  max-width: 100%;
  max-height: 280px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.75);
  box-shadow: 0 8px 24px rgba(31, 52, 92, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.7);
  object-fit: contain;
  background: #f6f8fa;
}

.drop-actions {
  display: flex;
  gap: 0.5rem;
}

.ghost-btn {
  padding: 0.3rem 0.8rem;
  border: 1px solid #ccd2da;
  border-radius: 6px;
  background: #fff;
  color: #333;
  cursor: pointer;
  font-size: 0.85rem;
}

.ghost-btn:hover {
  border-color: #1f6feb;
  color: #1f6feb;
}

.ghost-btn.danger:hover {
  border-color: #b3261e;
  color: #b3261e;
}

.drop-input {
  display: none;
}

.drop-error {
  margin: 0.4rem 0 0;
  font-size: 0.85rem;
  color: #b3261e;
}
</style>
