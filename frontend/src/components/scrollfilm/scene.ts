/**
 * ClubSphere scroll-film scene — live-rendered WebGL3D.
 *
 * A single continuous scene whose state is a pure function of scroll progress
 * p ∈ [0,1] (the same contract the frame-film engine uses, so an AI-rendered
 * frame sequence can drop in behind the same captions later).
 *
 * Chapters (progress windows, mirrored in ScrollFilm captions):
 *   0.00–0.10 dormant sphere in a starfield        0.10–0.22 core ignition
 *   0.22–0.40 governance meridians draw on         0.38–0.56 orbital ring + club nodes
 *   0.54–0.72 member constellation + pulses        0.70–0.86 compliance shell
 *   0.86–1.00 finale — bloom, pull-back, full mix
 */
import * as THREE from 'three'
import { createNewspaperTexture } from '../newspaperTexture'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'

export interface FilmScene {
  setProgress(p: number): void
  render(dtSeconds: number): void
  resize(width: number, height: number): void
  dispose(): void
}

const TAU = Math.PI * 2
const BLOOD = 0x74070e
const ROSE = 0x947268
const OLIVE = 0x45462a

function smoothstep(a: number, b: number, x: number): number {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)))
  return t * t * (3 - 2 * t)
}

/** Soft radial sprite used for every glow in the scene (no texture assets). */
function makeGlowTexture(): THREE.CanvasTexture {
  const size = 128
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = size
  const ctx = canvas.getContext('2d')!
  const grad = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2)
  grad.addColorStop(0, 'rgba(255,255,255,1)')
  grad.addColorStop(0.5, 'rgba(255,255,255,1)')
  grad.addColorStop(0.7, 'rgba(255,255,255,0.85)')
  grad.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, size, size)
  const tex = new THREE.CanvasTexture(canvas)
  tex.colorSpace = THREE.SRGBColorSpace
  return tex
}

/** Latitude/longitude line segments, ordered so setDrawRange "draws" all circles at once. */
function buildMeridians(radius: number, latitudes: number, longitudes: number, segs: number) {
  const positions: number[] = []
  const circles: THREE.Vector3[][] = []

  for (let m = 1; m < longitudes; m++) {
    const phi = (m / longitudes) * Math.PI
    const pts: THREE.Vector3[] = []
    for (let s = 0; s <= segs; s++) {
      const t = (s / segs) * TAU
      pts.push(
        new THREE.Vector3(
          radius * Math.sin(phi) * Math.cos(t),
          radius * Math.cos(phi),
          radius * Math.sin(phi) * Math.sin(t),
        ),
      )
    }
    circles.push(pts)
  }
  for (let l = 1; l <= latitudes; l++) {
    const theta = (l / (latitudes + 1) - 0.5) * Math.PI * 1.62
    const y = radius * Math.sin(theta)
    const r = radius * Math.cos(theta)
    const pts: THREE.Vector3[] = []
    for (let s = 0; s <= segs; s++) {
      const t = (s / segs) * TAU
      pts.push(new THREE.Vector3(r * Math.cos(t), y, r * Math.sin(t)))
    }
    circles.push(pts)
  }

  for (let s = 0; s < segs; s++) {
    for (const pts of circles) {
      positions.push(pts[s].x, pts[s].y, pts[s].z, pts[s + 1].x, pts[s + 1].y, pts[s + 1].z)
    }
  }
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  return geo
}

/** Random-but-stable points on a shell (golden-spiral + jitter). */
function shellPoints(count: number, rMin: number, rMax: number) {
  const pts: THREE.Vector3[] = []
  const rng = mulberry32(20261018)
  const golden = Math.PI * (3 - Math.sqrt(5))
  for (let i = 0; i < count; i++) {
    const y = 1 - (i / (count - 1)) * 2
    const rAtY = Math.sqrt(Math.max(0, 1 - y * y))
    const theta = golden * i
    const radius = rMin + rng() * (rMax - rMin)
    pts.push(
      new THREE.Vector3(
        Math.cos(theta) * rAtY * radius,
        y * radius + (rng() - 0.5) * 0.18,
        Math.sin(theta) * rAtY * radius,
      ),
    )
  }
  return pts
}

