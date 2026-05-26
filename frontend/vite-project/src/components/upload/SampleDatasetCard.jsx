import Button from '../ui/Button'
import Card from '../ui/Card'
import Spinner from '../ui/Spinner'

const accentRing = {
  emerald: 'ring-emerald-100',
  sky: 'ring-sky-100',
  violet: 'ring-violet-100',
}

export default function SampleDatasetCard({
  source,
  loading,
  activeSource,
  onLoadSample,
}) {
  const isLoading = loading && activeSource === source.id

  return (
    <Card className={`ring-1 ${accentRing[source.accent] || 'ring-slate-100'}`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {source.scope}
          </p>
          <h3 className="mt-0.5 font-semibold text-slate-900">{source.label}</h3>
        </div>
      </div>
      <p className="mt-2 text-sm text-slate-500">{source.description}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          size="sm"
          onClick={() => onLoadSample(source.id)}
          disabled={loading}
        >
          {isLoading ? <Spinner className="h-4 w-4" /> : 'Load sample'}
        </Button>
        <a
          href={source.samplePath}
          download={source.sampleDownloadName}
          className="inline-flex items-center rounded-lg px-3 py-1.5 text-xs font-medium text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
        >
          Download CSV
        </a>
      </div>
    </Card>
  )
}
