import { useState } from 'react'

const API_URL = import.meta.env.PROD
  ? (import.meta.env.VITE_API_URL || '')
  : ''

const MATCH_OPTIONS = [
  { value: 'good_match', label: 'Good match' },
  { value: 'too_light', label: 'Too light' },
  { value: 'too_dark', label: 'Too dark' },
  { value: 'too_warm', label: 'Too warm' },
  { value: 'too_cool', label: 'Too cool' },
]

export default function FeedbackPanel({ skinAnalysis, recommendations, sessionId }) {
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
          <span className="px-3 py-1 rounded-md bg-green-100 text-green-800 text-xs font-semibold">
            Feedback saved
          </span>
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
              <option key={product.id} value={product.id}>
                {product.brand} - {product.shade_name}
              </option>
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
            type="range"
            min="1"
            max="5"
            value={rating}
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
