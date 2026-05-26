import { useEffect, useState } from 'react'
import { SOURCES, STATUS_OPTIONS } from '../../constants/sources'
import Alert from '../ui/Alert'
import Button from '../ui/Button'
import EmptyState from '../ui/EmptyState'
import Spinner from '../ui/Spinner'
import RecordCardList from './RecordCardList'
import RecordTable from './RecordTable'

export default function ReviewView({
  records,
  loading,
  error,
  actionId,
  initialStatus = 'flagged',
  initialSource = '',
  onLoad,
  onApprove,
  onReject,
}) {
  const [status, setStatus] = useState(initialStatus)
  const [sourceType, setSourceType] = useState(initialSource)

  useEffect(() => {
    setStatus(initialStatus)
  }, [initialStatus])

  useEffect(() => {
    onLoad({ status, sourceType })
  }, [status, sourceType, onLoad])

  const statusMeta = STATUS_OPTIONS.find((s) => s.id === status)

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            Review records
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Row-level review — approve clean rows or investigate flagged anomalies before audit lock.
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onLoad({ status, sourceType })}
          disabled={loading}
        >
          {loading ? <Spinner className="h-4 w-4" /> : 'Refresh'}
        </Button>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => setStatus(opt.id)}
              className={[
                'rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
                status === opt.id
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50',
              ].join(' ')}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <select
          value={sourceType}
          onChange={(e) => setSourceType(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
        >
          <option value="">All sources</option>
          {SOURCES.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {statusMeta && (
        <p className="text-sm text-slate-500">{statusMeta.description}</p>
      )}

      {error && (
        <Alert variant="error" title="Could not load records">
          {error}
        </Alert>
      )}

      {loading && records.length === 0 ? (
        <div className="flex min-h-[200px] items-center justify-center">
          <Spinner className="h-8 w-8" />
        </div>
      ) : records.length === 0 ? (
        <EmptyState
          title="No records in this queue"
          description={`No ${status} records${sourceType ? ' for this source' : ''}. Try another filter or ingest sample data.`}
        />
      ) : (
        <>
          <p className="text-sm text-slate-500">{records.length} record(s)</p>
          <RecordTable
            records={records}
            actionId={actionId}
            onApprove={onApprove}
            onReject={onReject}
          />
          <RecordCardList
            records={records}
            actionId={actionId}
            onApprove={onApprove}
            onReject={onReject}
          />
        </>
      )}
    </div>
  )
}
