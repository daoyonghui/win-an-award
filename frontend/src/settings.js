import { ref } from 'vue'

const MOTION_KEY = 'printmind.motion'
const HINT_KEY = 'printmind.diagHintDismissed'
const DEMO_KEY = 'printmind.demoMode'

function read(key, fallback) {
  try {
    const value = localStorage.getItem(key)
    return value === null ? fallback : value
  } catch (e) {
    return fallback
  }
}

// 'standard' | 'reduced'
export const motion = ref(read(MOTION_KEY, 'standard'))

// 是否显示新手提示（与诊断页共用同一 localStorage 键）
export const showTips = ref(read(HINT_KEY, '0') !== '1')

// 比赛演示模式
export const demoMode = ref(read(DEMO_KEY, '0') === '1')

export function setDemoMode(value) {
  demoMode.value = !!value
  try {
    localStorage.setItem(DEMO_KEY, demoMode.value ? '1' : '0')
  } catch (e) {
    /* ignore */
  }
}

export function applyMotion() {
  const root = document.documentElement
  if (motion.value === 'reduced') root.setAttribute('data-motion', 'reduced')
  else root.removeAttribute('data-motion')
}

export function setMotion(value) {
  motion.value = value === 'reduced' ? 'reduced' : 'standard'
  try {
    localStorage.setItem(MOTION_KEY, motion.value)
  } catch (e) {
    /* ignore */
  }
  applyMotion()
}

export function setShowTips(value) {
  showTips.value = !!value
  try {
    localStorage.setItem(HINT_KEY, showTips.value ? '0' : '1')
  } catch (e) {
    /* ignore */
  }
}
