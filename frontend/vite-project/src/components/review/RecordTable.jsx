import Badge from '../ui/Badge'
import Button from '../ui/Button'
import {
  formatCo2,
  formatDate,
  formatNumber,
  formatScope,
  formatSourceType,
  scopeColor,
  statusColor,
} from '../../lib/format'

export default function RecordTable({ records, actionId, onApprove, onReject }) {
  return (
    <div className="hidden overflow-x-auto rounded-xl border border-slate-200 bg-white md:block">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Date</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Source</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Activity</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Site</th>
            <th className="px-4 py-3 text-right font-medium text-slate-600">Quantity</th>
            <th className="px-4 py-3 text-right font-medium text-slate-600">CO₂</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Flag reason</th>
            <th className="px-4 py-3 text-right font-medium text-slate-600">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {records.map((record) => {
            const busy = actionId === record.id
            const canAct = record.status === 'pending' || record.status === 'flagged'

            return (
              <tr key={record.id} className="hover:bg-slate-50/80">
                <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                  {formatDate(record.record_date)}
                </td>
                <td className="px-4 py-3">
                  <span className="text-slate-900">{formatSourceType(record.source_type)}</span>
                  <Badge className={`ml-2 ${scopeColor(record.scope)}`}>
                    {formatScope(record.scope)}
                  </Badge>
                </td>
                <td className="px-4 py-3 font-medium text-slate-900">{record.activity_type}</td>
                <td className="max-w-[120px] truncate px-4 py-3 text-slate-600" title={record.site_name}>
                  {record.site_name || '—'}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right tabular-nums text-slate-700">
                  {formatNumber(record.quantity_normalised, 2)}{' '}
                  <span className="text-slate-400">{record.unit_normalised}</span>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right font-medium tabular-nums text-slate-900">
                  {formatCo2(record.co2_kg)}
                </td>
                <td className="px-4 py-3">
                  <Badge className={statusColor(record.status)}>{record.status}</Badge>
                </td>
                <td className="max-w-xs px-4 py-3 text-slate-600">
                  {record.flag_reason || '—'}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right">
                  {canAct ? (
                    <div className="flex justify-end gap-2">
                      <Button
                        size="sm"
                        onClick={() => onApprove(record.id)}
                        disabled={busy}
                      >
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => onReject(record.id)}
                        disabled={busy}
                      >
                        Reject
                      </Button>
                    </div>
                  ) : (
                    <span className="text-xs text-slate-400">
                      {record.is_locked ? 'Locked' : '—'}
                    </span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