function mulberry32(seed: number) {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export function createFilmScene(canvas: HTMLCanvasElement): FilmScene | null {
  let renderer: THREE.WebGLRenderer
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' })
  } catch {
    return null // no WebGL — the page falls back to captions over the backdrop
  }

  const mobile = Math.min(window.innerWidth, window.innerHeight) < 640
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  // Low-power heuristic: keep the scene but drop the expensive post pass on
  // phones that report few cores / little memory.
  const cores = navigator.hardwareConcurrency ?? 8
  const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory ?? 8
  const lowPower = mobile && (cores <= 4 || memory <= 4)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, mobile ? (lowPower ? 1.25 : 1.5) : 2))
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.05

  const scene = new THREE.Scene()
  scene.background = new THREE.Color(0xffffff)
  scene.fog = new THREE.FogExp2(0xffffff, 0.009)

  const camera = new THREE.PerspectiveCamera(42, 16 / 9, 0.1, 80)
  camera.position.set(0, 0.4, 4.4)

  // Studio reflections for the obsidian surfaces.
  const pmrem = new THREE.PMREMGenerator(renderer)
  const envTex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture
  scene.environment = envTex
  scene.environmentIntensity = 0.32

  const glowTex = makeGlowTexture()
  const disposables: Array<{ dispose: () => void }> = [glowTex, pmrem]
  const track = <T extends { dispose: () => void }>(obj: T): T => {
    disposables.push(obj)
    return obj
  }

  /* ── lights ─────────────────────────────────────────── */
  scene.add(new THREE.AmbientLight(0xffffff, 1.5))
  const key = new THREE.DirectionalLight(0xffffff, 1.8)
  key.position.set(-3, 4, 2.5)
  const rim = new THREE.DirectionalLight(0xf4e3b2, 0.6)
  rim.position.set(3.5, -1.2, -3)
  const cyanHint = new THREE.DirectionalLight(OLIVE, 0.55)
  cyanHint.position.set(2.4, 2.2, -3.6)
  scene.add(key, rim, cyanHint)
  const coreLight = new THREE.PointLight(BLOOD, 0, 9, 2)
  scene.add(coreLight)

  /* ── root group (everything scrolls around this) ────── */
  const root = new THREE.Group()
  root.rotation.x = -0.1
  scene.add(root)

  // Newspaper globe; retain the original scroll camera and chapter choreography.
  const newspaperTexture = track(createNewspaperTexture())
  newspaperTexture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy())
  const sphereGeo = track(new THREE.SphereGeometry(1, 96, 64))
  const sphereMat = track(
    new THREE.MeshPhysicalMaterial({
      map: newspaperTexture,
      color: 0xffffff,
      metalness: 0,
      roughness: 0.9,
      clearcoat: 0,
    }),
  )
  const sphere = new THREE.Mesh(sphereGeo, sphereMat)
  root.add(sphere)

  // Fresnel rim atmosphere
  const rimMat = track(
    new THREE.ShaderMaterial({
      uniforms: {
        uColor: { value: new THREE.Color(BLOOD) },
        uIntensity: { value: 0.55 },
      },
      vertexShader: `
        varying vec3 vN;
        void main() {
          vN = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }`,
      fragmentShader: `
        uniform vec3 uColor;
        uniform float uIntensity;
        varying vec3 vN;
        void main() {
          float f = pow(clamp(1.0 - abs(vN.z), 0.0, 1.0), 2.6);
          gl_FragColor = vec4(uColor, f * uIntensity);
        }`,
      transparent: true,
      blending: THREE.NormalBlending,
      depthWrite: false,
    }),
  )
  const rimMesh = new THREE.Mesh(track(new THREE.SphereGeometry(1.045, 64, 48)), rimMat)
  root.add(rimMesh)

  // Glowing core (ignites in chapter 2)
  const coreMat = track(
    new THREE.MeshStandardMaterial({
      color: 0x74070e,
      emissive: new THREE.Color(BLOOD),
      emissiveIntensity: 0,
      roughness: 0.4,
    }),
  )
  const core = new THREE.Mesh(track(new THREE.IcosahedronGeometry(0.42, 4)), coreMat)
  root.add(core)
  const coreGlowMat = track(
    new THREE.PointsMaterial({
      size: 2.6,
      map: glowTex,
      color: BLOOD,
      transparent: true,
      opacity: 0,
      depthWrite: false,
      blending: THREE.NormalBlending,
      sizeAttenuation: true,
    }),
  )
  const coreGlow = new THREE.Points(track(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3()])), coreGlowMat)
  root.add(coreGlow)

  // Governance meridians (draw-on)
  const meridianGeo = track(buildMeridians(1.008, 7, 12, 96))
  const meridianCount = meridianGeo.getAttribute('position').count
  meridianGeo.setDrawRange(0, 0)
  const meridianMat = track(
    new THREE.LineBasicMaterial({
      color: BLOOD,
      transparent: true,
      opacity: 0,
      blending: THREE.NormalBlending,
      depthWrite: false,
    }),
  )
  root.add(new THREE.LineSegments(meridianGeo, meridianMat))

  // Orbital ring + travelling club nodes
  const ringGroup = new THREE.Group()
  ringGroup.rotation.set(0.34, 0, 0.46)
  root.add(ringGroup)
  const ringMat = track(
    new THREE.MeshBasicMaterial({ color: ROSE, transparent: true, opacity: 0 }),
  )
  const ring = new THREE.Mesh(track(new THREE.TorusGeometry(1.62, 0.0045, 8, 240)), ringMat)
  ring.rotation.x = Math.PI / 2
  ringGroup.add(ring)

  const NODE_COUNT = mobile ? 10 : 14
  const nodeGeo = track(new THREE.BufferGeometry())
  nodeGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(NODE_COUNT * 3), 3))
  const nodeMat = track(
    new THREE.PointsMaterial({
      size: 0.16,
      map: glowTex,
      color: BLOOD,
      transparent: true,
      opacity: 0,
      depthWrite: false,
      blending: THREE.NormalBlending,
      sizeAttenuation: true,
    }),
  )
  ringGroup.add(new THREE.Points(nodeGeo, nodeMat))
  const nodeAngles = Array.from({ length: NODE_COUNT }, (_, i) => (i / NODE_COUNT) * TAU)

  // Member constellation + connections + pulses
  const memberPoints = shellPoints(mobile ? 30 : 46, 2.0, 2.5)
  const memberGeo = track(new THREE.BufferGeometry().setFromPoints(memberPoints))
  const memberMat = track(
    new THREE.PointsMaterial({
      size: 0.12,
      map: glowTex,
      color: OLIVE,
      transparent: true,
      opacity: 0,
      depthWrite: false,
      blending: THREE.NormalBlending,
      sizeAttenuation: true,
    }),
  )
  const members = new THREE.Points(memberGeo, memberMat)
  root.add(members)

  const connections: Array<[THREE.Vector3, THREE.Vector3]> = []
  for (let i = 0; i < memberPoints.length; i++) {
    const dists = memberPoints
      .map((p, j) => ({ j, d: j === i ? Infinity : p.distanceToSquared(memberPoints[i]) }))
      .sort((a, b) => a.d - b.d)
    for (const { j, d } of dists.slice(0, 2)) {
      if (d < 1.1 && j > i) connections.push([memberPoints[i], memberPoints[j]])
    }
  }
  const connPositions: number[] = []
  for (const [a, b] of connections) connPositions.push(a.x, a.y, a.z, b.x, b.y, b.z)
  const connGeo = track(new THREE.BufferGeometry())
  connGeo.setAttribute('position', new THREE.Float32BufferAttribute(connPositions, 3))
  connGeo.setDrawRange(0, 0)
  const connMat = track(
    new THREE.LineBasicMaterial({
      color: BLOOD,
      transparent: true,
      opacity: 0,
      blending: THREE.NormalBlending,
      depthWrite: false,
    }),
  )
  members.add(new THREE.LineSegments(connGeo, connMat))

  const PULSE_COUNT = mobile ? 6 : 10
  const pulseGeo = track(new THREE.BufferGeometry())
  pulseGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(PULSE_COUNT * 3), 3))
  const pulseMat = track(
    new THREE.PointsMaterial({
      size: 0.14,
      map: glowTex,
      color: BLOOD,
      transparent: true,
      opacity: 0,
      depthWrite: false,
      blending: THREE.NormalBlending,
      sizeAttenuation: true,
    }),
  )
  members.add(new THREE.Points(pulseGeo, pulseMat))
  const pulseSeeds = Array.from({ length: PULSE_COUNT }, (_, i) => ({
    link: (i * 7) % Math.max(1, connections.length),
    phase: i / PULSE_COUNT,
  }))

  // Compliance shell
  const shellEdges = track(new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(2.75, 2)))
  const shellMat = track(
    new THREE.LineBasicMaterial({
      color: BLOOD,
      transparent: true,
      opacity: 0,
      blending: THREE.NormalBlending,
      depthWrite: false,
    }),
  )
  const shell = new THREE.LineSegments(shellEdges, shellMat)
  root.add(shell)

  // Starfield
  const STAR_COUNT = mobile ? 500 : 900
  const rng = mulberry32(7)
  const starPositions = new Float32Array(STAR_COUNT * 3)
  for (let i = 0; i < STAR_COUNT; i++) {
    // Uniform-ish distribution on a large shell (u = cos θ, uniform in [-1,1]).
    const u = rng() * 2 - 1
    const theta = rng() * TAU
    const ring = Math.sqrt(Math.max(0, 1 - u * u))
    const radius = 16 + rng() * 18
    starPositions[i * 3] = Math.cos(theta) * ring * radius
    starPositions[i * 3 + 1] = u * radius
    starPositions[i * 3 + 2] = Math.sin(theta) * ring * radius
  }
  const starGeo = track(new THREE.BufferGeometry())
  starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3))
  const starMat = track(
    new THREE.PointsMaterial({
      size: 0.09,
      map: glowTex,
      color: 0x947268,
      transparent: true,
      opacity: 0.65,
      depthWrite: false,
      blending: THREE.NormalBlending,
      sizeAttenuation: true,
    }),
  )
  const stars = new THREE.Points(starGeo, starMat)
  scene.add(stars)

  /* ── post ───────────────────────────────────────────── */
  const composer = new EffectComposer(renderer)
  composer.addPass(new RenderPass(scene, camera))
  // Bloom is the heaviest pass; skip it on low-power phones and lean on the
  // emissive core + additive glows to keep the finale luminous.
  const bloom = lowPower ? null : new UnrealBloomPass(new THREE.Vector2(1, 1), 0, 0.6, 1)
  if (bloom) composer.addPass(bloom)
  composer.addPass(new OutputPass())

  /* ── state ──────────────────────────────────────────── */
  let progress = 0
  let elapsed = 0

  const tmp = new THREE.Vector3()

  return {
    setProgress(p: number) {
      progress = Math.min(1, Math.max(0, p))
    },

    render(dt: number) {
      elapsed += dt
      const p = progress

      const ignite = smoothstep(0.1, 0.22, p)
      const meridians = smoothstep(0.22, 0.4, p)
      const ringIn = smoothstep(0.38, 0.56, p)
      const constellation = smoothstep(0.54, 0.72, p)
      const shellIn = smoothstep(0.7, 0.86, p)
      const finale = smoothstep(0.86, 1, p)

      // Camera: one continuous orbit + pull-back, no cuts.
      const azimuth = -0.55 + p * 1.5 + (reduceMotion ? 0 : Math.sin(elapsed * 0.05) * 0.02)
      // Keep the core sphere fully in frame on portrait screens: solve for the
      // distance at which the horizontal half-FOV still covers the sphere.
      const fovDeg = 42 - finale * 4
      const halfWidth = Math.tan(((fovDeg * Math.PI) / 180) / 2) * camera.aspect
      const minRadius = 1.28 / Math.max(halfWidth, 0.0001)
      const radius = Math.max(4.35 + p * 3.5, minRadius)
      const height = 0.35 + Math.sin(p * Math.PI) * 0.45 + p * 0.95
      camera.position.set(Math.sin(azimuth) * radius, height, Math.cos(azimuth) * radius)
      camera.lookAt(0, 0.05 + p * 0.12, 0)
      camera.fov = fovDeg
      camera.updateProjectionMatrix()

      // Idle life — skipped entirely when the user prefers reduced motion.
      if (!reduceMotion) {
        root.rotation.y += dt * 0.035
        shell.rotation.y -= dt * 0.02
        stars.rotation.y += dt * 0.004
        core.rotation.y -= dt * 0.15
      }
      const pulse = reduceMotion ? 1 : 1 + Math.sin(elapsed * 2.1) * 0.04

      // Ignition.
      coreMat.emissiveIntensity = ignite * (2.1 + (reduceMotion ? 0 : Math.sin(elapsed * 1.7) * 0.25))
      coreGlowMat.opacity = ignite * 0.85
      core.scale.setScalar((0.6 + ignite * 0.4) * pulse)
      coreGlow.scale.setScalar(pulse)
      coreLight.intensity = ignite * 7
      rimMat.uniforms.uIntensity.value = 0.35 + ignite * 0.5 + finale * 0.25

      // Meridians draw-on.
      meridianMat.opacity = meridians * 0.8
      meridianGeo.setDrawRange(0, Math.floor(meridianCount * meridians))

      // Ring + nodes.
      ringMat.opacity = ringIn * 0.9
      nodeMat.opacity = ringIn * 0.95
      const ringSpin = reduceMotion ? 0 : elapsed * 0.22
      const pos = nodeGeo.getAttribute('position') as THREE.BufferAttribute
      for (let i = 0; i < NODE_COUNT; i++) {
        const a = nodeAngles[i] + ringSpin
        // Torus lies in the XY plane after ring.rotation.x = PI/2 → nodes travel on it.
        pos.setXYZ(i, Math.cos(a) * 1.62, Math.sin(a) * 1.62, 0)
      }
      pos.needsUpdate = true

      // Constellation.
      memberMat.opacity = constellation * 0.8
      connMat.opacity = constellation * 0.72
      connGeo.setDrawRange(0, Math.floor((connPositions.length / 6) * 2 * constellation))
      pulseMat.opacity = constellation * 0.9
      const ppos = pulseGeo.getAttribute('position') as THREE.BufferAttribute
      for (let i = 0; i < PULSE_COUNT; i++) {
        const { link, phase } = pulseSeeds[i]
        const [a, b] = connections[link] ?? connections[0]
        if (!a || !b) continue
        const t = reduceMotion ? phase : (elapsed * 0.35 + phase) % 1
        tmp.lerpVectors(a, b, t)
        ppos.setXYZ(i, tmp.x, tmp.y, tmp.z)
      }
      ppos.needsUpdate = true

      // Shell.
      shellMat.opacity = shellIn * 0.62 + finale * 0.13

      // Finale lift.
      if (bloom) bloom.strength = 0
      renderer.toneMappingExposure = 1.05 + finale * 0.12

      composer.render()
    },

    resize(width: number, height: number) {
      if (width === 0 || height === 0) return
      camera.aspect = width / height
      camera.updateProjectionMatrix()
      renderer.setSize(width, height, false)
      composer.setSize(width, height)
      bloom?.setSize(width, height)
    },

    dispose() {
      for (const d of disposables) d.dispose()
      composer.dispose()
      scene.clear()
      renderer.dispose()
    },
  }
}
