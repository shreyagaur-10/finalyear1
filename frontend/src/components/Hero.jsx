import { useState, useEffect, useRef } from 'react'

function AnimatedCounter({ target, suffix = '' }) {
  const [count, setCount] = useState(0)
  const started = useRef(false)

  useEffect(() => {
    if (started.current) return
    started.current = true
    const duration = 1400
    const start = performance.now()

    const animate = (now) => {
      const progress = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setCount(Math.round(eased * target))
      if (progress < 1) requestAnimationFrame(animate)
    }
    requestAnimationFrame(animate)
  }, [target])

  return <span>{count}{suffix}</span>
}

const SHADE_STRIP = ['#F8D9C8', '#EBC1A0', '#D39C75', '#B77954', '#875338', '#563325']

export default function Hero() {
  return (
    <section className="hero-stage relative overflow-hidden">
      <div className="hero-noise" />
      <div className="hero-marquee" aria-hidden="true">
        <div>
          <span>CIEDE2000 shade matching</span>
          <span>lighting quality checks</span>
          <span>six shade-depth classes</span>
          <span>real product ranking</span>
        </div>
        <div>
          <span>CIEDE2000 shade matching</span>
          <span>lighting quality checks</span>
          <span>six shade-depth classes</span>
          <span>real product ranking</span>
        </div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-20 sm:pt-18 sm:pb-24">
        <div className="grid lg:grid-cols-[0.98fr_1.02fr] gap-10 lg:gap-14 items-center">
          <div className="relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/70 border border-white/80 shadow-sm text-xs font-bold text-charcoal mb-5 animate-fade-in">
              <span className="w-2 h-2 rounded-full bg-[#7C3F2E] animate-pulse-soft" />
              Shade intelligence for real skin
            </div>

            <h1 className="hero-title font-serif font-black text-charcoal leading-[0.9] tracking-normal animate-fade-in-up">
              Find the shade that feels like you.
            </h1>

            <p className="mt-6 text-base sm:text-lg text-charcoal-light max-w-xl leading-relaxed animate-fade-in-up stagger-2">
              A loving little beauty lab that reads your selfie, checks the lighting, understands undertone, and ranks real products with explainable color science.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row gap-3 animate-fade-in-up stagger-3">
              <a href="#analyze" className="magnetic-button inline-flex items-center justify-center px-6 py-3.5 rounded-2xl bg-charcoal text-cream font-bold text-sm shadow-xl">
                Start my shade ritual
              </a>
              <a href="#results-preview" className="inline-flex items-center justify-center px-6 py-3.5 rounded-2xl bg-white/70 border border-white/80 text-charcoal font-bold text-sm shadow-sm hover:-translate-y-0.5 transition-all">
                Peek inside the lab
              </a>
            </div>

            <div className="mt-10 grid grid-cols-3 gap-3 max-w-xl animate-fade-in-up stagger-4">
              {[
                ['78%', '6-class macro-F1'],
                ['56+', 'catalog shades'],
                ['CIEDE', 'color distance'],
              ].map(([value, label]) => (
                <div key={label} className="tiny-stat">
                  <p className="text-2xl sm:text-3xl font-black text-charcoal font-serif">
                    {value === '56+' ? <AnimatedCounter target={56} suffix="+" /> : value}
                  </p>
                  <p className="text-[11px] text-charcoal-light mt-1">{label}</p>
                </div>
              ))}
            </div>
          </div>

          <div id="results-preview" className="hero-collage relative min-h-[560px] animate-fade-in-up stagger-2">
            <div className="floating-label label-one">undertone warm-neutral</div>
            <div className="floating-label label-two">good light · 91%</div>

            <div className="shade-orbit orbit-one" />
            <div className="shade-orbit orbit-two" />

            <div className="phone-mockup">
              <div className="phone-topbar">
                <span />
                <span />
                <span />
              </div>
              <div className="phone-screen">
                <div className="face-card">
                  <div className="face-glow" />
                  <div className="face-oval">
                    <div className="cheek left" />
                    <div className="cheek right" />
                  </div>
                  <div className="scan-line" />
                </div>
                <div className="phone-copy">
                  <p className="text-xs uppercase tracking-[0.24em] text-charcoal-light">detected shade</p>
                  <h3 className="font-serif text-3xl font-black text-charcoal">Warm Honey</h3>
                  <p className="text-sm text-charcoal-light">CIEDE2000 distance · 4.8</p>
                </div>
              </div>
            </div>

            <div className="swatch-board">
              <p className="text-xs font-bold uppercase tracking-[0.22em] text-charcoal-light mb-3">shade depth</p>
              <div className="flex items-end gap-2 h-32">
                {SHADE_STRIP.map((color, index) => (
                  <div
                    key={color}
                    className="hero-swatch"
                    style={{ backgroundColor: color, height: `${58 + index * 13}px`, animationDelay: `${index * 0.12}s` }}
                  />
                ))}
              </div>
            </div>

            <div className="match-ticket">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold uppercase tracking-[0.22em] text-charcoal-light">top match</span>
                <span className="px-2.5 py-1 rounded-full bg-[#24352B] text-white text-xs font-bold">96%</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-2xl shadow-md border-2 border-white" style={{ backgroundColor: '#C88F65' }} />
                <div>
                  <p className="font-bold text-charcoal">Fit Me · 330 Toffee</p>
                  <p className="text-xs text-charcoal-light">shade + undertone + feedback prior</p>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </section>
  )
}
