import { useEffect, type RefObject } from 'react'

/**
 * Fades `[data-reveal]` descendants in as they enter the viewport
 * (the skill's IntersectionObserver reveal pattern, React-flavored).
 */
export function useReveal(rootRef: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const root = rootRef.current
    if (!root) return
    const els = Array.from(root.querySelectorAll<HTMLElement>('[data-reveal]:not(.revealed)'))
    if (!('IntersectionObserver' in window)) {
      els.forEach((el) => el.classList.add('revealed'))
      return
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting || entry.boundingClientRect.top < 0) {
            entry.target.classList.add('revealed')
            io.unobserve(entry.target)
          }
        }
      },
      { threshold: 0.18, rootMargin: '0px 0px -8% 0px' },
    )
    els.forEach((el) => io.observe(el))

    // Anchor jumps can skip past sections without ever intersecting them;
    // sweep anything that ended up above the viewport so it isn't left hidden.
    const sweep = () => {
      for (const el of els) {
        if (el.classList.contains('revealed')) continue
        if (el.getBoundingClientRect().bottom < 0) {
          el.classList.add('revealed')
          io.unobserve(el)
        }
      }
    }
    window.addEventListener('scroll', sweep, { passive: true })

    return () => {
      io.disconnect()
      window.removeEventListener('scroll', sweep)
    }
  }, [rootRef])
}
