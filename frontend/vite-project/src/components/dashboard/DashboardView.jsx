import Alert from '../ui/Alert'
import Button from '../ui/Button'
import Card from '../ui/Card'
import Spinner from '../ui/Spinner'
import { formatCo2, formatNumber } from '../../lib/format'
import ScopeBreakdown from './ScopeBreakdown'
import SourceBreakdown from './SourceBreakdown'
import StatCard from './StatCard'

export default function DashboardView({
  stats,
  co2,
  loading,
  error,
  onRefresh,
  onNavigate,
}) {
  if (loading && !stats) {
    return (
      <div className="flex min-h-[320px] items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            Emissions dashboard
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Monitor ingested activity, review queue, and approved CO₂ by GHG scope.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={onRefresh} disabled={loading}>
          {loading ? <Spinner /> : 'Refresh'}
        </Button>
      </div>

      {error && (
        <Alert variant="error" title="Could not load dashboard">
          {error}. Ensure the Django API is running on port 8000.
        </Alert>
      )}

      <Card className="border-emerald-200/60 bg-gradient-to-br from-emerald-50 to-white">
        <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">
          Approved emissions (audit-ready)
        </p>
        <p className="mt-2 text-4xl font-semibold tabular-nums text-slate-900 sm:text-5xl">
          {co2 ? formatCo2(co2.total_kg) : '—'}
        </p>
        {co2 && (
          <p className="mt-2 text-sm text-slate-600">
            {formatNumber(co2.total_tonnes, 2)} tonnes CO₂e · {co2.approved_records} approved rows
          </p>
        )}
      </Card>

      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <StatCard label="Total records" value={stats.total_records} />
          <StatCard label="Approved" value={stats.approved_records} accent="emerald" />
          <StatCard
            label="Pending review"
            value={stats.pending_records}
            accent="sky"
            subtext="Ready for bulk approval"
          />
          <StatCard
            label="Flagged"
            value={stats.flagged_records}
            accent="amber"
            subtext="Requires analyst attention"
          />
          <StatCard
            label="Rejected"
            value={stats.rejected_records}
            accent="rose"
            subtext="View audit trail"
          />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <ScopeBreakdown co2={co2} />
        <SourceBreakdown breakdown={stats?.source_breakdown} />
      </div>

      {stats && (stats.flagged_records > 0 || stats.pending_records > 0) && (
        <Card>
          <h2 className="text-base font-semibold text-slate-900">Analyst actions</h2>
          <p className="mt-1 text-sm text-slate-500">
            Review flagged rows individually. Approve clean pending rows in bulk from the review tab.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            {stats.flagged_records > 0 && (
              <Button onClick={() => onNavigate('review', { status: 'flagged' })}>
                Review {stats.flagged_records} flagged
              </Button>
            )}
            {stats.pending_records > 0 && (
              <Button
                variant="secondary"
                onClick={() => onNavigate('review', { status: 'pending' })}
              >
                Review {stats.pending_records} pending
              </Button>
            )}
            <Button variant="ghost" onClick={() => onNavigate('upload')}>
              Ingest more data
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}
