import { useState } from 'react'

const API_URL = import.meta.env.PROD
  ? (import.meta.env.VITE_API_URL || '')
  : ''

export default function VirtualTryOn({ imageFile, product, onClose }) {
  const [tryOnImage, setTryOnImage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [originalPreview] = useState(() => URL.createObjectURL(imageFile))

  const handleTryOn = async () => {
    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('image', imageFile)
      formData.append('hex_color', product.hex_color)
      formData.append('product_type', product.type || 'foundation')

      const response = await fetch(`${API_URL}/api/tryon`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Try-on failed. Please try again.')
      }

      const blob = await response.blob()
      setTryOnImage(URL.createObjectURL(blob))
    } catch (err) {
      console.error('Try-on error:', err)
      setError(err.message || 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  // Start try-on on mount
  useState(() => {
    handleTryOn()
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto animate-fade-in-up">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-blush/20">
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-lg border-2 border-white shadow-sm"
              style={{ backgroundColor: product.hex_color }}
            />
            <div>
              <h3 className="font-semibold text-charcoal text-sm">
                Virtual try-on
              </h3>
              <p className="text-xs text-charcoal-light">
                {product.brand}: {product.shade_name}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-9 h-9 rounded-lg bg-cream hover:bg-cream-dark transition-colors
              flex items-center justify-center text-charcoal cursor-pointer"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-5">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="w-12 h-12 border-4 border-blush/30 border-t-blush rounded-full animate-spin mb-4" />
              <p className="text-charcoal-light text-sm">Applying {product.shade_name}...</p>
            </div>
          )}

          {error && (
            <div className="text-center py-12">
              <p className="text-red-500 mb-4">{error}</p>
              <button
                onClick={handleTryOn}
                className="px-6 py-2.5 bg-charcoal text-white rounded-lg font-medium
                  hover:bg-charcoal-light transition-colors cursor-pointer"
              >
                Retry
              </button>
            </div>
          )}

          {tryOnImage && !loading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Original */}
              <div>
                <p className="text-xs font-medium text-charcoal-light mb-2 text-center">Original</p>
                <img
                  src={originalPreview}
                  alt="Original"
                  className="w-full rounded-lg object-cover shadow-md"
                  style={{ maxHeight: '400px' }}
                />
              </div>
              {/* Try-on result */}
              <div>
                <p className="text-xs font-medium text-charcoal-light mb-2 text-center">
                  With {product.shade_name}
                </p>
                <img
                  src={tryOnImage}
                  alt="Try-on result"
                  className="w-full rounded-lg object-cover shadow-md"
                  style={{ maxHeight: '400px' }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
