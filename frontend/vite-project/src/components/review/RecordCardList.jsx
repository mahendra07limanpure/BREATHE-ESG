import Badge from '../ui/Badge'
import Button from '../ui/Button'
import Card from '../ui/Card'
import {
  formatCo2,
  formatDate,
  formatNumber,
  formatScope,
  formatSourceType,
  scopeColor,
  statusColor,
} from '../../lib/format'

export default function RecordCardList({ records, actionId, onApprove, onReject }) {
  return (
    <div className="space-y-3 md:hidden">
      {records.map((record) => {
        const busy = actionId === record.id
        const canAct = record.status === 'pending' || record.status === 'flagged'

        return (
          <Card key={record.id}>
            <div className="flex flex-wrap items-center gap-2">
              <Badge className={statusColor(record.status)}>{record.status}</Badge>
              <Badge className={scopeColor(record.scope)}>{formatScope(record.scope)}</Badge>
              <span className="text-xs text-slate-500">{formatSourceType(record.source_type)}</span>
            </div>
            <p className="mt-2 font-semibold text-slate-900">{record.activity_type}</p>
            <p className="text-sm text-slate-500">{formatDate(record.record_date)}</p>
            {record.site_name && (
              <p className="mt-1 text-sm text-slate-600">{record.site_name}</p>
            )}
            <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
              <div>
                <dt className="text-slate-500">Quantity</dt>
                <dd className="font-medium tabular-nums">
                  {formatNumber(record.quantity_normalised, 2)} {record.unit_normalised}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">CO₂</dt>
                <dd className="font-medium">{formatCo2(record.co2_kg)}</dd>
              </div>
            </dl>
            {record.flag_reason && (
              <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900 ring-1 ring-amber-100">
                {record.flag_reason}
              </p>
            )}
            {canAct && (
              <div className="mt-4 flex gap-2">
                <Button className="flex-1" size="sm" onClick={() => onApprove(record.id)} disabled={busy}>
                  Approve
                </Button>
                <Button
                  className="flex-1"
                  size="sm"
                  variant="danger"
                  onClick={() => onReject(record.id)}
                  disabled={busy}
                >
                  Reject
                </Button>
              </div>
            )}
          </Card>
        )
      })}
    </div>
  )
}
