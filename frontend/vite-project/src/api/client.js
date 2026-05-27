const API_BASE = import.meta.env.VITE_API_URL || '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.error || data.detail || `Request failed (${response.status})`)
  }

  return data
}

export async function fetchDashboardStats() {
  return request('/dashboard/stats/')
}

export async function fetchCo2Summary() {
  return request('/summary/co2/')
}

export async function fetchRecords({ sourceType = '', status = 'pending', limit = 100 } = {}) {
  const params = new URLSearchParams()
  if (sourceType) params.set('source_type', sourceType)
  if (status) params.set('status', status)
  params.set('limit', String(limit))

  return request(`/records/review/?${params}`)
}

export async function uploadCsv(file, sourceType, uploadedBy = 'analyst@demo.breatheesg.com') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('source_type', sourceType)
  formData.append('uploaded_by', uploadedBy)

  return request('/upload/', {
    method: 'POST',
    body: formData,
  })
}

export async function approveRecord(recordId, note = 'Approved via dashboard') {
  return request(`/records/${recordId}/approve/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ performed_by: 'analyst', note }),
  })
}

export async function rejectRecord(recordId, note = 'Rejected via dashboard') {
  return request(`/records/${recordId}/reject/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ performed_by: 'analyst', note }),
  })
}

export async function approveAllRecords(status = 'pending', note = 'Bulk approved via dashboard') {
  return request('/records/approve-all/', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ performed_by: 'analyst', status, note }),
  })
}

export async function rejectAllRecords(status = 'flagged', note = 'Bulk rejected via dashboard - flagged anomalies') {
  return request('/records/reject-all/', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ performed_by: 'analyst', status, note }),
  })
}

export async function fetchAuditTrail(recordId) {
  return request(`/records/${recordId}/audit/`)
}

export async function getAuditReport() {
  return request('/audit/report/')
}

export async function loadSampleCsv(samplePath, downloadName) {
  const response = await fetch(samplePath)
  if (!response.ok) {
    throw new Error(`Could not load sample file (${response.status})`)
  }
  const blob = await response.blob()
  const uniqueName = downloadName.replace('.csv', `_${Date.now()}.csv`)
  return new File([blob], uniqueName, { type: 'text/csv' })
}
