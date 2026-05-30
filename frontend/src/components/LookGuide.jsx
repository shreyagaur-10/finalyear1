const DIFFICULTY_STYLES = {
  beginner: 'bg-green-100 text-green-800',
  intermediate: 'bg-amber-100 text-amber-800',
  pro: 'bg-red-100 text-red-800',
}

export default function LookGuide({ completeLook }) {
  if (!completeLook) return null

  const { look_name, look_description, estimated_time, difficulty, steps } = completeLook
  const difficultyStyle = DIFFICULTY_STYLES[difficulty] || DIFFICULTY_STYLES.beginner

  return (
    <div className="rounded-lg bg-white/85 border border-blush/15 p-6 sm:p-8 animate-fade-in-up stagger-3">
      {/* Header */}
      <div className="mb-8">
        <h3 className="text-2xl font-bold text-charcoal font-serif mb-2">
          {look_name}
        </h3>
        {look_description && (
          <p className="text-sm text-charcoal-light leading-relaxed mb-4">
            {look_description}
          </p>
        )}
        <div className="flex flex-wrap gap-2">
          {estimated_time && (
            <span className="px-3 py-1.5 bg-cream/80 border border-blush/10 rounded-md text-xs font-medium text-charcoal">
              {estimated_time}
            </span>
          )}
          {difficulty && (
            <span className={`px-3 py-1.5 rounded-md text-xs font-semibold capitalize ${difficultyStyle}`}>
              {difficulty}
            </span>
          )}
        </div>
      </div>

      {/* Timeline Steps */}
      {steps?.length > 0 && (
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-blush/30" />

          <div className="space-y-6">
            {steps.map((step, i) => {
              return (
                <div
                  key={step.step_number || i}
                  className="relative pl-14 animate-fade-in-up"
                  style={{ animationDelay: `${i * 0.1}s` }}
                >
                  {/* Numbered circle */}
                  <div className="absolute left-2 top-0 w-7 h-7 rounded-full
                    bg-charcoal text-white
                    flex items-center justify-center text-xs font-bold shadow-md z-10">
                    {step.step_number || i + 1}
                  </div>

                  {/* Step card */}
                  <div className="p-4 bg-cream/70 border border-blush/10 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-semibold text-charcoal-light uppercase tracking-wider">
                        {step.category}
                      </span>
                    </div>

                    <p className="text-sm text-charcoal leading-relaxed">
                      {step.instruction}
                    </p>

                    {/* Product swatch */}
                    {step.product && (
                      <div className="mt-2 flex items-center gap-2">
                        <div
                          className="w-5 h-5 rounded-md border-2 border-white shadow-sm flex-shrink-0"
                          style={{ backgroundColor: step.product.hex_color || '#ccc' }}
                        />
                        <span className="text-xs font-medium text-charcoal">
                          {step.product.brand}: {step.product.shade_name}
                        </span>
                      </div>
                    )}

                    {/* Pro tip */}
                    {step.pro_tip && (
                      <p className="mt-2 text-xs text-gold-dark italic">
                        {step.pro_tip}
                      </p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
