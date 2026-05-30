import { useState } from 'react'

// ── ShadeCard ────────────────────────────────────────────────────────────────

const UNDERTONE_COLORS = {
  'warm': 'bg-amber-100 text-amber-800',
  'cool': 'bg-blue-100 text-blue-800',
  'neutral': 'bg-gray-100 text-gray-700',
  'neutral-warm': 'bg-amber-50 text-amber-700',
  'neutral-cool': 'bg-blue-50 text-blue-700',
}

function ShadeCard({ skinAnalysis }) {
  const {
    hex_color, shade_name, shade_code, undertone, undertone_description,
    confidence, ml_skin_tone, lighting_quality, capture_quality, sample_quality,
  } = skinAnalysis

  const badgeColor = UNDERTONE_COLORS[undertone] || 'bg-gray-100 text-gray-700'

  return (
    <div className="rounded-lg bg-white/85 border border-blush/15 p-6 sm:p-8 animate-fade-in-up">
      <h3 className="text-lg font-semibold text-charcoal mb-6">Skin analysis</h3>

      <div className="flex flex-col sm:flex-row items-center gap-6">
        <div className="shrink-0">
          <div
            className="w-28 h-28 rounded-lg shadow-lg border-4 border-white"
            style={{ backgroundColor: hex_color }}
          />
          <p className="text-center mt-2 text-xs font-mono text-charcoal-light">{hex_color}</p>
        </div>

        <div className="flex-1 text-center sm:text-left">
          <h4 className="text-2xl font-bold text-charcoal font-serif">{shade_name}</h4>
          <p className="text-sm text-charcoal-light mb-3">Shade Code: {shade_code}</p>
          <div className="inline-flex items-center gap-2 mb-3">
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${badgeColor}`}>
              {undertone.charAt(0).toUpperCase() + undertone.slice(1)} Undertone
            </span>
            <span className="text-sm text-charcoal-light">
              {Math.round(confidence * 100)}% confidence
            </span>
          </div>
          <p className="text-sm text-charcoal-light leading-relaxed">{undertone_description}</p>
        </div>
      </div>

      {ml_skin_tone && (
        <div className="mt-6 pt-4 border-t border-blush/20">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-semibold text-charcoal">AI Skin Tone Analysis</span>
            <span className="ml-auto px-2 py-0.5 rounded-md text-xs font-medium bg-violet-100 text-violet-700">
              {ml_skin_tone.predicted_tone}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {Object.entries(ml_skin_tone.probabilities || {}).map(([tone, prob]) => (
              <div
                key={tone}
                className="min-w-0 rounded-lg bg-cream/60 border border-blush/10 p-2"
              >
                <div className="flex items-start justify-between gap-2 text-xs text-charcoal-light mb-2">
                  <span className="font-medium leading-tight break-words">{tone}</span>
                  <span className="shrink-0 font-semibold text-charcoal">{Math.round(prob * 100)}%</span>
                </div>
                <div className="h-1.5 bg-blush-light/30 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-1000"
                    style={{
                      width: `${Math.round(prob * 100)}%`,
                      backgroundColor: tone === ml_skin_tone.predicted_tone ? '#8b5cf6' : '#d4a5a5',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {lighting_quality && (
        <div className="mt-6 pt-4 border-t border-blush/20">
          <div className="flex items-center justify-between gap-3 mb-2">
            <span className="text-xs font-semibold text-charcoal">Photo Lighting Quality</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
              lighting_quality.label === 'good'
                ? 'bg-green-100 text-green-800'
                : lighting_quality.label === 'usable'
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-red-100 text-red-800'
            }`}>
              {lighting_quality.label} · {lighting_quality.score}%
            </span>
          </div>
          <p className="text-xs text-charcoal-light leading-relaxed">{lighting_quality.message}</p>
        </div>
      )}

      {(capture_quality || sample_quality) && (
        <div className="mt-6 pt-4 border-t border-blush/20 grid sm:grid-cols-2 gap-3">
          {capture_quality && (
            <div className="rounded-lg bg-cream/70 border border-blush/10 p-3">
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs font-semibold text-charcoal">Capture quality</span>
                <span className="text-xs font-semibold text-charcoal">{capture_quality.score}%</span>
              </div>
              <p className="mt-1 text-xs text-charcoal-light capitalize">{capture_quality.label}</p>
            </div>
          )}
          {sample_quality && (
            <div className="rounded-lg bg-cream/70 border border-blush/10 p-3">
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs font-semibold text-charcoal">Skin sample quality</span>
                <span className="text-xs font-semibold text-charcoal">{sample_quality.score}%</span>
              </div>
              <p className="mt-1 text-xs text-charcoal-light">
                {sample_quality.filtered_sample_count} usable pixels
              </p>
            </div>
          )}
        </div>
      )}

      <div className="mt-6 pt-4 border-t border-blush/20">
        <div className="flex items-center justify-between text-xs text-charcoal-light mb-2">
          <span>Analysis Confidence</span>
          <span className="font-semibold">{Math.round(confidence * 100)}%</span>
        </div>
        <div className="h-2 bg-blush-light/30 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blush to-gold rounded-full transition-all duration-1000"
            style={{ width: `${Math.round(confidence * 100)}%` }}
          />
        </div>
      </div>
    </div>
  )
}

