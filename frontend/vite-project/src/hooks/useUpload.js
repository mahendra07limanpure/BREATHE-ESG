import { useCallback, useState } from 'react'
import { loadSampleCsv, uploadCsv } from '../api/client'
import { SOURCE_BY_ID } from '../constants/sources'

export function useUpload() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastResult, setLastResult] = useState(null)

  const upload = useCallback(async (file, sourceType) => {
    setLoading(true)
    setError(null)
    setLastResult(null)
    try {
      const result = await uploadCsv(file, sourceType)
      setLastResult(result)
      return result
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const uploadSample = useCallback(async (sourceType) => {
    const source = SOURCE_BY_ID[sourceType]
    if (!source) {
      throw new Error('Unknown source type')
    }
    const file = await loadSampleCsv(source.samplePath, source.sampleDownloadName)
    return upload(file, sourceType)
  }, [upload])

  const clearResult = useCallback(() => {
    setLastResult(null)
    setError(null)
  }, [])

  return { loading, error, lastResult, upload, uploadSample, clearResult }
}
