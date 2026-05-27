import { useEffect, useState } from 'react'
import Button from '../ui/Button'
import Card from '../ui/Card'
import Spinner from '../ui/Spinner'
import Alert from '../ui/Alert'
import { formatNumber } from '../../lib/format'
import * as client from '../../api/client'

export default function AuditReportView() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadReport()
  }, [])

  const loadReport = async () => {
    try {
      setLoading(true)
      const data = await client.getAuditReport()
      setReport(data)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load audit report')
    } finally {
      setLoading(false)
    }
  }

  const downloadCsv = () => {
    if (!report?.rejected_details) return

    // Prepare CSV content
    const headers = [
      'Record ID',
      'Source',
      'Activity Type',
      'Date',
      'Quantity',
      'Unit',
      'CO2 (kg)',
      'Flag Reason',
      'Rejected At',
    ]
    const rows = report.rejected_details.map((r) => [
      r.id,
      r.source_type,
      r.activity_type,
      r.record_date,
      r.quantity_normalised,
      r.unit_normalised,
      r.co2_kg,
      r.flag_reason || '—',
      r.updated_at || '—',
    ])

    const csv = [headers, ...rows]
      .map((row) => row.map((cell) => `"${cell}"`).join(','))
      .join('\n')

    // Download
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit_report_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  if (loading) {
    return (
      <div className="flex min-h-[320px] items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="error" title="Failed to load audit report">
        {error}
      </Alert>
    )
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            Audit Report
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            View all record statuses, rejected entries, and upload history.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={downloadCsv}>
            Export CSV
          </Button>
          <Button onClick={loadReport}>Refresh</Button>
        </div>
      </div>

      {report?.summary && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Card className="border-slate-200 bg-slate-50">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-600">Total</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">
              {formatNumber(report.summary.total_records)}
            </p>
          </Card>
          <Card className="border-emerald-200 bg-emerald-50">
            <p className="text-xs font-medium uppercase tracking-wide text-emerald-600">Approved</p>
            <p className="mt-2 text-2xl font-semibold text-emerald-900">
              {formatNumber(report.summary.approved_records)}
            </p>
          </Card>
          <Card className="border-sky-200 bg-sky-50">
            <p className="text-xs font-medium uppercase tracking-wide text-sky-600">Pending</p>
            <p className="mt-2 text-2xl font-semibold text-sky-900">
              {formatNumber(report.summary.pending_records)}
            </p>
          </Card>
          <Card className="border-amber-200 bg-amber-50">
            <p className="text-xs font-medium uppercase tracking-wide text-amber-600">Flagged</p>
            <p className="mt-2 text-2xl font-semibold text-amber-900">
              {formatNumber(report.summary.flagged_records)}
            </p>
          </Card>
          <Card className="border-rose-200 bg-rose-50">
            <p className="text-xs font-medium uppercase tracking-wide text-rose-600">Rejected</p>
            <p className="mt-2 text-2xl font-semibold text-rose-900">
              {formatNumber(report.summary.rejected_records)}
            </p>
          </Card>
        </div>
      )}

      {report?.rejected_details && report.rejected_details.length > 0 && (
        <Card>
          <h2 className="text-base font-semibold text-slate-900">Rejected Records ({report.rejected_details.length})</h2>
          <p className="mt-1 text-sm text-slate-500">
            All records marked as rejected are excluded from CO₂ calculations.
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-200 bg-slate-50">
                <tr>
                  <th className="px-4 py-2 text-left font-semibold text-slate-600">ID</th>
                  <th className="px-4 py-2 text-left font-semibold text-slate-600">Source</th>
                  <th className="px-4 py-2 text-left font-semibold text-slate-600">Type</th>
                  <th className="px-4 py-2 text-left font-semibold text-slate-600">Date</th>
                  <th className="px-4 py-2 text-right font-semibold text-slate-600">CO₂ (kg)</th>
                  <th className="px-4 py-2 text-left font-semibold text-slate-600">Reason</th>
                  <th className="px-4 py-2 text-left font-semibold text-slate-600">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {report.rejected_details.map((record) => (
                  <tr key={record.id} className="hover:bg-slate-50">
                    <td className="px-4 py-2 text-slate-900 font-mono text-xs">#{record.id}</td>
                    <td className="px-4 py-2">
                      <span className="inline-block rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                        {record.source_type}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-slate-600">{record.activity_type}</td>
                    <td className="px-4 py-2 text-slate-600 text-xs">
                      {new Date(record.record_date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2 text-right text-slate-900 font-semibold">
                      {formatNumber(record.co2_kg, 1)}
                    </td>
                    <td className="px-4 py-2 text-slate-600">{record.flag_reason || '—'}</td>
                    <td className="px-4 py-2 text-slate-500 text-xs">
                      {record.updated_at
                        ? new Date(record.updated_at).toLocaleString()
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {report?.upload_batches && report.upload_batches.length > 0 && (
        <Card>
          <h2 className="text-base font-semibold text-slate-900">Upload History ({report.upload_batches.length})</h2>
          <p className="mt-1 text-sm text-slate-500">
            Chronological list of all data ingestion events.
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-200 bg-slate-50">
                <tr>
                  <th className="px-4 py-2 text-left font-semibold text-slate-600">Date/Time</th>
                  <th className="px-4 py-2 text-left font-semibold text-slate-600">Source</th>
                  <th className="px-4 py-2 text-right font-semibold text-slate-600">Rows</th>
                  <th className="px-4 py-2 text-right font-semibold text-slate-600">Flagged</th>
                  <th className="px-4 py-2 text-left font-semibold text-slate-600">Uploaded By</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {report.upload_batches.map((batch) => (
                  <tr key={batch.id} className="hover:bg-slate-50">
                    <td className="px-4 py-2 text-slate-600 text-xs whitespace-nowrap">
                      {new Date(batch.uploaded_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-2">
                      <span className="inline-block rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                        {batch.source_type}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right text-slate-900 font-semibold">
                      {formatNumber(batch.total_rows)}
                    </td>
                    <td className="px-4 py-2 text-right text-amber-600 font-semibold">
                      {formatNumber(batch.flagged_rows)}
                    </td>
                    <td className="px-4 py-2 text-slate-600 text-xs">{batch.uploaded_by}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
