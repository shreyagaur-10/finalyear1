export default function SkinToneViz({ hexColor, luminance, shadeName }) {
  // Map luminance to Fitzpatrick scale
  const getFitzpatrickType = (lum) => {
    if (lum > 200) return 1
    if (lum >= 185) return 2
    if (lum >= 155) return 3
    if (lum >= 125) return 4
    if (lum >= 80) return 5
    return 6
  }

  const fitzType = getFitzpatrickType(luminance)

  // Position on gradient (0-100%) — higher luminance = more left
  const markerPosition = Math.max(2, Math.min(98, 100 - (luminance / 255) * 100))

  const fitzpatrickScale = [
    { type: 'I', label: 'Very Light', color: '#FDDCB5' },
    { type: 'II', label: 'Light', color: '#E8B88A' },
    { type: 'III', label: 'Medium', color: '#C8956C' },
    { type: 'IV', label: 'Olive', color: '#A0714F' },
    { type: 'V', label: 'Brown', color: '#6B4226' },
    { type: 'VI', label: 'Dark', color: '#3B2210' },
  ]

  return (
    <div className="glass rounded-2xl p-6 sm:p-8 animate-fade-in-up stagger-2">
      <h3 className="text-lg font-semibold text-charcoal mb-6 flex items-center gap-2">
        <span className="text-xl">🌈</span> Skin Tone Spectrum
      </h3>

      {/* Gradient bar with marker */}
      <div className="mb-8">
        <div className="relative">
          <div
            className="h-6 rounded-full shadow-inner"
            style={{
              background: 'linear-gradient(to right, #FDDCB5, #E8B88A, #C8956C, #A0714F, #6B4226, #3B2210)',
            }}
          />
          {/* Marker */}
          <div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 transition-all duration-700"
            style={{ left: `${markerPosition}%` }}
          >
            <div className="flex flex-col items-center">
              <div
                className="w-8 h-8 rounded-full border-[3px] border-white shadow-lg -mb-1"
                style={{ backgroundColor: hexColor }}
              />
              <div className="w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-l-transparent border-r-transparent border-t-white" />
            </div>
          </div>
        </div>
        <div className="flex justify-between mt-2 text-[10px] text-charcoal-light">
          <span>Light</span>
          <span>Dark</span>
        </div>
      </div>

      {/* Fitzpatrick Scale */}
      <div>
        <p className="text-sm font-medium text-charcoal mb-3">
          Fitzpatrick Scale <span className="text-gold font-semibold">Type {fitzpatrickScale[fitzType - 1].type}</span>
        </p>
        <div className="grid grid-cols-6 gap-2">
          {fitzpatrickScale.map((item, i) => {
            const isActive = i + 1 === fitzType
            return (
              <div
                key={item.type}
                className={`flex flex-col items-center p-2 rounded-xl transition-all duration-300 ${
                  isActive
                    ? 'ring-2 ring-gold bg-gold-light/20 scale-105'
                    : 'opacity-60 hover:opacity-80'
                }`}
              >
                <div
                  className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg shadow-md border-2 border-white mb-1.5"
                  style={{ backgroundColor: item.color }}
                />
                <span className={`text-xs font-bold ${isActive ? 'text-charcoal' : 'text-charcoal-light'}`}>
                  {item.type}
                </span>
                <span className="text-[9px] text-charcoal-light hidden sm:block">
                  {item.label}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Current shade label */}
      <div className="mt-4 pt-4 border-t border-blush/20 flex items-center gap-3">
        <div
          className="w-5 h-5 rounded-full border-2 border-white shadow-sm"
          style={{ backgroundColor: hexColor }}
        />
        <p className="text-sm text-charcoal-light">
          Your shade: <span className="font-semibold text-charcoal">{shadeName}</span>
          <span className="ml-2 text-xs text-charcoal-light/60">(Luminance: {Math.round(luminance)})</span>
        </p>
      </div>
    </div>
  )
}
