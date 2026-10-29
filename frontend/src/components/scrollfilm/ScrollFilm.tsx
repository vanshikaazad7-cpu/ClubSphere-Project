/**
 * Scroll-film engine — React port of the skill's vanilla scrubber.
 *
 * A tall track with a sticky full-viewport stage. Scroll progress (0..1) is
 * time-lerped (1 − exp(−dt·14)) so fast flicks glide, then fed to the scene
 * and to the caption system (data-in / hold / out fractions, exactly like
 * the frame-film engine — captions stay valid if an AI film drops in later).
 */
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { createFilmScene, type FilmScene } from './scene'

type CaptionPos = 'center' | 'left' | 'right' | 'top' | 'bottom'

interface CaptionSpec {
  pos: CaptionPos
  /** Scroll fraction the caption fades in (negative so the title shows at 0). */
  in: number
  hold: number
  out: number
  node: React.ReactNode
}

const CAPTIONS: CaptionSpec[] = [
  {
    pos: 'center',
    in: -0.05,
    hold: 0.03,
    out: 0.085,
    node: (
      <>
        <h1 className="film-h1">
          Club<span className="accent">Sphere</span>
        </h1>
        <p>The university club, engineered end to end.</p>
      </>
    ),
  },
  {
    pos: 'left',
    in: 0.12,
    hold: 0.165,
    out: 0.21,
    node: (
      <>
        <h2>It starts with a spark.</h2>
        <p>A student idea. A faculty signature. One light on.</p>
      </>
    ),
  },
  {
    pos: 'right',
    in: 0.26,
    hold: 0.315,
    out: 0.37,
    node: (
      <>
        <h2>
          Structure, without the <span className="accent">weight.</span>
        </h2>
        <p>Governance lines drawn once. Approvals follow them forever.</p>
      </>
    ),
  },
  {
    pos: 'left',
    in: 0.42,
    hold: 0.475,
    out: 0.525,
    node: (
      <>
        <h2>Clubs find their orbit.</h2>
        <p>Seven clubs, every program, one gravity.</p>
      </>
    ),
  },
  {
    pos: 'right',
    in: 0.58,
    hold: 0.635,
    out: 0.685,
    node: (
      <>
        <h2>Events, in motion.</h2>
        <p>Registrations, attendance, notifications — travelling the same wire.</p>
      </>
    ),
  },
  {
    pos: 'left',
    in: 0.735,
    hold: 0.79,
    out: 0.84,
    node: (
      <>
        <h2>
          Audited. <span className="accent">Accountable.</span>
        </h2>
        <p>Every action leaves a trace. Compliance, by construction.</p>
      </>
    ),
  },
  {
    pos: 'bottom',
    in: 0.9,
    hold: 0.965,
    out: 1.12,
    node: (
      <>
        <div className="film-h1">
          Club<span className="accent">Sphere</span>
        </div>
        <p>One sphere. Every activity.</p>
        <Link className="film-cta" to="/login">
          Enter the platform
        </Link>
      </>
    ),
  },
]

function transformBase(pos: CaptionPos): string {
  if (pos === 'center') return 'translate(-50%, -50%)'
  if (pos === 'top' || pos === 'bottom') return 'translateX(-50%)'
  return 'translateY(-50%)'
}

