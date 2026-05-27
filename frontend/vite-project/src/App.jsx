import { useCallback, useState } from 'react'
import AppShell from './components/layout/AppShell'
import DashboardView from './components/dashboard/DashboardView'
import UploadView from './components/upload/UploadView'
import ReviewView from './components/review/ReviewView'
import AuditReportView from './components/audit/AuditReportView'
import { useDashboard } from './hooks/useDashboard'
import { useRecords } from './hooks/useRecords'
import { useUpload } from './hooks/useUpload'

export default function App() {
  const [activeView, setActiveView] = useState('dashboard')
  const [reviewPrefs, setReviewPrefs] = useState({ status: 'flagged', source: '' })

  const { stats, co2, loading: dashLoading, error: dashError, refresh: refreshDashboard } =
    useDashboard()
  const { records, loading: recordsLoading, error: recordsError, actionId, load, approve, bulkApprove, bulkReject, reject } =
    useRecords()
  const { loading: uploadLoading, error: uploadError, lastResult, upload, uploadSample, clearResult } =
    useUpload()

  const navigate = useCallback((view, prefs) => {
    setActiveView(view)
    if (prefs?.status !== undefined || prefs?.source !== undefined) {
      setReviewPrefs({
        status: prefs.status ?? 'flagged',
        source: prefs.source ?? '',
      })
    }
  }, [])

  const handleIngestSuccess = useCallback(() => {
    refreshDashboard()
    setReviewPrefs({ status: 'flagged', source: '' })
  }, [refreshDashboard])

  const handleRecordAction = useCallback(async () => {
    await refreshDashboard()
  }, [refreshDashboard])

  const wrappedApprove = useCallback(
    async (id) => {
      const ok = await approve(id)
      if (ok) await handleRecordAction()
      return ok
    },
    [approve, handleRecordAction]
  )

  const wrappedReject = useCallback(
    async (id) => {
      const ok = await reject(id)
      if (ok) await handleRecordAction()
      return ok
    },
    [reject, handleRecordAction]
  )

  const wrappedBulkApprove = useCallback(
    async (status) => {
      const result = await bulkApprove(status)
      if (result) await handleRecordAction()
      return result
    },
    [bulkApprove, handleRecordAction]
  )

  const wrappedBulkReject = useCallback(
    async (status) => {
      const result = await bulkReject(status)
      if (result) await handleRecordAction()
      return result
    },
    [bulkReject, handleRecordAction]
  )

  return (
    <AppShell
      activeView={activeView}
      onNavigate={navigate}
      flaggedCount={stats?.flagged_records ?? 0}
    >
      {activeView === 'dashboard' && (
        <DashboardView
          stats={stats}
          co2={co2}
          loading={dashLoading}
          error={dashError}
          onRefresh={refreshDashboard}
          onNavigate={navigate}
        />
      )}

      {activeView === 'upload' && (
        <UploadView
          loading={uploadLoading}
          error={uploadError}
          lastResult={lastResult}
          onUpload={upload}
          onUploadSample={uploadSample}
          onClearResult={clearResult}
          onIngestSuccess={handleIngestSuccess}
        />
      )}

      {activeView === 'review' && (
        <ReviewView
          records={records}
          loading={recordsLoading}
          error={recordsError}
          actionId={actionId}
          initialStatus={reviewPrefs.status}
          initialSource={reviewPrefs.source}
          onLoad={load}
          onApprove={wrappedApprove}
          onBulkApprove={wrappedBulkApprove}
          onBulkReject={wrappedBulkReject}
          onReject={wrappedReject}
        />
      )}

      {activeView === 'audit' && <AuditReportView />}
    </AppShell>
  )
}
