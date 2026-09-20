import { ref } from 'vue'
import {
  defectLabel,
  directionLabel,
  effectLabel,
  factorLabel,
  messages,
  severityLabel,
} from './messages'

const STORAGE_KEY = 'printmind.lang'

function initialLang() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'en' || stored === 'zh') return stored
  } catch (e) {
    /* ignore */
  }
  return 'zh'
}

export const lang = ref(initialLang())

export function setLang(value) {
  lang.value = value === 'en' ? 'en' : 'zh'
  try {
    localStorage.setItem(STORAGE_KEY, lang.value)
  } catch (e) {
    /* ignore */
  }
}

export function toggleLang() {
  setLang(lang.value === 'zh' ? 'en' : 'zh')
}

export function t(key, vars) {
  const dict = messages[lang.value] || messages.zh
  let text = dict[key] ?? messages.zh[key] ?? key
  if (vars) {
    Object.keys(vars).forEach((name) => {
      text = text.split(`{${name}}`).join(String(vars[name]))
    })
  }
  return text
}

export function defectText(code) {
  const item = defectLabel[code]
  return item ? item[lang.value] : code
}

export function severityText(code) {
  const item = severityLabel[code]
  return item ? item[lang.value] : code
}

export function factorText(code) {
  const item = factorLabel[code]
  return item ? item[lang.value] : code
}

export function directionText(code) {
  const item = directionLabel[code]
  return item ? item[lang.value] : code
}

export function effectText(code) {
  const item = effectLabel[code]
  return item ? item[lang.value] : code
}

// 把后端 warning 映射成用户可读文案（显示层翻译，不改后端值）
export function warningText(warning) {
  if (!warning) return ''
  const w = String(warning)
  if (
    w.includes('视觉分析不可用') ||
    w.includes('视觉模型未配置') ||
    w.includes('无法归类') ||
    w.includes('vision')
  ) {
    return t('err.vision_fallback')
  }
  if (w.includes('冲突')) {
    return t('warn.conflict')
  }
  return w
}

// 把开发语言错误统一映射成人话
export function friendlyError(message) {
  const m = String(message || '')
  if (/无法连接|Failed to fetch|NetworkError|Load failed|network/i.test(m)) return t('err.network')
  if (/10MB|10 MB/i.test(m)) return t('err.image_size')
  if (/JPG|JPEG|PNG|格式/i.test(m)) return t('err.image_type')
  if (/喷嘴|nozzle/i.test(m)) {
    if (/180|least|至少/i.test(m)) return t('err.nozzle_min')
    return t('err.nozzle_min')
  }
  if (/热床|bed/i.test(m)) {
    if (/120|exceed|超过/i.test(m)) return t('err.bed_max')
    return t('err.bed_min')
  }
  if (/422|Validation|Internal Server|Traceback|Schema|Literal|JSON|detail/i.test(m)) {
    return t('err.diagnose_failed')
  }
  return m || t('err.diagnose_failed')
}

// ---------- 实验结论显示层翻译（不改后端） ----------
const CONCLUSION_FACTORS = {
  '风扇': 'fan speed',
  '喷嘴温度': 'nozzle temperature',
  '热床温度': 'bed temperature',
  '打印速度': 'print speed',
  '回抽': 'retraction',
  '层高': 'layer height',
  '冷却': 'cooling',
}

function factorEn(name) {
  return CONCLUSION_FACTORS[name] || name
}

function joinScores(text) {
  const parts = String(text)
    .split('、')
    .map((s) => s.trim())
    .filter(Boolean)
  if (parts.length <= 1) return parts[0] || text
  if (parts.length === 2) return `${parts[0]} and ${parts[1]}`
  return `${parts.slice(0, -1).join(', ')} and ${parts[parts.length - 1]}`
}

export function translateConclusion(text, l) {
  const s = String(text || '')
  const target = l || lang.value
  if (target === 'zh') return s

  let m
  if ((m = s.match(/^增强(.+?)显示改善趋势。$/))) return `Increasing ${factorEn(m[1])} showed an improvement trend.`
  if ((m = s.match(/^提高(.+?)显示改善趋势。$/))) return `Increasing ${factorEn(m[1])} showed an improvement trend.`
  if ((m = s.match(/^降低(.+?)显示改善趋势。$/))) return `Lowering ${factorEn(m[1])} showed an improvement trend.`
  if ((m = s.match(/^提高(.+?)未显示改善趋势。$/))) return `Increasing ${factorEn(m[1])} did not show an improvement trend.`
  if ((m = s.match(/^降低(.+?)未显示改善趋势。$/))) return `Lowering ${factorEn(m[1])} did not show an improvement trend.`
  if ((m = s.match(/^提高(.+?)曾出现质量下降。$/))) return `Increasing ${factorEn(m[1])} was associated with a quality decrease.`
  if ((m = s.match(/^降低(.+?)曾出现质量下降。$/))) return `Lowering ${factorEn(m[1])} was associated with a quality decrease.`
  if ((m = s.match(/^(.+?)(提高|降低)后质量无明显变化。$/))) {
    return `${m[2] === '提高' ? 'Increasing' : 'Lowering'} ${factorEn(m[1])} showed no clear change.`
  }
  if ((m = s.match(/正式闭环验证质量由\s*([\d.]+)\s*提升至\s*([\d.]+)/))) {
    return `Closed-loop validation improved the quality score from ${m[1]} to ${m[2]}.`
  }
  if ((m = s.match(/重复实验达到\s*([\d、.]+)/))) {
    return `Repeatability trials using the same recommended settings reached scores of ${joinScores(
      m[1],
    )}, indicating a repeatable improvement trend.`
  }
  if ((m = s.match(/进一步调整参数（([^）]+)）未超过重复性验证的最佳结果（([^）]+)）/))) {
    return `Further parameter exploration (${m[1]}) did not exceed the best repeatability result (${m[2]}); under the current conditions, the repeatability settings remain the better candidate.`
  }
  if (/不代表统计显著性/.test(s)) {
    return 'These conclusions are based on a small number of experiments and are not statistically significant.'
  }
  return 'See the experiment summary for details.'
}
