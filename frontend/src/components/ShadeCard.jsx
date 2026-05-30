export default function ShadeCard({ skinAnalysis }) {
  const {
    hex_color, shade_name, shade_code, undertone, undertone_description,
    confidence, ml_skin_tone, lighting_quality,
    capture_quality, sample_quality,
  } = skinAnalysis

  // Determine undertone badge color
  const undertoneColors = {
    'warm': 'bg-amber-100 text-amber-800',
    'cool': 'bg-blue-100 text-blue-800',
    'neutral': 'bg-gray-100 text-gray-700',
    'neutral-warm': 'bg-amber-50 text-amber-700',
    'neutral-cool': 'bg-blue-50 text-blue-700',
  }

  const badgeColor = undertoneColors[undertone] || 'bg-gray-100 text-gray-700'

  return (
    <div className="rounded-lg bg-white/85 border border-blush/15 p-6 sm:p-8 animate-fade-in-up">
      <h3 className="text-lg font-semibold text-charcoal mb-6">Skin analysis</h3>

      <div className="flex flex-col sm:flex-row items-center gap-6">
        {/* Color Swatch */}
        <div className="flex-shrink-0">
          <div
            className="w-28 h-28 rounded-lg shadow-lg border-4 border-white"
            style={{ backgroundColor: hex_color }}
          />
          <p className="text-center mt-2 text-xs font-mono text-charcoal-light">
            {hex_color}
          </p>
        </div>

        {/* Details */}
        <div className="flex-1 text-center sm:text-left">
          <h4 className="text-2xl font-bold text-charcoal font-serif">{shade_name}</h4>
          <p className="text-sm text-charcoal-light mb-3">Shade Code: {shade_code}</p>

          {/* Undertone Badge */}
          <div className="inline-flex items-center gap-2 mb-3">
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${badgeColor}`}>
              {undertone.charAt(0).toUpperCase() + undertone.slice(1)} Undertone
            </span>
            <span className="text-sm text-charcoal-light">
              {Math.round(confidence * 100)}% confidence
            </span>
          </div>

          {/* Description */}
          <p className="text-sm text-charcoal-light leading-relaxed">
            {undertone_description}
          </p>
        </div>
      </div>

      {/* ML Skin Tone Prediction */}
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

      {/* Lighting Quality */}
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
          <p className="text-xs text-charcoal-light leading-relaxed">
            {lighting_quality.message}
          </p>
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

      {/* Confidence Bar */}
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
