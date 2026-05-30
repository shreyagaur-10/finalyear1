import { useState, useEffect, useRef } from 'react'
import Hero from './components/Hero'
import ImageUpload from './components/ImageUpload'
import TextInput from './components/TextInput'
import Results from './components/Results'
import LoadingSpinner from './components/LoadingSpinner'
import VirtualTryOn from './components/VirtualTryOn'
import useRevealOnScroll from './hooks/useRevealOnScroll'

// API URL — uses proxy in dev, direct URL in production
const API_URL = import.meta.env.PROD
  ? (import.meta.env.VITE_API_URL || '')
  : ''

async function readJsonResponse(response) {
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json()
  }

  const text = await response.text()
  throw new Error(
    response.status === 404 && API_URL === ''
      ? 'Backend API URL is not configured. Set VITE_API_URL in Vercel and redeploy.'
      : text || `Server returned ${response.status}. Please try again.`
  )
}

function App() {
  useRevealOnScroll()

  const [sessionId] = useState(() => {
    try {
      const existing = localStorage.getItem('shadeSenseSessionId')
      if (existing) return existing
      const created = crypto.randomUUID()
      localStorage.setItem('shadeSenseSessionId', created)
      return created
    } catch {
      return `session-${Date.now()}`
    }
  })

  const [darkMode, setDarkMode] = useState(() => {
    try { return localStorage.getItem('darkMode') === 'true' } catch { return false }
  })

  useEffect(() => {
    try { localStorage.setItem('darkMode', darkMode) } catch {}
  }, [darkMode])

  const [image, setImage] = useState(null)         // File object
  const [imagePreview, setImagePreview] = useState(null) // base64 preview
  const [text, setText] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Party mode (multi-face)
  const [partyMode, setPartyMode] = useState(false)
  const [multiFaces, setMultiFaces] = useState(null)
  const [activeFaceIndex, setActiveFaceIndex] = useState(0)

  // Virtual try-on
  const [tryOnProduct, setTryOnProduct] = useState(null)
  const resultsRef = useRef(null)

  const handleImageSelect = (file) => {
    setImage(file)
    setError(null)
    setResults(null)
    setMultiFaces(null)

    // Create preview
    const reader = new FileReader()
    reader.onload = (e) => setImagePreview(e.target.result)
    reader.readAsDataURL(file)
  }

  const handleClearImage = () => {
    setImage(null)
    setImagePreview(null)
    setResults(null)
    setMultiFaces(null)
    setError(null)
  }

  const handleAnalyze = async () => {
    if (!image) {
      setError('Please upload or capture a photo first.')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)
    setMultiFaces(null)
    setActiveFaceIndex(0)

    try {
      const formData = new FormData()
      formData.append('image', image)
      formData.append('text', text)

      const endpoint = partyMode ? '/api/analyze-multi' : '/api/analyze'
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        body: formData,
      })

      const data = await readJsonResponse(response)

      if (!response.ok) {
        throw new Error(data.detail || 'Server error. Please try again.')
      }

      if (data.success) {
        if (partyMode && data.faces) {
          setMultiFaces(data.faces)
          setResults(data.faces[0])
        } else {
          setResults(data)
        }
      } else {
        setError(data.error || 'Analysis failed. Please try a clearer photo.')
      }
    } catch (err) {
      console.error('Analysis error:', err)
      setError(
        err.message === 'Failed to fetch'
          ? 'Cannot connect to the server. Please make sure the backend is running.'
          : err.message || 'Something went wrong. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleTryOn = (product) => {
    setTryOnProduct(product)
  }

  const activeResults = multiFaces ? multiFaces[activeFaceIndex] : results

  useEffect(() => {
    if (!activeResults || loading) return

    window.requestAnimationFrame(() => {
      resultsRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      })
    })
  }, [activeResults, loading])

  return (
    <div className={`min-h-screen bg-cream app-shell ${darkMode ? 'dark' : ''}`}>
      <header className="sticky top-0 z-50 bg-cream/75 backdrop-blur-xl border-b border-blush/10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <a href="#" className="flex items-center gap-3">
            <span className="w-9 h-9 rounded-lg bg-charcoal text-cream flex items-center justify-center font-serif font-bold">
              S
            </span>
            <span>
              <span className="block text-sm font-bold text-charcoal leading-tight">ShadeSense AI</span>
              <span className="block text-[11px] text-charcoal-light leading-tight">shade intelligence lab</span>
            </span>
          </a>
          <div className="flex items-center gap-2">
            <a href="#analyze" className="hidden sm:inline-flex px-3 py-2 rounded-lg text-sm font-semibold text-charcoal hover:bg-white/70 transition-colors">
              Analyze
            </a>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="px-3 py-2 rounded-lg bg-white/80 border border-blush/15 text-xs font-semibold text-charcoal
                hover:border-charcoal/20 transition-colors cursor-pointer"
              aria-label="Toggle dark mode"
            >
              {darkMode ? 'Light' : 'Dark'}
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <Hero />

      {/* Main Content */}
      <main id="analyze" className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Upload + Input Section */}
        <div className="reveal-on-scroll">
          <div className="lab-card rounded-[2rem] bg-white/85 border border-white/70 p-4 sm:p-6 shadow-xl">
            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3 mb-6">
              <div>
                <p className="eyebrow">Shade lab</p>
                <h2 className="text-2xl sm:text-3xl font-bold font-serif text-charcoal">Upload, describe, match</h2>
              </div>
              <div className="flex gap-2 text-xs text-charcoal-light">
                <span className="soft-pill">No login</span>
                <span className="soft-pill">Private preview</span>
                <span className="soft-pill">Real products</span>
              </div>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left: Image Upload */}
              <div>
                <h3 className="text-base font-semibold text-charcoal mb-1">1. Add a face photo</h3>
                <p className="text-sm text-charcoal-light mb-4">
                  Use a front-facing photo with even natural light.
                </p>
                <ImageUpload
                  onImageSelect={handleImageSelect}
                  onClear={handleClearImage}
                  preview={imagePreview}
                />

                {/* Party Mode Toggle */}
                <div className="mt-4 flex items-center gap-3 p-3 rounded-2xl bg-cream/70 border border-blush/10">
                  <button
                    onClick={() => setPartyMode(!partyMode)}
                    className={`relative w-12 h-7 rounded-full transition-all duration-300 cursor-pointer flex-shrink-0 ${
                      partyMode
                        ? 'bg-charcoal'
                        : 'bg-charcoal-light/20'
                    }`}
                    aria-label="Toggle multi-face mode"
                  >
                    <div
                      className={`absolute top-0.5 w-6 h-6 bg-white rounded-full shadow-md transition-all duration-300 ${
                        partyMode ? 'left-5.5' : 'left-0.5'
                      }`}
                    />
                  </button>
                  <div>
                    <p className="text-sm font-medium text-charcoal">
                      Multi-face mode
                    </p>
                    <p className="text-xs text-charcoal-light">
                      Detect & analyze multiple faces in one photo
                    </p>
                  </div>
                </div>
              </div>

              {/* Right: Text Input + Analyze Button */}
              <div className="flex flex-col">
                <h3 className="text-base font-semibold text-charcoal mb-1">2. Set the makeup direction</h3>
                <p className="text-sm text-charcoal-light mb-4">
                  Describe the look you're going for (optional)
                </p>
                <TextInput value={text} onChange={setText} />

                <div className="mt-auto pt-6">
                  {error && (
                    <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm animate-fade-in">
                      {error}
                    </div>
                  )}

                  <button
                    onClick={handleAnalyze}
                    disabled={!image || loading}
                    className="w-full py-4 rounded-2xl font-semibold text-base
                      transition-all duration-300 cursor-pointer
                      disabled:opacity-50 disabled:cursor-not-allowed
                      bg-charcoal magnetic-button
                      text-white shadow-lg
                      hover:shadow-xl hover:-translate-y-0.5
                      active:scale-[0.98]"
                  >
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Analyzing...
                      </span>
                    ) : (
                      'Find matching shades'
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && <LoadingSpinner />}

        {/* Multi-Face Selector */}
        {multiFaces && multiFaces.length > 1 && !loading && (
          <div className="mt-8 reveal-on-scroll is-visible">
            <div className="lab-card rounded-[1.5rem] bg-white/85 border border-white/70 p-4">
              <p className="text-sm font-medium text-charcoal mb-3">
                {multiFaces.length} faces detected
              </p>
              <div className="flex flex-wrap gap-2">
                {multiFaces.map((face, i) => (
                  <button
                    key={i}
                    onClick={() => setActiveFaceIndex(i)}
                    className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer
                      flex items-center gap-2
                      ${activeFaceIndex === i
                        ? 'bg-charcoal text-white shadow-md'
                        : 'bg-cream text-charcoal-light hover:text-charcoal hover:shadow-sm'
                      }`}
                  >
                    <div
                      className="w-5 h-5 rounded-full border-2 border-white shadow-sm"
                      style={{ backgroundColor: face.skin_analysis?.hex_color || '#ccc' }}
                    />
                    Face {i + 1}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {activeResults && !loading && (
          <div ref={resultsRef} className="mt-12 reveal-on-scroll is-visible">
            <Results
              data={activeResults}
              imageFile={image}
              onTryOn={handleTryOn}
              sessionId={sessionId}
            />
          </div>
        )}
      </main>

      {/* Virtual Try-On Modal */}
      {tryOnProduct && image && (
        <VirtualTryOn
          imageFile={image}
          product={tryOnProduct}
          onClose={() => setTryOnProduct(null)}
        />
      )}

      {/* Footer */}
      <footer className="mt-10 border-t border-blush/15 bg-white/45 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-4">
              <span className="w-11 h-11 rounded-xl bg-charcoal text-cream flex items-center justify-center font-serif font-bold shadow-lg">
                S
              </span>
              <div>
                <p className="font-serif text-xl font-bold text-charcoal">ShadeSense AI</p>
                <p className="text-sm text-charcoal-light">
                  Shade matching for Indian and South Asian skin tones.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 text-xs font-semibold text-charcoal-light">
              <span className="soft-pill">Private preview</span>
              <span className="soft-pill">Real catalog shades</span>
              <span className="soft-pill">Explainable ranking</span>
            </div>
          </div>

          <div className="mt-7 flex flex-col gap-4 border-t border-blush/10 pt-5 sm:flex-row sm:items-center sm:justify-between">
            <nav className="flex flex-wrap gap-x-5 gap-y-2 text-sm font-semibold text-charcoal">
              <a href="#analyze" className="hover:text-blush-dark transition-colors">Analyze</a>
              <a href="#" className="hover:text-blush-dark transition-colors">Top</a>
              <a href={`${API_URL || 'http://localhost:8000'}/api/health`} className="hover:text-blush-dark transition-colors">API status</a>
            </nav>

            <p className="text-xs text-charcoal-light">
              Results can vary with lighting. Test products in store when possible.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
