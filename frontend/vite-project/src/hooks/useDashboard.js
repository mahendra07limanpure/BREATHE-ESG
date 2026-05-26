import { useCallback, useEffect, useState } from 'react'
import { fetchCo2Summary, fetchDashboardStats } from '../api/client'

export function useDashboard() {
  const [stats, setStats] = useState(null)
  const [co2, setCo2] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [statsData, co2Data] = await Promise.all([
        fetchDashboardStats(),
        fetchCo2Summary(),
      ])
      setStats(statsData)
      setCo2(co2Data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { stats, co2, loading, error, refresh }
}