// ── ColorPalette ─────────────────────────────────────────────────────────────

const JEWELRY_DISPLAY = {
  gold: { label: 'Gold' },
  silver: { label: 'Silver' },
  'rose gold': { label: 'Rose Gold' },
  all: { label: 'All Metals' },
}

function Swatch({ hex, strikeThrough = false }) {
  const [showCopied, setShowCopied] = useState(false)

  const handleClick = async () => {
    try {
      await navigator.clipboard.writeText(hex)
      setShowCopied(true)
      setTimeout(() => setShowCopied(false), 1200)
    } catch {
      // clipboard unavailable
    }
  }

  return (
    <div className="relative group">
      <button
        onClick={handleClick}
        className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg border-2 border-white shadow-md
          cursor-pointer transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
        style={{ backgroundColor: hex }}
      >
        {strikeThrough && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-full h-0.5 bg-red-500 rotate-45 rounded-full" />
          </div>
        )}
      </button>
      <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1
        bg-charcoal text-cream text-[10px] font-mono rounded-md
        opacity-0 group-hover:opacity-100 transition-opacity duration-200
        pointer-events-none whitespace-nowrap z-10">
        {hex}
      </div>
      {showCopied && (
        <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1
          bg-green-600 text-white text-[10px] font-medium rounded-md
          animate-fade-in whitespace-nowrap z-20">
          Copied!
        </div>
      )}
    </div>
  )
}