export default function ScrollFilm({ onFilmEnd }: { onFilmEnd?: (ended: boolean) => void }) {
  const trackRef = useRef<HTMLDivElement>(null)
  const stageRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const captionRefs = useRef<Array<HTMLDivElement | null>>([])
  const cueRef = useRef<HTMLDivElement>(null)
  const loaderBarRef = useRef<HTMLDivElement>(null)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    const canvas = canvasRef.current
    const track = trackRef.current
    if (!canvas || !track) return

    let scene: FilmScene | null = null
    try {
      scene = createFilmScene(canvas)
    } catch {
      scene = null // degraded mode: captions over the backdrop still work
    }

    const resize = () => {
      scene?.resize(canvas.clientWidth, canvas.clientHeight)
    }
    resize()
    window.addEventListener('resize', resize)

    // Scene is synchronous — one rendered frame means we're ready.
    scene?.render(0.016)
    let loaderTimeout = 0
    const loaderFrame = requestAnimationFrame(() => {
      if (loaderBarRef.current) loaderBarRef.current.style.width = '100%'
      loaderTimeout = window.setTimeout(() => setLoaded(true), 350)
    })

    let raf = 0
    let lastT = performance.now()
    let smooth = 0
    let lastEnded: boolean | null = null

    // Respect the OS reduced-motion preference: scrub directly, no easing.
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    const tick = (now: number) => {
      const dt = Math.min((now - lastT) / 1000, 0.5) || 0.016
      lastT = now

      // Measure the pinned stage rather than `window.innerHeight`: on mobile the
      // stage uses `100dvh`, so this keeps the scroll→progress mapping stable
      // while the browser chrome collapses/expands.
      const stageH = stageRef.current?.offsetHeight ?? window.innerHeight
      const max = track.offsetHeight - stageH
      const scrolled = window.scrollY - track.offsetTop
      const target = max > 0 ? Math.min(1, Math.max(0, scrolled / max)) : 0

      // Time-based lerp: fast flicks glide, throttled tabs still converge.
      const k = reduceMotion ? 1 : 1 - Math.exp(-dt * 14)
      smooth += (target - smooth) * k
      if (Math.abs(target - smooth) < 0.0004) smooth = target

      scene?.setProgress(smooth)
      scene?.render(dt)

      // Captions — same opacity/travel math as the frame engine.
      for (let i = 0; i < CAPTIONS.length; i++) {
        const el = captionRefs.current[i]
        if (!el) continue
        const { in: tIn, hold: tHold, out: tOut, pos } = CAPTIONS[i]
        const rise = Math.max((tHold - tIn) * 0.4, 0.008)
        const fall = Math.max((tOut - tHold) * 0.6, 0.008)
        let o = 0
        if (target >= tIn && target <= tOut) {
          o = Math.min((target - tIn) / rise, 1) * Math.min((tOut - target) / fall, 1)
          o = Math.min(Math.max(o, 0), 1)
        }
        el.inert = o < 0.05
        el.style.opacity = o.toFixed(3)
        const drift = (target - tHold) * -40
        el.style.transform = `${transformBase(pos)} translateY(${drift.toFixed(1)}px)`
      }

      if (cueRef.current) cueRef.current.style.opacity = target < 0.015 ? '1' : '0'

      const ended = target > 0.995
      if (ended !== lastEnded) {
        lastEnded = ended
        onFilmEnd?.(ended)
      }

      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)

    return () => {
      cancelAnimationFrame(raf)
      cancelAnimationFrame(loaderFrame)
      window.clearTimeout(loaderTimeout)
      window.removeEventListener('resize', resize)
      scene?.dispose()
    }
  }, [onFilmEnd])

  return (
    <>
      <div className={`film-loader ${loaded ? 'done' : ''}`} aria-hidden={loaded}>
        <div className="mark">ClubSphere</div>
        <div className="bar">
          <i ref={loaderBarRef} />
        </div>
      </div>

      <div ref={trackRef} className="film-track">
        <div ref={stageRef} className="film-stage">
          <canvas ref={canvasRef} className="film-canvas" />
          <div className="film-vignette" aria-hidden />

          {CAPTIONS.map((cap, i) => (
            <div
              key={i}
              ref={(el) => {
                captionRefs.current[i] = el
              }}
              className={`film-caption cap-${cap.pos}`}
              style={{ opacity: 0 }}
            >
              {cap.node}
            </div>
          ))}

          <div ref={cueRef} className="film-cue">
            Scroll
          </div>
        </div>
      </div>
    </>
  )
}
