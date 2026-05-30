import { useState } from 'react'

export default function ShareCard({ skinAnalysis, recommendations }) {
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

  const handleShare = async () => {
    const text = buildSummaryText()

    if (navigator.share) {
      try {
        await navigator.share({
          title: 'My ShadeSense AI Results',
          text,
        })
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Share failed:', err)
        }
      }
    } else {
      await copyToClipboard(text)
    }
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

  return (
    <div className="rounded-lg bg-white/85 border border-blush/15 overflow-hidden animate-fade-in-up stagger-4">
      <div className="bg-charcoal p-5 text-cream">
        <div className="text-sm font-medium opacity-90">
          ShadeSense AI
        </div>
        <h3 className="text-lg font-bold mt-1">Shareable shade summary</h3>
      </div>

      <div className="p-6">
        {/* Shade info */}
        <div className="flex items-center gap-4 mb-5">
          <div
            className="w-16 h-16 rounded-lg shadow-lg border-[3px] border-white flex-shrink-0"
            style={{ backgroundColor: hex_color }}
          />
          <div>
            <p className="font-bold text-charcoal text-lg font-serif">{shade_name}</p>
            <p className="text-sm text-charcoal-light capitalize">{undertone} undertone</p>
            <p className="text-xs font-mono text-charcoal-light/60 mt-0.5">{hex_color}</p>
          </div>
        </div>

        {/* Top 3 products */}
        {topProducts.length > 0 && (
          <div className="mb-5">
            <p className="text-xs font-semibold text-charcoal-light uppercase tracking-wider mb-3">
              Top Picks
            </p>
            <div className="space-y-2.5">
              {topProducts.map((p, i) => (
                <div key={p.id || i} className="flex items-center gap-3 p-2.5 bg-cream/70 border border-blush/10 rounded-lg">
                  <div
                    className="w-8 h-8 rounded-lg border-2 border-white shadow-sm flex-shrink-0"
                    style={{ backgroundColor: p.hex_color }}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-charcoal truncate">
                      {p.brand}: {p.shade_name}
                    </p>
                    <p className="text-xs text-charcoal-light">{p.line}</p>
                  </div>
                  <span className="text-xs font-bold text-gold flex-shrink-0">
                    {p.match_percentage}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleShare}
            className="flex-1 py-3 rounded-xl font-semibold text-sm
              bg-charcoal text-white
              hover:shadow-lg hover:-translate-y-0.5 active:scale-[0.98]
              transition-all duration-300 cursor-pointer
              flex items-center justify-center gap-2"
          >
            {navigator.share ? 'Share results' : 'Copy summary'}
          </button>

          <button
            onClick={() => copyToClipboard()}
            className="py-3 px-4 rounded-lg font-semibold text-sm
              border border-blush/30 text-charcoal
              hover:border-blush hover:bg-blush-light/20
              transition-all duration-300 cursor-pointer
              flex items-center justify-center gap-2"
          >
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      </div>
    </div>
  )
}
