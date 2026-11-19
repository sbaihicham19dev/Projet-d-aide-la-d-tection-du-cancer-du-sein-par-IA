import { createContext, useContext, useState, useRef, useCallback } from 'react'
import { analyzeMammography, analyzeGradcam } from './services/api'

const AnalysisContext = createContext(null)

export function AnalysisProvider({ children }) {
  const [result, setResult]                 = useState(null)
  const [loading, setLoading]               = useState(false)
  const [error, setError]                   = useState(null)
  const [preview, setPreview]               = useState(null)
  const [gradcam, setGradcam]               = useState(null)
  const [loadingGradcam, setLoadingGradcam] = useState(false)
  const [currentFile, setCurrentFile]       = useState(null)
  const [showGradcam, setShowGradcam]       = useState(false)
  const [progress, setProgress]             = useState(null)

  const abortRef = useRef(null)

  const startAnalysis = useCallback(async (file) => {
    if (!file || !file.type.startsWith('image/')) return
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()

    setLoading(true)
    setError(null)
    setResult(null)
    setGradcam(null)
    setShowGradcam(false)
    setProgress('detecting')
    setPreview(URL.createObjectURL(file))
    setCurrentFile(file)

    const steps = ['detecting', 'classifying', 'birads', 'narrative']
    let stepIdx = 0
    const stepTimer = setInterval(() => {
      stepIdx = Math.min(stepIdx + 1, steps.length - 1)
      setProgress(steps[stepIdx])
    }, 2500)

    try {
      const data = await analyzeMammography(file)
      clearInterval(stepTimer)
      setResult(data)
      setProgress(null)
    } catch (e) {
      clearInterval(stepTimer)
      if (e.name !== 'AbortError') {
        setError('Erreur de connexion au gateway :8080 — vérifiez que les services sont démarrés.')
      }
      setProgress(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const loadGradcam = useCallback(async () => {
    if (!currentFile) return
    setLoadingGradcam(true)
    setError(null)
    try {
      const html = await analyzeGradcam(currentFile)
      setGradcam(html)
      setShowGradcam(true)
    } catch {
      setError('Erreur Grad-CAM — vérifiez le service detection :8011')
    } finally {
      setLoadingGradcam(false)
    }
  }, [currentFile])

  const reset = useCallback(() => {
    if (abortRef.current) abortRef.current.abort()
    setResult(null)
    setPreview(null)
    setError(null)
    setGradcam(null)
    setCurrentFile(null)
    setShowGradcam(false)
    setProgress(null)
    setLoading(false)
  }, [])

  return (
    <AnalysisContext.Provider value={{
      result, loading, error, preview, gradcam,
      loadingGradcam, currentFile, showGradcam, progress,
      setShowGradcam, startAnalysis, loadGradcam, reset,
    }}>
      {children}
    </AnalysisContext.Provider>
  )
}

export function useAnalysis() {
  const ctx = useContext(AnalysisContext)
  if (!ctx) throw new Error('useAnalysis must be used inside AnalysisProvider')
  return ctx
}
