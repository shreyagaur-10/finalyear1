import { useState } from 'react'

const SUGGESTIONS = [
  'Natural look for college',
  'Party glam, full coverage',
  'Everyday office look',
  'Dewy glass skin for photos',
  'Wedding guest, long-lasting',
  'Minimal no-makeup makeup',
]

export default function TextInput({ value, onChange }) {
  const [focused, setFocused] = useState(false)

  return (
    <div className="flex-1 flex flex-col">
      <div className={`relative rounded-2xl transition-all duration-300 ${
        focused ? 'ring-2 ring-blush/50' : ''
      }`}>
        <textarea
          id="text-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="e.g., Natural look for college, matte finish..."
          rows={4}
          className="w-full px-4 py-3 rounded-lg bg-white/70 border border-blush/20
            text-charcoal placeholder-charcoal-light/50
            focus:outline-none focus:bg-white/80
            transition-all duration-300 resize-none
            text-[15px] leading-relaxed"
        />
      </div>

      {/* Quick Suggestions */}
      <div className="mt-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-charcoal-light mb-2">Quick directions</p>
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => onChange(suggestion)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium
                transition-all duration-200 cursor-pointer
                ${value === suggestion
                  ? 'bg-charcoal text-white'
                  : 'bg-white/70 border border-blush/10 text-charcoal-light hover:bg-blush-light/30 hover:text-charcoal'
                }`}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
