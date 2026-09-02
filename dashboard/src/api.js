const API = 'http://localhost:8000/api'

export async function fetchOverview() {
  const res = await fetch(`${API}/overview`)
  return res.json()
}

export async function fetchRings() {
  const res = await fetch(`${API}/rings`)
  return res.json()
}

export async function fetchRingDetail(ringId) {
  const res = await fetch(`${API}/rings/${ringId}`)
  return res.json()
}

export async function fetchRingExplanation(ringId) {
  const res = await fetch(`${API}/rings/${ringId}/explain`)
  return res.json()
}

export async function fetchModels() {
  const res = await fetch(`${API}/models`)
  return res.json()
}
export async function chatWithRing(ringId, message, history) {
  const res = await fetch(`${API}/rings/${ringId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history })
  })
  return res.json()
}

export async function uploadAndAnalyze(file) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${API}/analyze`, {
    method: 'POST',
    body: formData
  })
  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail || 'Upload failed')
  }
  return res.json()
}