function ColorPalette({ colorHarmony }) {
  if (!colorHarmony) return null

  const { best_clothing_colors, best_jewelry, best_lip_colors, avoid_colors } = colorHarmony
  const jewelry = JEWELRY_DISPLAY[best_jewelry] || JEWELRY_DISPLAY.all

  return (
    <div className="rounded-lg bg-white/85 border border-blush/15 p-6 sm:p-8 animate-fade-in-up stagger-2">
      <h3 className="text-lg font-semibold text-charcoal mb-6">Color palette</h3>
      <div className="space-y-6">
        {best_clothing_colors?.length > 0 && (
          <div>
            <p className="text-sm font-medium text-charcoal mb-3">Clothing colors</p>
            <div className="flex flex-wrap gap-3">
              {best_clothing_colors.map((hex, i) => <Swatch key={i} hex={hex} />)}
            </div>
          </div>
        )}
        {best_lip_colors?.length > 0 && (
          <div>
            <p className="text-sm font-medium text-charcoal mb-3">Lip shades</p>
            <div className="flex flex-wrap gap-3">
              {best_lip_colors.map((hex, i) => <Swatch key={i} hex={hex} />)}
            </div>
          </div>
        )}
        {best_jewelry && (
          <div>
            <p className="text-sm font-medium text-charcoal mb-3">Jewelry</p>
            <div className="inline-flex items-center gap-2 px-4 py-2.5 bg-cream/70 border border-blush/10 rounded-lg">
              <span className="text-sm font-semibold text-charcoal">{jewelry.label}</span>
            </div>
          </div>
        )}
        {avoid_colors?.length > 0 && (
          <div>
            <p className="text-sm font-medium text-charcoal mb-3">Lower harmony colors</p>
            <div className="flex flex-wrap gap-3">
              {avoid_colors.map((hex, i) => <Swatch key={i} hex={hex} strikeThrough />)}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── SkinToneViz ──────────────────────────────────────────────────────────────

const FITZPATRICK_SCALE = [
  { type: 'I',   label: 'Very Light', color: '#FDDCB5' },
  { type: 'II',  label: 'Light',      color: '#E8B88A' },
  { type: 'III', label: 'Medium',     color: '#C8956C' },
  { type: 'IV',  label: 'Olive',      color: '#A0714F' },
  { type: 'V',   label: 'Brown',      color: '#6B4226' },
  { type: 'VI',  label: 'Dark',       color: '#3B2210' },
]

function getFitzpatrickType(lum) {
  if (lum > 200) return 1
  if (lum >= 185) return 2
  if (lum >= 155) return 3
  if (lum >= 125) return 4
  if (lum >= 80)  return 5
  return 6
}

function SkinToneViz({ hexColor, luminance, shadeName }) {
  const fitzType = getFitzpatrickType(luminance)
  const markerPosition = Math.max(2, Math.min(98, 100 - (luminance / 255) * 100))

  return (
    <div className="glass rounded-2xl p-6 sm:p-8 animate-fade-in-up stagger-2">
      <h3 className="text-lg font-semibold text-charcoal mb-6 flex items-center gap-2">
        <span className="text-xl">🌈</span> Skin Tone Spectrum
      </h3>

      <div className="mb-8">
        <div className="relative">
          <div
            className="h-6 rounded-full shadow-inner"
            style={{ background: 'linear-gradient(to right, #FDDCB5, #E8B88A, #C8956C, #A0714F, #6B4226, #3B2210)' }}
          />
          <div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 transition-all duration-700"
            style={{ left: `${markerPosition}%` }}
          >
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 rounded-full border-[3px] border-white shadow-lg -mb-1" style={{ backgroundColor: hexColor }} />
              <div className="w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-l-transparent border-r-transparent border-t-white" />
            </div>
          </div>
        </div>
        <div className="flex justify-between mt-2 text-[10px] text-charcoal-light">
          <span>Light</span>
          <span>Dark</span>
        </div>
      </div>

      <div>
        <p className="text-sm font-medium text-charcoal mb-3">
          Fitzpatrick Scale <span className="text-gold font-semibold">Type {FITZPATRICK_SCALE[fitzType - 1].type}</span>
        </p>
        <div className="grid grid-cols-6 gap-2">
          {FITZPATRICK_SCALE.map((item, i) => {
            const isActive = i + 1 === fitzType
            return (
              <div
                key={item.type}
                className={`flex flex-col items-center p-2 rounded-xl transition-all duration-300 ${
                  isActive ? 'ring-2 ring-gold bg-gold-light/20 scale-105' : 'opacity-60 hover:opacity-80'
                }`}
              >
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg shadow-md border-2 border-white mb-1.5" style={{ backgroundColor: item.color }} />
                <span className={`text-xs font-bold ${isActive ? 'text-charcoal' : 'text-charcoal-light'}`}>{item.type}</span>
                <span className="text-[9px] text-charcoal-light hidden sm:block">{item.label}</span>
              </div>
            )
          })}
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-blush/20 flex items-center gap-3">
        <div className="w-5 h-5 rounded-full border-2 border-white shadow-sm" style={{ backgroundColor: hexColor }} />
        <p className="text-sm text-charcoal-light">
          Your shade: <span className="font-semibold text-charcoal">{shadeName}</span>
          <span className="ml-2 text-xs text-charcoal-light/60">(Luminance: {Math.round(luminance)})</span>
        </p>
      </div>
    </div>
  )
}

// ── SkinHealth ───────────────────────────────────────────────────────────────

const HYDRATION_CONFIG = {
  good:     { color: '#3B82F6', bg: 'bg-blue-100',   label: 'Good' },
  moderate: { color: '#EAB308', bg: 'bg-yellow-100', label: 'Moderate' },
  low:      { color: '#EF4444', bg: 'bg-red-100',    label: 'Low' },
}

function CircularProgress({ score }) {
  const radius = 36
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="relative w-24 h-24 flex items-center justify-center">
      <svg className="w-24 h-24 -rotate-90" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r={radius} fill="none" stroke="rgba(255,182,193,0.3)" strokeWidth="6" />
        <circle
          cx="40" cy="40" r={radius} fill="none"
          stroke="url(#progressGradient)" strokeWidth="6"
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

function SkinHealth({ skinHealth }) {
  if (!skinHealth) return null
  const { hydration_estimate, evenness_score, tip } = skinHealth
  const hydration = HYDRATION_CONFIG[hydration_estimate] || HYDRATION_CONFIG.moderate

  return (
    <div className="rounded-lg bg-white/85 border border-blush/15 p-6 sm:p-8 animate-fade-in-up stagger-3">
      <h3 className="text-lg font-semibold text-charcoal mb-6">Skin health signals</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="flex items-center gap-4">
          <div className={`w-14 h-14 rounded-lg ${hydration.bg} flex items-center justify-center shrink-0`}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill={hydration.color}>
              <path d="M12 2C12 2 5 10 5 15a7 7 0 0014 0C19 10 12 2 12 2z" />
            </svg>
          </div>
          <div>
            <p className="text-xs font-medium text-charcoal-light uppercase tracking-wider">Hydration</p>
            <p className="text-lg font-bold text-charcoal">{hydration.label}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <CircularProgress score={evenness_score ?? 0} />
          <div>
            <p className="text-xs font-medium text-charcoal-light uppercase tracking-wider">Skin Evenness</p>
            <p className="text-sm text-charcoal-light">
              {evenness_score >= 80 ? 'Very even tone' : evenness_score >= 60 ? 'Fairly even' : 'Some unevenness detected'}
            </p>
          </div>
        </div>
      </div>
      {tip && (
        <div className="mt-6 p-4 bg-gold-light/20 border border-gold/20 rounded-lg">
          <p className="text-sm text-charcoal leading-relaxed"><span className="font-semibold">Tip:</span> {tip}</p>
        </div>
      )}
    </div>
  )
}

// ── Combined panel ────────────────────────────────────────────────────────────

export default function SkinAnalysisPanel({ skinAnalysis }) {
  return (
    <>
      <ShadeCard skinAnalysis={skinAnalysis} />
      <ColorPalette colorHarmony={skinAnalysis?.color_harmony} />
      {skinAnalysis?.luminance != null && (
        <SkinToneViz
          hexColor={skinAnalysis.hex_color}
          luminance={skinAnalysis.luminance}
          shadeName={skinAnalysis.shade_name}
        />
      )}
      <SkinHealth skinHealth={skinAnalysis?.skin_health_indicators} />
    </>
  )
}
