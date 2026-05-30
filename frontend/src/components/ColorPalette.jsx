import { useState } from 'react'

function Swatch({ hex, onCopy, strikeThrough = false }) {
  const [showCopied, setShowCopied] = useState(false)

  const handleClick = async () => {
    try {
      await navigator.clipboard.writeText(hex)
      setShowCopied(true)
      onCopy?.(hex)
      setTimeout(() => setShowCopied(false), 1200)
    } catch {
      // fallback: do nothing
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
      {/* CSS-only tooltip */}
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

const JEWELRY_DISPLAY = {
  gold: { label: 'Gold' },
  silver: { label: 'Silver' },
  'rose gold': { label: 'Rose Gold' },
  all: { label: 'All Metals' },
}

export default function ColorPalette({ colorHarmony }) {
  if (!colorHarmony) return null

  const { best_clothing_colors, best_jewelry, best_lip_colors, avoid_colors } = colorHarmony
  const jewelry = JEWELRY_DISPLAY[best_jewelry] || JEWELRY_DISPLAY.all

  return (
    <div className="rounded-lg bg-white/85 border border-blush/15 p-6 sm:p-8 animate-fade-in-up stagger-2">
      <h3 className="text-lg font-semibold text-charcoal mb-6">Color palette</h3>

      <div className="space-y-6">
        {/* Clothing Colors */}
        {best_clothing_colors?.length > 0 && (
          <div>
            <p className="text-sm font-medium text-charcoal mb-3">
              Clothing colors
            </p>
            <div className="flex flex-wrap gap-3">
              {best_clothing_colors.map((hex, i) => (
                <Swatch key={i} hex={hex} />
              ))}
            </div>
          </div>
        )}

        {/* Lip Colors */}
        {best_lip_colors?.length > 0 && (
          <div>
            <p className="text-sm font-medium text-charcoal mb-3">
              Lip shades
            </p>
            <div className="flex flex-wrap gap-3">
              {best_lip_colors.map((hex, i) => (
                <Swatch key={i} hex={hex} />
              ))}
            </div>
          </div>
        )}

        {/* Jewelry */}
        {best_jewelry && (
          <div>
            <p className="text-sm font-medium text-charcoal mb-3">
              Jewelry
            </p>
            <div className="inline-flex items-center gap-2 px-4 py-2.5 bg-cream/70 border border-blush/10 rounded-lg">
              <span className="text-sm font-semibold text-charcoal">{jewelry.label}</span>
            </div>
          </div>
        )}

        {/* Colors to Avoid */}
        {avoid_colors?.length > 0 && (
          <div>
            <p className="text-sm font-medium text-charcoal mb-3">
              Lower harmony colors
            </p>
            <div className="flex flex-wrap gap-3">
              {avoid_colors.map((hex, i) => (
                <Swatch key={i} hex={hex} strikeThrough />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
