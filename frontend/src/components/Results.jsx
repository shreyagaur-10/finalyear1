import { useState } from 'react'
import ShadeCard from './ShadeCard'
import ColorPalette from './ColorPalette'
import SkinToneViz from './SkinToneViz'
import SkinHealth from './SkinHealth'
import LookGuide from './LookGuide'
import ProductCard from './ProductCard'
import ShareCard from './ShareCard'
import FeedbackPanel from './FeedbackPanel'

const CATEGORY_TABS = [
  { key: 'all', label: 'All' },
  { key: 'foundation', label: 'Foundation' },
  { key: 'lipstick', label: 'Lipstick' },
  { key: 'blush', label: 'Blush' },
  { key: 'concealer', label: 'Concealer' },
]

export default function Results({ data, imageFile, onTryOn, sessionId }) {
  const { skin_analysis, recommendations, style_tips, intent } = data
  const [activeTab, setActiveTab] = useState('all')

  const filteredProducts = activeTab === 'all'
    ? recommendations
    : (recommendations || []).filter(
        (p) => (p.type || '').toLowerCase() === activeTab
      )

  return (
    <div className="space-y-8">
      {/* Section Title */}
      <div className="animate-fade-in rounded-lg bg-white/85 border border-blush/15 p-5 sm:p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-charcoal-light">Analysis complete</p>
            <h2 className="text-2xl sm:text-3xl font-bold font-serif text-charcoal">
              Your shade profile
            </h2>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="rounded-lg bg-cream/70 border border-blush/10 px-3 py-2">
              <p className="text-xs text-charcoal-light">Shade</p>
              <p className="text-sm font-semibold text-charcoal truncate">{skin_analysis?.shade_name}</p>
            </div>
            <div className="rounded-lg bg-cream/70 border border-blush/10 px-3 py-2">
              <p className="text-xs text-charcoal-light">Undertone</p>
              <p className="text-sm font-semibold text-charcoal capitalize truncate">{skin_analysis?.undertone}</p>
            </div>
            <div className="rounded-lg bg-cream/70 border border-blush/10 px-3 py-2">
              <p className="text-xs text-charcoal-light">Confidence</p>
              <p className="text-sm font-semibold text-charcoal">{Math.round((skin_analysis?.confidence || 0) * 100)}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Shade Analysis Card */}
      <ShadeCard skinAnalysis={skin_analysis} />

      {/* Color Harmony Palette */}
      <ColorPalette colorHarmony={skin_analysis?.color_harmony} />

      {/* Skin Tone Visualization */}
      {skin_analysis?.luminance != null && (
        <SkinToneViz
          hexColor={skin_analysis.hex_color}
          luminance={skin_analysis.luminance}
          shadeName={skin_analysis.shade_name}
        />
      )}

      {/* Skin Health Dashboard */}
      <SkinHealth skinHealth={skin_analysis?.skin_health_indicators} />

      {/* Detected Preferences */}
      {intent?.preferences_detected && (
        <div className="rounded-lg bg-white/85 border border-blush/15 p-5 animate-fade-in-up stagger-2">
          <h3 className="text-base font-semibold text-charcoal mb-3">Detected preferences</h3>
          <div className="flex flex-wrap gap-2">
            <span className="px-3 py-1.5 bg-cream/80 rounded-lg border border-blush/10 text-sm font-medium text-charcoal capitalize">
              {intent.occasion}
            </span>
            <span className="px-3 py-1.5 bg-cream/80 rounded-lg border border-blush/10 text-sm font-medium text-charcoal capitalize">
              {intent.look} look
            </span>
            <span className="px-3 py-1.5 bg-cream/80 rounded-lg border border-blush/10 text-sm font-medium text-charcoal capitalize">
              {intent.coverage} coverage
            </span>
            <span className="px-3 py-1.5 bg-cream/80 rounded-lg border border-blush/10 text-sm font-medium text-charcoal capitalize">
              {intent.finish} finish
            </span>
          </div>
        </div>
      )}

      {/* Complete Look Guide */}
      {data.complete_look && (
        <LookGuide completeLook={data.complete_look} />
      )}

      {/* Product Recommendations */}
      <div className="animate-fade-in-up stagger-3">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3 mb-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-charcoal-light">Ranked catalog</p>
            <h3 className="text-xl font-semibold text-charcoal">Recommended products</h3>
          </div>
          <p className="text-sm text-charcoal-light">Sorted by shade distance, undertone, finish, and coverage.</p>
        </div>

        {/* Category Tabs */}
        <div className="inline-flex flex-wrap gap-1 mb-6 p-1 rounded-lg bg-white/80 border border-blush/15">
          {CATEGORY_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-all duration-200 cursor-pointer
                ${activeTab === tab.key
                  ? 'bg-charcoal text-white shadow-sm'
                  : 'text-charcoal-light hover:text-charcoal hover:bg-cream'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {filteredProducts && filteredProducts.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredProducts.map((product, i) => (
              <ProductCard
                key={product.id}
                product={product}
                index={i}
                onTryOn={imageFile ? () => onTryOn(product) : undefined}
                skinHex={skin_analysis?.hex_color}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-8 bg-white/85 border border-blush/15 rounded-lg">
            <p className="text-charcoal-light">
              {activeTab === 'all'
                ? 'No matching products found. Try a different photo or preference.'
                : `No ${activeTab} matches found. Try the "All" tab to see other recommendations.`}
            </p>
          </div>
        )}
      </div>

      {/* Share Card */}
      <ShareCard skinAnalysis={skin_analysis} recommendations={recommendations} />

      <FeedbackPanel
        skinAnalysis={skin_analysis}
        recommendations={recommendations}
        sessionId={sessionId}
      />

      {/* Style Tips */}
      {style_tips && style_tips.length > 0 && (
        <div className="rounded-lg bg-white/85 border border-blush/15 p-6 animate-fade-in-up stagger-4">
          <h3 className="text-lg font-semibold text-charcoal mb-4">Application tips</h3>
          <ul className="space-y-3">
            {style_tips.map((tip, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-charcoal-light leading-relaxed">
                <span className="text-gold mt-0.5 flex-shrink-0">•</span>
                {tip}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-center text-xs text-charcoal-light/60 pt-4">
        Results are AI generated and may vary. We recommend testing products in store when possible.
        Shade matches are based on image analysis and may be affected by lighting conditions.
      </p>
    </div>
  )
}
