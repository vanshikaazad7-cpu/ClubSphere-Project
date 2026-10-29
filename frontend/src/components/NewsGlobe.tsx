import { useEffect, useRef, type RefObject } from 'react'
import * as THREE from 'three'

import { createNewspaperTexture } from './newspaperTexture'

export default function NewsGlobe({ className = '', scrollProgress }: { className?: string; scrollProgress?: RefObject<number> }) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    // Scene setup
    const scene = new THREE.Scene()

    // Dimensions
    const initialWidth = container.clientWidth || 300
    const initialHeight = container.clientHeight || 300

    // Camera: FOV 45, positioned at z=7
    const camera = new THREE.PerspectiveCamera(45, initialWidth / initialHeight, 0.1, 1000)
    camera.position.set(0, 0, 8.8)

    // Renderer with transparent background (alpha: true)
    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' })
    } catch {
      container.dataset.unavailable = 'true'
      return
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(initialWidth, initialHeight)
    renderer.setClearColor(0x000000, 0)
    renderer.domElement.style.width = '100%'
    renderer.domElement.style.height = '100%'
    renderer.domElement.style.display = 'block'
    container.appendChild(renderer.domElement)

    // Lighting for warm editorial look
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.4)
    scene.add(ambientLight)

    const mainLight = new THREE.DirectionalLight(0xffffff, 1.6)
    mainLight.position.set(5, 5, 6)
    scene.add(mainLight)

    const fillLight = new THREE.DirectionalLight(0xffffff, 0.6)
    fillLight.position.set(-5, -3, -4)
    scene.add(fillLight)

    // Sphere: radius 2.8, 64 segments
    const geometry = new THREE.SphereGeometry(2.8, 64, 64)
    const texture = createNewspaperTexture()
    texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy())

    // MeshStandardMaterial with slight roughness (0.7) and metalness (0.05)
    const material = new THREE.MeshStandardMaterial({
      map: texture,
      roughness: 0.7,
      metalness: 0.05,
    })

    const sphere = new THREE.Mesh(geometry, material)
    // Subtle initial tilt for natural editorial globe posture
    sphere.rotation.x = 0.1
    scene.add(sphere)

    // Drag-to-rotate interaction state
    let isDragging = false
    let dragRotation = 0
    let previousPointerPosition = { x: 0, y: 0 }

    const handlePointerDown = (e: PointerEvent) => {
      isDragging = true
      previousPointerPosition = { x: e.clientX, y: e.clientY }
      container.style.cursor = 'grabbing'
      try {
        container.setPointerCapture(e.pointerId)
      } catch {
        // Safe fallback
      }
    }

    const handlePointerMove = (e: PointerEvent) => {
      if (!isDragging) return
      const deltaX = e.clientX - previousPointerPosition.x
      const deltaY = e.clientY - previousPointerPosition.y
      previousPointerPosition = { x: e.clientX, y: e.clientY }

      dragRotation += deltaX * 0.005
      sphere.rotation.y += deltaX * 0.005
      sphere.rotation.x = Math.max(-0.7, Math.min(0.7, sphere.rotation.x + deltaY * 0.005))
    }

    const handlePointerUp = (e: PointerEvent) => {
      if (isDragging) {
        isDragging = false
        container.style.cursor = 'grab'
        try {
          container.releasePointerCapture(e.pointerId)
        } catch {
          // Safe fallback
        }
      }
    }

    container.style.cursor = 'grab'
    container.style.touchAction = 'pan-y'

    container.addEventListener('pointerdown', handlePointerDown)
    container.addEventListener('pointermove', handlePointerMove)
    container.addEventListener('pointerup', handlePointerUp)
    container.addEventListener('pointercancel', handlePointerUp)

    // Resize handling via ResizeObserver
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        if (width > 0 && height > 0) {
          camera.aspect = width / height
          camera.updateProjectionMatrix()
          renderer.setSize(width, height, false)
        }
      }
    })
    resizeObserver.observe(container)

    // Animation loop: auto-rotates slowly (0.002 radians/frame on Y axis)
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
    let visible = false
    const observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting })
    observer.observe(container)
    let previousTime = performance.now()
    let animationFrameId = 0
    const animate = (time: number) => {
      animationFrameId = requestAnimationFrame(animate)

      const elapsed = Math.min((time - previousTime) / 1000, 0.1)
      previousTime = time
      if (!visible || document.hidden) return
      if (scrollProgress) {
        const target = scrollProgress.current * Math.PI * 2 + dragRotation
        sphere.rotation.y += (target - sphere.rotation.y) * (reducedMotion.matches ? 1 : Math.min(1, elapsed * 8))
        const scale = 0.94 + Math.sin(scrollProgress.current * Math.PI) * 0.06
        sphere.scale.setScalar(scale)
      } else if (!isDragging && !reducedMotion.matches) sphere.rotation.y += elapsed * 0.12
      renderer.render(scene, camera)
    }
    animationFrameId = requestAnimationFrame(animate)

    // Proper cleanup on unmount
    return () => {
      cancelAnimationFrame(animationFrameId)
      resizeObserver.disconnect()
      observer.disconnect()

      container.removeEventListener('pointerdown', handlePointerDown)
      container.removeEventListener('pointermove', handlePointerMove)
      container.removeEventListener('pointerup', handlePointerUp)
      container.removeEventListener('pointercancel', handlePointerUp)

      geometry.dispose()
      material.dispose()
      texture.dispose()
      renderer.dispose()

      if (renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement)
      }
    }
  }, [scrollProgress])

  return (
    <div ref={containerRef} className={className} role="img" aria-label="A rotating globe of campus newspaper clippings. Drag horizontally to rotate.">
      <div className="ed-globe-fallback" aria-hidden="true"><span>Ideas.<br />People.<br />Stories.</span></div>
    </div>
  )
}
