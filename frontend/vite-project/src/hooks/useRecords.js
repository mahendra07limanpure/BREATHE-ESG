import { useCallback, useState } from 'react'
import { approveRecord, approveAllRecords, rejectAllRecords, fetchRecords, rejectRecord } from '../api/client'

export function useRecords() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [actionId, setActionId] = useState(null)

  const load = useCallback(async ({ sourceType = '', status = 'pending', limit = 1000 } = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchRecords({ sourceType, status, limit })
      setRecords(data.records || [])
      return data.records || []
    } catch (err) {
      setError(err.message)
      setRecords([])
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  const approve = useCallback(async (recordId) => {
    setActionId(recordId)
    try {
      await approveRecord(recordId)
      setRecords((prev) => prev.filter((r) => r.id !== recordId))
      return true
    } catch (err) {
      setError(err.message)
      return false
    } finally {
      setActionId(null)
    }
  }, [])

  const bulkApprove = useCallback(async (status = 'pending') => {
    setLoading(true)
    setError(null)
    try {
      const result = await approveAllRecords(status)
      setRecords([])  // Clear the list after bulk approval
      return result
    } catch (err) {
      setError(err.message)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const bulkReject = useCallback(async (status = 'flagged') => {
    setLoading(true)
    setError(null)
    try {
      const result = await rejectAllRecords(status)
      setRecords([])  // Clear the list after bulk rejection
      return result
    } catch (err) {
      setError(err.message)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const reject = useCallback(async (recordId) => {
    setActionId(recordId)
    try {
      await rejectRecord(recordId)
      setRecords((prev) => prev.filter((r) => r.id !== recordId))
      return true
    } catch (err) {
      setError(err.message)
      return false
    } finally {
      setActionId(null)
    }
  }, [])

  return { records, loading, error, actionId, load, approve, bulkApprove, bulkReject, reject }
}
