import { useCallback, useState } from 'react'

export default function DropZone({ onFileSelect, disabled, accept = '.csv' }) {
  const [dragOver, setDragOver] = useState(false)

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault()
      setDragOver(false)
      if (disabled) return
      const file = e.dataTransfer.files?.[0]
      if (file) onFileSelect(file)
    },
    [disabled, onFileSelect]
  )

  return (
    <label
      className={[
        'flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors',
        dragOver
          ? 'border-emerald-400 bg-emerald-50/50'
          : 'border-slate-200 bg-slate-50/50 hover:border-slate-300 hover:bg-slate-50',
        disabled ? 'cursor-not-allowed opacity-60' : '',
      ].join(' ')}
      onDragOver={(e) => {
        e.preventDefault()
        if (!disabled) setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      <svg
        className="mb-3 h-10 w-10 text-slate-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
        />
      </svg>
      <span className="text-sm font-medium text-slate-900">
        Drop CSV here or click to browse
      </span>
      <span className="mt-1 text-xs text-slate-500">SAP MB51, utility portal, or travel export</span>
      <input
        type="file"
        accept={accept}
        className="sr-only"
        disabled={disabled}
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) onFileSelect(file)
          e.target.value = ''
        }}
      />
    </label>
  )
}
