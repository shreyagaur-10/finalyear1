import { useState } from 'react'

const API_URL = import.meta.env.PROD
  ? (import.meta.env.VITE_API_URL || '')
  : ''

// ── ShareCard ─────────────────────────────────────────────────────────────────

function ShareCard({ skinAnalysis, recommendations }) {
  const [copied, setCopied] = useState(false)

  const { hex_color, shade_name, undertone } = skinAnalysis
  const topProducts = (recommendations || []).slice(0, 3)

  const buildSummaryText = () => {
    let text = `ShadeSense AI Results\n\n`
    text += `Skin Shade: ${shade_name}\n`
    text += `Undertone: ${undertone}\n`
    text += `Color: ${hex_color}\n\n`
    if (topProducts.length > 0) {
      text += `Top Recommendations:\n`
      topProducts.forEach((p, i) => {
        text += `${i + 1}. ${p.brand} ${p.line}: ${p.shade_name} (${p.match_percentage}% match)\n`
      })
    }
    text += `\nFind your perfect shade at ShadeSense AI`
    return text
  }

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text || buildSummaryText())
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      console.error('Copy failed')
    }
  }

  const handleShare = async () => {
    const text = buildSummaryText()
    if (navigator.share) {
      try {
        await navigator.share({ title: 'My ShadeSense AI Results', text })
      } catch (err) {
        if (err.name !== 'AbortError') console.error('Share failed:', err)
      }
    } else {
      await copyToClipboard(text)
    }
  }

  return (
    <div className="rounded-lg bg-white/85 border border-blush/15 overflow-hidden animate-fade-in-up stagger-4">
      <div className="bg-charcoal p-5 text-cream">
        <div className="text-sm font-medium opacity-90">ShadeSense AI</div>
        <h3 className="text-lg font-bold mt-1">Shareable shade summary</h3>
      </div>
      <div className="p-6">
        <div className="flex items-center gap-4 mb-5">
          <div
            className="w-16 h-16 rounded-lg shadow-lg border-[3px] border-white shrink-0"
            style={{ backgroundColor: hex_color }}
          />
          <div>
            <p className="font-bold text-charcoal text-lg font-serif">{shade_name}</p>
            <p className="text-sm text-charcoal-light capitalize">{undertone} undertone</p>
            <p className="text-xs font-mono text-charcoal-light/60 mt-0.5">{hex_color}</p>
          </div>
        </div>

        {topProducts.length > 0 && (
          <div className="mb-5">
            <p className="text-xs font-semibold text-charcoal-light uppercase tracking-wider mb-3">Top Picks</p>
            <div className="space-y-2.5">
              {topProducts.map((p, i) => (
                <div key={p.id || i} className="flex items-center gap-3 p-2.5 bg-cream/70 border border-blush/10 rounded-lg">
                  <div className="w-8 h-8 rounded-lg border-2 border-white shadow-sm shrink-0" style={{ backgroundColor: p.hex_color }} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-charcoal truncate">{p.brand}: {p.shade_name}</p>
                    <p className="text-xs text-charcoal-light">{p.line}</p>
                  </div>
                  <span className="text-xs font-bold text-gold shrink-0">{p.match_percentage}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={handleShare}
            className="flex-1 py-3 rounded-xl font-semibold text-sm bg-charcoal text-white
              hover:shadow-lg hover:-translate-y-0.5 active:scale-[0.98]
              transition-all duration-300 cursor-pointer flex items-center justify-center gap-2"
          >
            {navigator.share ? 'Share results' : 'Copy summary'}
          </button>
          <button
            onClick={() => copyToClipboard()}
            className="py-3 px-4 rounded-lg font-semibold text-sm border border-blush/30 text-charcoal
              hover:border-blush hover:bg-blush-light/20 transition-all duration-300 cursor-pointer
              flex items-center justify-center gap-2"
          >
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── FeedbackPanel ─────────────────────────────────────────────────────────────

const MATCH_OPTIONS = [
  { value: 'good_match', label: 'Good match' },
  { value: 'too_light',  label: 'Too light' },
  { value: 'too_dark',   label: 'Too dark' },
  { value: 'too_warm',   label: 'Too warm' },
  { value: 'too_cool',   label: 'Too cool' },
]

function FeedbackPanel({ skinAnalysis, recommendations, sessionId }) {
  const [rating, setRating] = useState(5)
  const [actualMatch, setActualMatch] = useState('good_match')
  const [selectedProductId, setSelectedProductId] = useState(recommendations?.[0]?.id || '')
  const [correctedHex, setCorrectedHex] = useState('')
  const [notes, setNotes] = useState('')
  const [status, setStatus] = useState('idle')

  const submitFeedback = async () => {
    setStatus('saving')
    try {
      const response = await fetch(`${API_URL}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          skin_hex: skinAnalysis?.hex_color,
          predicted_shade: skinAnalysis?.shade_name,
          selected_product_id: selectedProductId || null,
          rating,
          actual_match: actualMatch,
          corrected_hex: correctedHex || null,
          notes: notes || null,
        }),
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Could not save feedback')
      }
      setStatus('saved')
    } catch (error) {
      console.error(error)
      setStatus('error')
    }
  }

  return (
    <div className="rounded-lg bg-white/85 border border-blush/15 p-6 animate-fade-in-up">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-charcoal-light">Learning loop</p>
          <h3 className="text-lg font-semibold text-charcoal">Help improve future matches</h3>
          <p className="text-sm text-charcoal-light mt-1">
            Real user corrections are stored as training signals for the recommendation engine.
          </p>
        </div>
        {status === 'saved' && (
          <span className="px-3 py-1 rounded-md bg-green-100 text-green-800 text-xs font-semibold">Feedback saved</span>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-xs font-semibold text-charcoal-light uppercase tracking-wide">Product tested</span>
          <select
            value={selectedProductId}
            onChange={(e) => setSelectedProductId(e.target.value)}
            className="mt-2 w-full rounded-lg border border-blush/20 bg-white px-3 py-2 text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-blush/40"
          >
            {(recommendations || []).map((product) => (
              <option key={product.id} value={product.id}>{product.brand} - {product.shade_name}</option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-xs font-semibold text-charcoal-light uppercase tracking-wide">Actual result</span>
          <select
            value={actualMatch}
            onChange={(e) => setActualMatch(e.target.value)}
            className="mt-2 w-full rounded-lg border border-blush/20 bg-white px-3 py-2 text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-blush/40"
          >
            {MATCH_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-xs font-semibold text-charcoal-light uppercase tracking-wide">Rating</span>
          <input
            type="range" min="1" max="5" value={rating}
            onChange={(e) => setRating(Number(e.target.value))}
            className="mt-3 w-full accent-[#2D2D2D]"
          />
          <span className="text-sm font-semibold text-charcoal">{rating}/5</span>
        </label>

        <label className="block">
          <span className="text-xs font-semibold text-charcoal-light uppercase tracking-wide">Corrected shade hex</span>
          <input
            value={correctedHex}
            onChange={(e) => setCorrectedHex(e.target.value)}
            placeholder="#C8A07A"
            className="mt-2 w-full rounded-lg border border-blush/20 bg-white px-3 py-2 text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-blush/40"
          />
        </label>
      </div>

      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Optional note: lighting, brand oxidation, neck match, undertone issue..."
        rows={3}
        className="mt-4 w-full rounded-lg border border-blush/20 bg-white px-3 py-2 text-sm text-charcoal resize-none focus:outline-none focus:ring-2 focus:ring-blush/40"
      />

      <button
        onClick={submitFeedback}
        disabled={status === 'saving' || status === 'saved'}
        className="mt-4 px-5 py-2.5 rounded-lg bg-charcoal text-white text-sm font-semibold disabled:opacity-60 disabled:cursor-not-allowed hover:-translate-y-0.5 transition-all"
      >
        {status === 'saving' ? 'Saving...' : status === 'saved' ? 'Saved' : 'Submit feedback'}
      </button>

      {status === 'error' && (
        <p className="mt-3 text-sm text-red-600">Could not save feedback. Check the corrected hex value and try again.</p>
      )}
    </div>
  )
}

// ── Combined footer ───────────────────────────────────────────────────────────

export default function ResultsFooter({ skinAnalysis, recommendations, sessionId }) {
  return (
    <>
      <ShareCard skinAnalysis={skinAnalysis} recommendations={recommendations} />
      <FeedbackPanel skinAnalysis={skinAnalysis} recommendations={recommendations} sessionId={sessionId} />
    </>
  )
}
