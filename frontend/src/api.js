export const API_BASE = 'http://127.0.0.1:8000'

export function uploadUrl(filename) {
  if (!filename) return ''
  return `${API_BASE}/uploads/${encodeURIComponent(filename)}`
}

async function handleResponse(res) {
  if (!res.ok) {
    let detail = `请求失败（HTTP ${res.status}）`
    try {
      const data = await res.json()
      if (data && data.detail) {
        detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
      }
    } catch (e) {
      // 忽略解析错误，使用默认提示
    }
    throw new Error(detail)
  }
  return res.json()
}

// 统一请求入口：网络不可用时返回友好错误，避免页面出现原始异常
async function request(url, options) {
  let res
  try {
    res = await fetch(url, options)
  } catch (e) {
    throw new Error('无法连接到后端服务，请确认 PrintMind 后端已启动。')
  }
  return handleResponse(res)
}

export async function diagnose(payload, imageFile) {
  // 有图片时使用 multipart/form-data，让后端视觉智能体参与诊断
  if (imageFile) {
    const formData = new FormData()
    Object.entries(payload).forEach(([key, value]) => {
      if (value !== undefined && value !== null) formData.append(key, value)
    })
    formData.append('image', imageFile)

    return request(`${API_BASE}/diagnose`, {
      method: 'POST',
      body: formData,
    })
  }

  // 无图片时保持 JSON 纯规则诊断
  return request(`${API_BASE}/diagnose`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function getHistory(limit = 20) {
  return request(`${API_BASE}/history?limit=${encodeURIComponent(limit)}`)
}

export async function getStats(includeSimulated = false) {
  const query = includeSimulated ? '?include_simulated=true' : ''
  return request(`${API_BASE}/stats${query}`)
}

export async function getExperimentSummary() {
  return request(`${API_BASE}/experiment-summary`)
}

export async function getHistoryDetail(id) {
  return request(`${API_BASE}/history/${encodeURIComponent(id)}`)
}

export async function saveHistoryResult(id, payload, imageFile) {
  const formData = new FormData()
  if (payload.quality_before !== '' && payload.quality_before !== null && payload.quality_before !== undefined) {
    formData.append('quality_before', payload.quality_before)
  }
  if (payload.quality_after !== '' && payload.quality_after !== null && payload.quality_after !== undefined) {
    formData.append('quality_after', payload.quality_after)
  }
  if (payload.defect_improved === true) {
    formData.append('defect_improved', 'true')
  } else if (payload.defect_improved === false) {
    formData.append('defect_improved', 'false')
  }
  // defect_improved 为 null（未验证 / 不适用）时不提交该字段
  if (payload.notes) formData.append('notes', payload.notes)
  if (imageFile) formData.append('result_image', imageFile)

  return request(`${API_BASE}/history/${encodeURIComponent(id)}/result`, {
    method: 'POST',
    body: formData,
  })
}

export async function saveExperiment(id, payload, imageFile) {
  const formData = new FormData()
  if (payload.experiment_id) formData.append('experiment_id', payload.experiment_id)
  if (payload.experiment_type) formData.append('experiment_type', payload.experiment_type)
  if (
    payload.reference_record_id !== '' &&
    payload.reference_record_id !== null &&
    payload.reference_record_id !== undefined
  ) {
    formData.append('reference_record_id', payload.reference_record_id)
  }
  if (
    payload.quality_score !== '' &&
    payload.quality_score !== null &&
    payload.quality_score !== undefined
  ) {
    formData.append('quality_score', payload.quality_score)
  }
  if (payload.notes) formData.append('notes', payload.notes)
  if (imageFile) formData.append('result_image', imageFile)

  return request(`${API_BASE}/history/${encodeURIComponent(id)}/experiment`, {
    method: 'POST',
    body: formData,
  })
}
