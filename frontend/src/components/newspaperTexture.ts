import * as THREE from 'three'

/** Shared, deterministic newspaper collage for both the film and editorial globe. */
export function createNewspaperTexture(): THREE.CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = 4096
  canvas.height = 2048
  const ctx = canvas.getContext('2d')!
  let seed = 73
  const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296 }
  const colors = ['#eee2c7', '#f1e6cc', '#d7c3a3', '#947268', '#74070E', '#45462A']
  const headlines = [
    'A Brighter Campus Together', 'Global Minds Local Impact',
    'Students Build a More Inclusive Tomorrow', 'People Create Brighter Tomorrows',
    'Good Ideas Belong Here', 'More Than A Degree', 'Ideas Travel Further Here',
    'The Campus Chronicle', 'A Community of Changemakers', 'Culture Without Borders',
    'New Voices New Possibilities', 'Small Clubs. Big Change.',
  ]
  const story = 'Across campus students are bringing fresh ideas to life. Through shared curiosity and creative collaboration our community discovers new ways to learn connect and make a lasting difference. Every voice belongs in the story.'
  ctx.fillStyle = '#eee2c7'
  ctx.fillRect(0, 0, 4096, 2048)

  function wrapped(text: string, x: number, y: number, width: number, lineHeight: number, maxLines: number) {
    const words = text.split(' ')
    let line = '', count = 0
    for (const word of words) {
      const next = line ? `${line} ${word}` : word
      if (ctx.measureText(next).width > width && line) {
        ctx.fillText(line, x, y + count * lineHeight)
        count++
        if (count >= maxLines) return y + count * lineHeight
        line = word
      } else line = next
    }
    if (count < maxLines) ctx.fillText(line, x, y + count++ * lineHeight)
    return y + count * lineHeight
  }

  // Etched campus buildings and student gatherings, rather than repeated glowing-orb stills.
  function engraving(x: number, y: number, w: number, h: number, variant: number) {
    ctx.save()
    ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip()
    const sky = ctx.createLinearGradient(0, y, 0, y + h)
    sky.addColorStop(0, '#d8ceb9'); sky.addColorStop(1, '#8e806b')
    ctx.fillStyle = sky; ctx.fillRect(x, y, w, h)
    ctx.fillStyle = '#413b2e'
    if (variant % 2 === 0) {
      // Portico, pediment, windows, and columns of a university building.
      ctx.fillRect(x + w * .1, y + h * .4, w * .8, h * .54)
      ctx.beginPath(); ctx.moveTo(x + w * .06, y + h * .42)
      ctx.lineTo(x + w * .5, y + h * .1); ctx.lineTo(x + w * .94, y + h * .42); ctx.fill()
      ctx.fillStyle = '#d8c7a6'
      for (let i = 0; i < 7; i++) {
        ctx.fillRect(x + w * (.17 + i * .105), y + h * .46, w * .035, h * .41)
        ctx.fillRect(x + w * (.16 + i * .105), y + h * .88, w * .06, h * .035)
      }
      ctx.fillStyle = '#27271f'; ctx.fillRect(x, y + h * .95, w, h * .05)
    } else {
      for (let row = 0; row < 3; row++) {
        for (let i = 0; i < 9; i++) {
          const cx = x + (i + .5 + (row % 2) * .3) * w / 9
          const cy = y + h * (.22 + row * .28)
          const r = w * (.025 + random() * .012)
          ctx.fillStyle = ['#333027', '#5b5142', '#b4a489'][Math.floor(random() * 3)]
          ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill()
          ctx.beginPath(); ctx.ellipse(cx, cy + r * 2.8, r * 1.65, r * 2.5, 0, 0, Math.PI * 2); ctx.fill()
        }
      }
    }
    // Printed halftone and cross-hatching give the clippings an ink-on-paper finish.
    ctx.fillStyle = '#211d1844'
    for (let yy = y; yy < y + h; yy += 4) {
      for (let xx = x; xx < x + w; xx += 4) ctx.fillRect(xx, yy, 1, 1)
    }
    ctx.strokeStyle = '#f1e6cc44'; ctx.lineWidth = .5
    for (let i = -h; i < w; i += 5) {
      ctx.beginPath(); ctx.moveTo(x + i, y); ctx.lineTo(x + i + h, y + h); ctx.stroke()
    }
    ctx.restore()
  }

  const columns = 16, rows = 5, cellW = 4096 / columns, cellH = 2048 / rows
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < columns; col++) {
      const index = row * columns + col
      const x = col * cellW, y = row * cellH
      const panel = (col * 3 + row * 5) % colors.length
      const dark = panel >= 3
      const ink = dark ? '#f4e3b2' : '#310e10'
      ctx.fillStyle = colors[panel]; ctx.fillRect(x + 3, y + 3, cellW - 6, cellH - 6)
      ctx.strokeStyle = '#55473088'; ctx.lineWidth = 1
      ctx.strokeRect(x + 5, y + 5, cellW - 10, cellH - 10)
      ctx.fillStyle = ink
      ctx.font = '10px Georgia'; ctx.fillText('CLUBSPHERE  /  CAMPUS CULTURE', x + 14, y + 22)
      ctx.fillRect(x + 14, y + 29, cellW - 28, 1)
      const photoFirst = index % 3 === 0
      let cursor = y + 60
      if (photoFirst) {
        engraving(x + 14, y + 40, cellW - 28, 140, index)
        cursor = y + 210
      }
      ctx.fillStyle = ink
      ctx.font = `${index % 2 ? 'italic ' : ''}bold ${photoFirst ? 27 : 34}px Georgia`
      cursor = wrapped(headlines[index % headlines.length], x + 14, cursor, cellW - 28, photoFirst ? 29 : 35, 5) + 9
      if (!photoFirst && index % 2 === 0) {
        engraving(x + 14, cursor, cellW - 28, 115, index + row)
        cursor += 132
      }
      ctx.fillStyle = ink
      // Two narrow columns of actual typeset article text.
      ctx.font = '12px Georgia'
      const bodyWidth = (cellW - 36) / 2
      const remaining = Math.max(0, Math.floor((y + cellH - 23 - cursor) / 14))
      wrapped(story, x + 14, cursor, bodyWidth, 14, remaining)
      wrapped(story.split(' ').slice(12).join(' '), x + 22 + bodyWidth, cursor, bodyWidth, 14, remaining)
      ctx.fillRect(x + 14, y + cellH - 18, cellW - 28, 1)
      ctx.font = '9px Georgia'; ctx.fillText(`INDEPENDENT VOICES • VOL. 01 • ${index + 1}`, x + 14, y + cellH - 7)
    }
  }
  // Fine fibers and ink variation without obscuring the typography.
  for (let i = 0; i < 65000; i++) {
    ctx.fillStyle = random() > .5 ? '#fff8e414' : '#39271814'
    ctx.fillRect(random() * 4096, random() * 2048, 1 + random() * 2, 1)
  }
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  texture.wrapS = THREE.RepeatWrapping
  texture.minFilter = THREE.LinearMipmapLinearFilter
  texture.anisotropy = 8
  return texture
}
