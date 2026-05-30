import { useState, useEffect, useRef } from 'react'

const STAGES = [
  { threshold: 0, message: 'Detecting face regions' },
  { threshold: 20, message: 'Extracting dominant skin color' },
  { threshold: 40, message: 'Checking undertone and lighting quality' },
  { threshold: 60, message: 'Ranking products by color distance' },
  { threshold: 80, message: 'Preparing explainable recommendations' },
]

export default function LoadingSpinner() {
  const [progress, setProgress] = useState(0)
  const rafRef = useRef(null)
  const startRef = useRef(null)

  useEffect(() => {
    startRef.current = performance.now()

    const animate = (now) => {
      const elapsed = now - startRef.current
      // Ease out — fast at first, slows toward 90%
      const raw = Math.min(90, (elapsed / 80) * (1 - elapsed / 20000))
      const value = Math.min(90, raw)
      setProgress(Math.max(0, Math.round(value)))
      if (value < 90) {
        rafRef.current = requestAnimationFrame(animate)
      }
    }

    rafRef.current = requestAnimationFrame(animate)
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  const currentStage = [...STAGES].reverse().find((s) => progress >= s.threshold) || STAGES[0]

  return (
    <div className="mt-10 flex flex-col items-center justify-center animate-fade-in">
      {/* Spinning shade wheel */}
      <div className="relative w-20 h-20 mb-6">
        <div className="absolute inset-0 rounded-full border-4 border-blush-light/50" />
        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-charcoal animate-spin-slow" />
        <div className="absolute inset-2 rounded-full bg-white flex items-center justify-center border border-blush/10">
          <span className="w-7 h-7 rounded-md" style={{ background: 'linear-gradient(135deg, #F5D6C3, #9A6242)' }} />
        </div>
      </div>

      <h3 className="text-lg font-semibold text-charcoal mb-2">Analyzing your shade profile</h3>

      {/* Stage message */}
      <p className="text-sm text-charcoal-light mb-4 animate-pulse-soft">
        {currentStage.message}
      </p>

      {/* Progress bar */}
      <div className="w-64 max-w-full">
        <div className="flex justify-between text-xs text-charcoal-light mb-1">
          <span>Progress</span>
          <span className="font-semibold">{progress}%</span>
        </div>
        <div className="h-1.5 bg-blush-light/30 rounded-full overflow-hidden">
          <div
            className="h-full bg-charcoal rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  )
}
