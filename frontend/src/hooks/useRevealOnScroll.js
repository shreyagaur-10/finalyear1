import { useEffect } from 'react'

export default function useRevealOnScroll() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible')
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.01, rootMargin: '0px 0px -40px 0px' }
    )

    const observeElement = (element) => {
      if (!(element instanceof Element)) return
      if (!element.classList.contains('reveal-on-scroll')) return
      if (element.classList.contains('is-visible')) return
      observer.observe(element)
    }

    document.querySelectorAll('.reveal-on-scroll').forEach(observeElement)

    const mutationObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          observeElement(node)
          if (node instanceof Element) {
            node.querySelectorAll('.reveal-on-scroll').forEach(observeElement)
          }
        })
      })
    })

    mutationObserver.observe(document.body, { childList: true, subtree: true })

    return () => {
      mutationObserver.disconnect()
      observer.disconnect()
    }
  }, [])
}
