import Card, { CardHeader } from '../ui/Card'
import { formatSourceType } from '../../lib/format'

export default function SourceBreakdown({ breakdown }) {
  if (!breakdown) return null

  const entries = Object.entries(breakdown)
  const max = Math.max(...entries.map(([, v]) => v), 1)

  return (
    <Card>
      <CardHeader
        title="Records by data source"
        description="All ingestion batches across SAP, utility, and travel."
      />
      <ul className="space-y-3">
        {entries.map(([source, count]) => (
          <li key={source}>
            <div className="mb-1 flex justify-between text-sm">
              <span className="font-medium text-slate-700">{formatSourceType(source)}</span>
              <span className="tabular-nums text-slate-900">{count}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-slate-400"
                style={{ width: `${(count / max) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </Card>
  )
}
