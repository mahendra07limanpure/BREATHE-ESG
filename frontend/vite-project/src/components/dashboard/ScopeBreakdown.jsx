import Card, { CardHeader } from '../ui/Card'
import { formatCo2 } from '../../lib/format'

export default function ScopeBreakdown({ co2 }) {
  if (!co2) return null

  const items = [
    { key: 'scope_1', label: 'Scope 1', sub: 'Direct fuel', value: co2.scope_1_kg, color: 'bg-emerald-500' },
    { key: 'scope_2', label: 'Scope 2', sub: 'Electricity', value: co2.scope_2_kg, color: 'bg-sky-500' },
    { key: 'scope_3', label: 'Scope 3', sub: 'Travel', value: co2.scope_3_kg, color: 'bg-violet-500' },
  ]

  const total = items.reduce((sum, i) => sum + Number(i.value || 0), 0) || 1

  return (
    <Card>
      <CardHeader
        title="Approved emissions by scope"
        description="Totals from approved records only — pending and flagged are excluded."
      />
      <div className="space-y-4">
        {items.map((item) => {
          const pct = Math.round((Number(item.value || 0) / total) * 100)
          return (
            <div key={item.key}>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <div>
                  <span className="font-medium text-slate-900">{item.label}</span>
                  <span className="ml-2 text-slate-500">{item.sub}</span>
                </div>
                <span className="font-medium tabular-nums text-slate-900">
                  {formatCo2(item.value)}
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-full rounded-full transition-all ${item.color}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
      <p className="mt-4 text-xs text-slate-500">
        {co2.approved_records} approved records contributing to these totals.
      </p>
    </Card>
  )
}
