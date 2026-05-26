import { useState } from 'react'
import { SOURCES } from '../../constants/sources'
import Alert from '../ui/Alert'
import Button from '../ui/Button'
import Card, { CardHeader } from '../ui/Card'
import Spinner from '../ui/Spinner'
import DropZone from './DropZone'
import SampleDatasetCard from './SampleDatasetCard'

export default function UploadView({
  loading,
  error,
  lastResult,
  onUpload,
  onUploadSample,
  onClearResult,
  onIngestSuccess,
}) {
  const [sourceType, setSourceType] = useState('')
  const [activeSample, setActiveSample] = useState(null)
  const [localMessage, setLocalMessage] = useState(null)

  const runUpload = async (file) => {
    if (!sourceType) {
      setLocalMessage({ type: 'error', text: 'Select a source type before uploading.' })
      return
    }
    setLocalMessage(null)
    onClearResult()
    try {
      const result = await onUpload(file, sourceType)
      setLocalMessage({
        type: 'success',
        text: `Ingested ${result.total_rows} rows — ${result.flagged_rows} flagged, ${result.pending_rows} pending.`,
      })
      onIngestSuccess?.()
    } catch {
      /* error set in hook */
    }
  }

  const runSample = async (id) => {
    setActiveSample(id)
    setLocalMessage(null)
    onClearResult()
    try {
      const result = await onUploadSample(id)
      setSourceType(id)
      setLocalMessage({
        type: 'success',
        text: `Sample ingested: ${result.total_rows} rows — ${result.flagged_rows} flagged.`,
      })
      onIngestSuccess?.()
    } catch {
      /* error set in hook */
    } finally {
      setActiveSample(null)
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
          Ingest data
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Upload client CSV exports or load a realistic sample file. All paths use the same
          backend parsers and flagging rules.
        </p>
      </div>

      {(error || localMessage) && (
        <div className="space-y-2">
          {error && (
            <Alert variant="error" title="Upload failed" onDismiss={onClearResult}>
              {error}
            </Alert>
          )}
          {localMessage?.type === 'success' && (
            <Alert variant="success" title="Ingestion complete">
              {localMessage.text}
            </Alert>
          )}
          {localMessage?.type === 'error' && (
            <Alert variant="warning">{localMessage.text}</Alert>
          )}
        </div>
      )}

      {lastResult && (
        <Card className="bg-slate-50">
          <CardHeader title="Last batch" />
          <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-slate-500">Batch ID</dt>
              <dd className="font-medium text-slate-900">#{lastResult.upload_batch_id}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Total rows</dt>
              <dd className="font-medium text-slate-900">{lastResult.total_rows}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Flagged</dt>
              <dd className="font-medium text-amber-700">{lastResult.flagged_rows}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Pending</dt>
              <dd className="font-medium text-slate-900">{lastResult.pending_rows}</dd>
            </div>
          </dl>
        </Card>
      )}

      <Card>
        <CardHeader
          title="Manual upload"
          description="Select the source system, then upload the CSV file from the client."
        />
        <div className="space-y-4">
          <div>
            <label htmlFor="sourceType" className="mb-1.5 block text-sm font-medium text-slate-700">
              Source type
            </label>
            <select
              id="sourceType"
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value)}
              disabled={loading}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 disabled:opacity-60"
            >
              <option value="">Select source…</option>
              {SOURCES.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label} ({s.scope})
                </option>
              ))}
            </select>
          </div>

          <DropZone onFileSelect={runUpload} disabled={loading} />

          {loading && (
            <div className="flex items-center justify-center gap-2 text-sm text-slate-500">
              <Spinner />
              Parsing and ingesting…
            </div>
          )}
        </div>
      </Card>

      <div>
        <h2 className="mb-1 text-lg font-semibold text-slate-900">Sample datasets</h2>
        <p className="mb-4 text-sm text-slate-500">
          One-click demo for reviewers. Sample files mirror real SAP MB51, MSEDCL-style utility,
          and Concur travel exports — same API as manual upload.
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {SOURCES.map((source) => (
            <SampleDatasetCard
              key={source.id}
              source={source}
              loading={loading}
              activeSource={activeSample}
              onLoadSample={runSample}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
