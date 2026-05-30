const HYDRATION_CONFIG = {
  good: { color: '#3B82F6', bg: 'bg-blue-100', label: 'Good' },
  moderate: { color: '#EAB308', bg: 'bg-yellow-100', label: 'Moderate' },
  low: { color: '#EF4444', bg: 'bg-red-100', label: 'Low' },
}

function CircularProgress({ score }) {
  const radius = 36
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="relative w-24 h-24 flex items-center justify-center">
      <svg className="w-24 h-24 -rotate-90" viewBox="0 0 80 80">
        <circle
          cx="40" cy="40" r={radius}
          fill="none"
          stroke="rgba(255,182,193,0.3)"
          strokeWidth="6"
        />
        <circle
          cx="40" cy="40" r={radius}
          fill="none"
          stroke="url(#progressGradient)"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000"
        />
        <defs>
          <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#D4AF37" />
            <stop offset="100%" stopColor="#FFB6C1" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold text-charcoal">{score}</span>
        <span className="text-[10px] text-charcoal-light">/ 100</span>
      </div>
    </div>
  )
}

export default function SkinHealth({ skinHealth }) {
  if (!skinHealth) return null

  const { hydration_estimate, evenness_score, tip } = skinHealth
  const hydration = HYDRATION_CONFIG[hydration_estimate] || HYDRATION_CONFIG.moderate

  return (
    <div className="rounded-lg bg-white/85 border border-blush/15 p-6 sm:p-8 animate-fade-in-up stagger-3">
      <h3 className="text-lg font-semibold text-charcoal mb-6">Skin health signals</h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Hydration */}
        <div className="flex items-center gap-4">
          <div className={`w-14 h-14 rounded-lg ${hydration.bg} flex items-center justify-center flex-shrink-0`}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill={hydration.color}>
              <path d="M12 2C12 2 5 10 5 15a7 7 0 0014 0C19 10 12 2 12 2z" />
            </svg>
          </div>
          <div>
            <p className="text-xs font-medium text-charcoal-light uppercase tracking-wider">
              Hydration
            </p>
            <p className="text-lg font-bold text-charcoal">{hydration.label}</p>
          </div>
        </div>

        {/* Evenness Score */}
        <div className="flex items-center gap-4">
          <CircularProgress score={evenness_score ?? 0} />
          <div>
            <p className="text-xs font-medium text-charcoal-light uppercase tracking-wider">
              Skin Evenness
            </p>
            <p className="text-sm text-charcoal-light">
              {evenness_score >= 80 ? 'Very even tone' :
               evenness_score >= 60 ? 'Fairly even' :
               'Some unevenness detected'}
            </p>
          </div>
        </div>
      </div>

      {/* Tip */}
      {tip && (
        <div className="mt-6 p-4 bg-gold-light/20 border border-gold/20 rounded-lg">
          <p className="text-sm text-charcoal leading-relaxed">
            <span className="font-semibold">Tip:</span> {tip}
          </p>
        </div>
      )}
    </div>
  )
}
