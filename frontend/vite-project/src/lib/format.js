export function formatNumber(value, decimals = 2) {
  const n = Number(value)
  if (Number.isNaN(n)) return '—'
  return n.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function formatCo2(kg) {
  const n = Number(kg)
  if (Number.isNaN(n)) return '—'
  if (n >= 1000) {
    return `${formatNumber(n / 1000, 2)} t`
  }
  return `${formatNumber(n, 1)} kg`
}

export function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatSourceType(id) {
  const labels = {
    sap_fuel: 'SAP Fuel',
    electricity: 'Electricity',
    travel: 'Travel',
  }
  return labels[id] || id
}

export function formatScope(scope) {
  const labels = {
    scope_1: 'Scope 1',
    scope_2: 'Scope 2',
    scope_3: 'Scope 3',
  }
  return labels[scope] || scope
}

export function scopeColor(scope) {
  switch (scope) {
    case 'scope_1':
      return 'bg-emerald-100 text-emerald-800 ring-emerald-600/20'
    case 'scope_2':
      return 'bg-sky-100 text-sky-800 ring-sky-600/20'
    case 'scope_3':
      return 'bg-violet-100 text-violet-800 ring-violet-600/20'
    default:
      return 'bg-slate-100 text-slate-700 ring-slate-600/20'
  }
}

export function statusColor(status) {
  switch (status) {
    case 'approved':
      return 'bg-emerald-50 text-emerald-700 ring-emerald-600/20'
    case 'flagged':
      return 'bg-amber-50 text-amber-800 ring-amber-600/20'
    case 'rejected':
      return 'bg-red-50 text-red-700 ring-red-600/20'
    default:
      return 'bg-slate-50 text-slate-600 ring-slate-500/20'
  }
}
