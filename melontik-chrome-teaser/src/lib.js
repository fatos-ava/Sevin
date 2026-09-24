/* Deterministic helpers for the Melontik teaser renderer. Everything is a pure function of time. */
(function (global) {
  const TAU = Math.PI * 2;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const mix = lerp;
  const smoothstep = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
  // progress of t inside [a,b] -> 0..1
  const span = (t, a, b) => clamp((t - a) / (b - a), 0, 1);

  const ease = {
    linear: t => t,
    inQuad: t => t * t,
    outQuad: t => 1 - (1 - t) * (1 - t),
    inOutQuad: t => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2,
    inCubic: t => t * t * t,
    outCubic: t => 1 - Math.pow(1 - t, 3),
    inOutCubic: t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
    outQuart: t => 1 - Math.pow(1 - t, 4),
    inQuart: t => t * t * t * t,
    inOutQuart: t => t < 0.5 ? 8 * t * t * t * t : 1 - Math.pow(-2 * t + 2, 4) / 2,
    outQuint: t => 1 - Math.pow(1 - t, 5),
    inQuint: t => t * t * t * t * t,
    inExpo: t => t === 0 ? 0 : Math.pow(2, 10 * t - 10),
    outExpo: t => t === 1 ? 1 : 1 - Math.pow(2, -10 * t),
    inOutExpo: t => t === 0 ? 0 : t === 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2,
    inOutSine: t => -(Math.cos(Math.PI * t) - 1) / 2,
    outSine: t => Math.sin((t * Math.PI) / 2),
    outBack: t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
    outElastic: t => t === 0 ? 0 : t === 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (TAU / 3)) + 1,
  };

  // Deterministic PRNG (mulberry32)
  function rng(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // Smooth 1-D noise from layered sines (deterministic, cheap). Range about -1..1
  function noise1(t, seed = 0) {
    const s = seed * 12.9898;
    return (Math.sin(t * 1.0 + s) * 0.5 + Math.sin(t * 2.3 + s * 1.7 + 1.3) * 0.3 + Math.sin(t * 4.7 + s * 0.3 + 2.1) * 0.15 + Math.sin(t * 9.1 + s * 2.9 + 0.7) * 0.05);
  }
  // Smooth 2-D-ish noise (value noise built from sines) for fluid backgrounds. Range about -1..1
  function noise2(x, y, t) {
    return (
      Math.sin(x * 1.3 + t * 0.7) * 0.35 +
      Math.sin(y * 1.7 - t * 0.5 + x * 0.6) * 0.3 +
      Math.sin((x + y) * 0.9 + t * 0.9 + 1.7) * 0.2 +
      Math.sin(x * 2.9 - y * 2.1 + t * 1.3 + 4.1) * 0.15
    );
  }

  function roundRect(ctx, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  // Radial soft glow
  function glow(ctx, x, y, r, color, alpha = 1, inner = 0) {
    const g = ctx.createRadialGradient(x, y, r * inner, x, y, r);
    g.addColorStop(0, withAlpha(color, alpha));
    g.addColorStop(0.35, withAlpha(color, alpha * 0.45));
    g.addColorStop(1, withAlpha(color, 0));
    ctx.fillStyle = g;
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }

  function hexToRgb(hex) {
    const h = hex.replace('#', '');
    const n = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function withAlpha(hex, a) {
    if (hex.startsWith('rgba') || hex.startsWith('rgb')) return hex;
    const [r, g, b] = hexToRgb(hex);
    return `rgba(${r},${g},${b},${clamp(a, 0, 1)})`;
  }
  function mixHex(h1, h2, t) {
    const a = hexToRgb(h1), b = hexToRgb(h2);
    return `rgb(${Math.round(lerp(a[0], b[0], t))},${Math.round(lerp(a[1], b[1], t))},${Math.round(lerp(a[2], b[2], t))})`;
  }

  // Vignette (multiply-style darkening at the edges)
  function vignette(ctx, w, h, strength = 0.6, radius = 0.75) {
    const g = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.2, w / 2, h / 2, Math.max(w, h) * radius);
    g.addColorStop(0, 'rgba(0,0,0,0)');
    g.addColorStop(1, `rgba(0,0,0,${strength})`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  }

  // Film grain: pre-rendered noise tiles, chosen per frame index, drawn with low alpha.
  const grainTiles = [];
  function ensureGrain(size = 256, count = 6) {
    if (grainTiles.length) return;
    const r = rng(1337);
    for (let i = 0; i < count; i++) {
      const c = document.createElement('canvas'); c.width = size; c.height = size;
      const cx = c.getContext('2d');
      const img = cx.createImageData(size, size);
      for (let p = 0; p < img.data.length; p += 4) {
        const v = 128 + (r() - 0.5) * 255;
        img.data[p] = img.data[p + 1] = img.data[p + 2] = v; img.data[p + 3] = 255;
      }
      cx.putImageData(img, 0, 0);
      grainTiles.push(c);
    }
  }
  function grain(ctx, w, h, frameIndex, amount = 0.06) {
    ensureGrain();
    const tile = grainTiles[frameIndex % grainTiles.length];
    ctx.save();
    ctx.globalCompositeOperation = 'overlay';
    ctx.globalAlpha = amount;
    const pat = ctx.createPattern(tile, 'repeat');
    // offset pattern per frame so it never looks static
    const ox = (frameIndex * 37) % 256, oy = (frameIndex * 91) % 256;
    ctx.translate(-ox, -oy);
    ctx.fillStyle = pat;
    ctx.fillRect(0, 0, w + 256, h + 256);
    ctx.restore();
  }

  // Text with letter spacing (Chromium supports ctx.letterSpacing)
  function text(ctx, str, x, y, opts = {}) {
    ctx.save();
    ctx.font = opts.font || '600 48px Montserrat';
    ctx.fillStyle = opts.color || '#fff';
    ctx.textAlign = opts.align || 'center';
    ctx.textBaseline = opts.baseline || 'alphabetic';
    if (opts.letterSpacing != null) ctx.letterSpacing = opts.letterSpacing + 'px';
    if (opts.alpha != null) ctx.globalAlpha *= opts.alpha;
    if (opts.blur) ctx.filter = `blur(${opts.blur}px)`;
    if (opts.shadow) { ctx.shadowColor = opts.shadow.color; ctx.shadowBlur = opts.shadow.blur; ctx.shadowOffsetX = opts.shadow.x || 0; ctx.shadowOffsetY = opts.shadow.y || 0; }
    ctx.fillText(str, x, y);
    ctx.restore();
  }
  function measure(ctx, str, font, letterSpacing = 0) {
    ctx.save(); ctx.font = font; ctx.letterSpacing = letterSpacing + 'px';
    const m = ctx.measureText(str); ctx.restore(); return m.width;
  }

  // Melontik logo mark: coral disc with a pale "%" whose slash is an upward arrow. R = disc radius.
  function logoMark(ctx, cx, cy, R, fill = '#FD7755', glyph = '#FEE3DC', glyphAlpha = 1) {
    ctx.save(); ctx.translate(cx, cy);
    if (fill) { ctx.fillStyle = fill; ctx.beginPath(); ctx.arc(0, 0, R, 0, TAU); ctx.fill(); }
    ctx.globalAlpha *= glyphAlpha;
    ctx.strokeStyle = glyph; ctx.fillStyle = glyph; ctx.lineCap = 'butt'; ctx.lineJoin = 'miter';
    const w = 0.137 * R;
    ctx.lineWidth = w;
    ctx.beginPath(); ctx.arc(-0.287 * R, -0.287 * R, 0.19 * R, 0, TAU); ctx.stroke();
    ctx.beginPath(); ctx.arc(0.313 * R, 0.313 * R, 0.19 * R, 0, TAU); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(-0.327 * R, 0.358 * R); ctx.lineTo(0.30 * R, -0.27 * R); ctx.stroke();
    const ox = 0.43 * R, oy = -0.40 * R, arm = 0.32 * R;
    ctx.fillRect(ox - arm, oy, arm, w);
    ctx.fillRect(ox - w, oy, w, arm);
    ctx.restore();
  }
  // Only the glyph (for outlines / light tracing), same geometry, stroked paths
  function logoGlyphPath(ctx, cx, cy, R) {
    ctx.translate(cx, cy);
    ctx.beginPath(); ctx.arc(-0.287 * R, -0.287 * R, 0.19 * R, 0, TAU);
    ctx.moveTo(0.313 * R + 0.19 * R, 0.313 * R); ctx.arc(0.313 * R, 0.313 * R, 0.19 * R, 0, TAU);
    ctx.moveTo(-0.327 * R, 0.358 * R); ctx.lineTo(0.30 * R, -0.27 * R);
    const ox = 0.43 * R, oy = -0.40 * R, arm = 0.32 * R, w = 0.137 * R;
    ctx.moveTo(ox - arm, oy + w / 2); ctx.lineTo(ox - w / 2, oy + w / 2); ctx.lineTo(ox - w / 2, oy + arm);
    ctx.translate(-cx, -cy);
  }

  // Draw an image fragment with a rounded-rect mask, optional soft edge (feather) and tint.
  function fragment(ctx, img, opts) {
    const { x, y, w, h, radius = 24, alpha = 1, rot = 0, feather = 0, blur = 0, scale = 1 } = opts;
    ctx.save();
    ctx.translate(x, y); ctx.rotate(rot); ctx.scale(scale, scale);
    ctx.globalAlpha *= alpha;
    if (blur) ctx.filter = `blur(${blur}px)`;
    roundRect(ctx, -w / 2, -h / 2, w, h, radius); ctx.clip();
    ctx.drawImage(img, -w / 2, -h / 2, w, h);
    if (feather > 0) {
      // fade edges to transparent using destination-in with a gradient frame
      ctx.filter = 'none';
      ctx.globalCompositeOperation = 'destination-in';
      const g = ctx.createRadialGradient(0, 0, Math.min(w, h) * 0.1, 0, 0, Math.max(w, h) * 0.6);
      g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1 - feather, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.fillRect(-w, -h, w * 2, h * 2);
    }
    ctx.restore();
  }

  // Beam of light: a long, soft, rotated gradient bar
  function beam(ctx, x, y, len, width, angle, color, alpha, softness = 0.5) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(angle);
    ctx.globalCompositeOperation = 'lighter';
    const g = ctx.createLinearGradient(0, -width / 2, 0, width / 2);
    g.addColorStop(0, withAlpha(color, 0));
    g.addColorStop(0.5 - softness * 0.5, withAlpha(color, alpha));
    g.addColorStop(0.5, withAlpha(color, alpha));
    g.addColorStop(0.5 + softness * 0.5, withAlpha(color, alpha));
    g.addColorStop(1, withAlpha(color, 0));
    ctx.fillStyle = g;
    const gl = ctx.createLinearGradient(-len / 2, 0, len / 2, 0);
    gl.addColorStop(0, 'rgba(0,0,0,0)'); gl.addColorStop(0.2, 'rgba(0,0,0,1)'); gl.addColorStop(0.8, 'rgba(0,0,0,1)'); gl.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillRect(-len / 2, -width / 2, len, width);
    ctx.globalCompositeOperation = 'destination-in';
    // fade the ends (applied only inside the current path region is not possible; so use a temp canvas approach in callers if needed)
    ctx.restore();
  }

  global.L = { TAU, clamp, lerp, mix, smoothstep, span, ease, rng, noise1, noise2, roundRect, glow, withAlpha, hexToRgb, mixHex, vignette, grain, text, measure, logoMark, logoGlyphPath, fragment, beam };
})(window);
