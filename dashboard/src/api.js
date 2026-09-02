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
