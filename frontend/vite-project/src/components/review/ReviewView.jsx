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
  onBulkApprove,
  onBulkReject,
  onReject,
}) {
  const [status, setStatus] = useState(initialStatus)
  const [sourceType, setSourceType] = useState(initialSource)
  const [showBulkApproveDialog, setShowBulkApproveDialog] = useState(false)
  const [showBulkRejectDialog, setShowBulkRejectDialog] = useState(false)
  const [bulkApproving, setBulkApproving] = useState(false)
  const [bulkRejecting, setBulkRejecting] = useState(false)

  useEffect(() => {
    setStatus(initialStatus)
  }, [initialStatus])

  useEffect(() => {
    setSourceType(initialSource)
  }, [initialSource])

  // FIX: Removed onLoad from dependency array
  // onLoad is a function that changes on every parent render, causing infinite loops
  // Removing it ensures the effect only runs when status or sourceType changes
  useEffect(() => {
    onLoad({ status, sourceType })
  }, [status, sourceType])

  const handleBulkApprove = async () => {
    setBulkApproving(true)
    try {
      await onBulkApprove(status)
      setShowBulkApproveDialog(false)
      // Reload the records after bulk approval
      await onLoad({ status, sourceType })
    } finally {
      setBulkApproving(false)
    }
  }

  const handleBulkReject = async () => {
    setBulkRejecting(true)
    try {
      await onBulkReject(status)
      setShowBulkRejectDialog(false)
      // Reload the records after bulk rejection
      await onLoad({ status, sourceType })
    } finally {
      setBulkRejecting(false)
    }
  }

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
        <div className="flex gap-2">
          {records.length > 0 && (
            <>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setShowBulkApproveDialog(true)}
                disabled={loading || bulkApproving || bulkRejecting}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {bulkApproving ? <Spinner className="h-4 w-4" /> : 'Approve All'}
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setShowBulkRejectDialog(true)}
                disabled={loading || bulkApproving || bulkRejecting}
                className="bg-red-600 hover:bg-red-700"
              >
                {bulkRejecting ? <Spinner className="h-4 w-4" /> : 'Reject All'}
              </Button>
            </>
          )}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onLoad({ status, sourceType })}
            disabled={loading}
          >
            {loading ? <Spinner className="h-4 w-4" /> : 'Refresh'}
          </Button>
        </div>
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
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">
              Showing <strong>{records.length}</strong> {status} record(s)
              {sourceType && <span> from {sourceType}</span>}
              — bulk actions will affect <strong>all matching records in database</strong>
            </p>
          </div>
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

      {showBulkApproveDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg bg-white shadow-lg">
            <div className="border-b border-slate-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-slate-900">Approve all {status} records?</h3>
            </div>
            <div className="space-y-4 px-6 py-4">
              <p className="text-sm text-slate-600">
                This will approve and lock <strong>all {status} records</strong> in the database (displaying {records.length} on this page).
              </p>
              <p className="text-sm text-slate-500">
                This action cannot be undone. All records will be locked for audit.
              </p>
            </div>
            <div className="flex gap-3 border-t border-slate-200 px-6 py-4">
              <button
                type="button"
                onClick={() => setShowBulkApproveDialog(false)}
                disabled={bulkApproving}
                className="flex-1 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleBulkApprove}
                disabled={bulkApproving}
                className="flex-1 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {bulkApproving ? (
                  <>
                    <Spinner className="h-4 w-4" />
                    Approving...
                  </>
                ) : (
                  'Approve All'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {showBulkRejectDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg bg-white shadow-lg">
            <div className="border-b border-slate-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-slate-900">Reject all {status} records?</h3>
            </div>
            <div className="space-y-4 px-6 py-4">
              <p className="text-sm text-slate-600">
                This will reject and exclude <strong>all {status} records</strong> in the database (displaying {records.length} on this page).
              </p>
              <p className="text-sm text-slate-500">
                Rejected records will be locked and excluded from CO₂ calculations. This action cannot be undone.
              </p>
            </div>
            <div className="flex gap-3 border-t border-slate-200 px-6 py-4">
              <button
                type="button"
                onClick={() => setShowBulkRejectDialog(false)}
                disabled={bulkRejecting}
                className="flex-1 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleBulkReject}
                disabled={bulkRejecting}
                className="flex-1 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {bulkRejecting ? (
                  <>
                    <Spinner className="h-4 w-4" />
                    Rejecting...
                  </>
                ) : (
                  'Reject All'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}