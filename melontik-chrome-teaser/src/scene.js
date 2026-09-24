/* Melontik Chrome extension teaser, 9:16, 15 s. Scene = pure function of time (render(t, frameIndex)). */
(function (global) {
  const W = 1080, H = 1920, CX = 540, CY = 960;
  const SAFE_TOP = 250, SAFE_BOTTOM = 1580;
  const { TAU, clamp, lerp, smoothstep, span, ease, rng, noise1, roundRect, glow, withAlpha, vignette, grain, logoMark, measure } = window.L;
  const d2r = d => d * Math.PI / 180;

  function create(ctx, canvas, A, tl) {
    const C = tl.brand;
    const CORAL = C.coral, PALE = C.pale, INK = C.ink, GREEN = C.green;
    const WARM = '#FFF7F4';
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';

    // ---------- offscreen canvases ----------
    const mk = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
    const hazeC = mk(270, 480), hz = hazeC.getContext('2d');
    const beamC = mk(540, 960), bm = beamC.getContext('2d');
    const fxC = mk(W, H), fx = fxC.getContext('2d');
    const fx2C = mk(W, H), fx2 = fx2C.getContext('2d');
    [fx, fx2].forEach(c => { c.imageSmoothingEnabled = true; c.imageSmoothingQuality = 'high'; });

    // ---------- deterministic particles ----------
    const R1 = rng(2024);
    const motes = Array.from({ length: 140 }, (_, i) => ({
      x0: R1() * W, y0: R1() * H, z: 0.3 + R1() * 1.3, vy: 6 + R1() * 8, ph: R1() * TAU, w: 2 + R1() * 3, coral: R1() < 0.12, tw: 2 + R1() * 3,
    }));
    const bokehSeeds = Array.from({ length: 12 }, () => ({ x: R1(), y: R1(), r: 40 + R1() * 60, ph: R1() * TAU, sp: 0.2 + R1() * 0.4 }));

    // ---------- camera ----------
    function camera(t) {
      // returns { zoom, roll(rad), dx, dy } — dolly-ins per shot
      let zoom = 1, roll = 0, dx = 0, dy = 0;
      const s = (a, b) => span(t, a, b);
      if (t < 3) zoom = lerp(1.0, 1.04, ease.inOutSine(s(1, 3)));
      else if (t < 4) zoom = lerp(1.0, 1.06, ease.outSine(s(3, 4)));
      else if (t < 5) { zoom = lerp(1.0, 1.03, s(4, 5)); roll = d2r(lerp(-1, 1, s(4, 5))); }
      else if (t < 6) zoom = lerp(1.0, 1.04, s(5, 6));
      else if (t < 7) { zoom = lerp(1.0, 1.05, s(6, 7)); roll = d2r(lerp(0, 2, s(6, 7))); }
      else if (t < 8) { zoom = lerp(1.0, 1.03, s(7, 8)); roll = d2r(lerp(0, 1.5, s(7, 8))); }
      else if (t < 8.5) zoom = lerp(1.0, 1.08, ease.inQuad(s(8, 8.5)));
      else if (t < 9) zoom = lerp(1.08, 1.14, ease.inExpo(s(8.5, 9)));
      return { zoom, roll, dx, dy };
    }
    function applyCamera(cm) { ctx.translate(CX + cm.dx, CY + cm.dy); ctx.rotate(cm.roll); ctx.scale(cm.zoom, cm.zoom); ctx.translate(-CX, -CY); }

    // ---------- background ----------
    function drawBase(t) {
      const g = ctx.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0, '#0B0605'); g.addColorStop(1, '#150A08');
      ctx.fillStyle = g; ctx.fillRect(-200, -200, W + 400, H + 400);
    }
    function drawHaze(t, amount = 1, ribbonAlpha = 1) {
      // three drifting coral/ember blobs + 4 bezier light ribbons on a small canvas, blurred once
      hz.setTransform(1, 0, 0, 1, 0, 0); hz.globalCompositeOperation = 'source-over'; hz.filter = 'none';
      hz.clearRect(0, 0, 270, 480);
      hz.globalCompositeOperation = 'lighter';
      const blobs = [
        { c: CORAL, a: 0.09, r: 190, x: 135 + 70 * Math.sin(0.13 * t + 0.4) + 30 * Math.sin(0.31 * t + 2.1), y: 300 + 80 * Math.sin(0.11 * t + 1.7) + 30 * Math.sin(0.27 * t) },
        { c: '#8A3A28', a: 0.09, r: 220, x: 60 + 60 * Math.sin(0.09 * t + 3.1), y: 120 + 70 * Math.sin(0.17 * t + 0.9) },
        { c: '#4A2A22', a: 0.12, r: 240, x: 220 + 50 * Math.sin(0.12 * t + 5.0), y: 420 + 60 * Math.sin(0.15 * t + 2.7) },
      ];
      for (const b of blobs) {
        const g = hz.createRadialGradient(b.x, b.y, 0, b.x, b.y, b.r);
        g.addColorStop(0, withAlpha(b.c, b.a * amount)); g.addColorStop(1, withAlpha(b.c, 0));
        hz.fillStyle = g; hz.fillRect(0, 0, 270, 480);
      }
      // ribbons: fluid light waves
      hz.lineCap = 'round';
      for (let i = 0; i < 4; i++) {
        const ph = i * 1.9, per = [7, 11, 13, 9][i];
        const y0 = 60 + i * 110 + 30 * Math.sin(TAU * t / per + ph);
        hz.beginPath();
        hz.moveTo(-40, y0 + 40 * Math.sin(t * 0.3 + ph));
        hz.bezierCurveTo(70, y0 + 90 * Math.sin(t * 0.21 + ph + 1), 180, y0 - 90 * Math.sin(t * 0.17 + ph + 2), 310, y0 + 30 * Math.sin(t * 0.25 + ph + 3) + (i % 2 ? 60 : -60));
        hz.lineWidth = 26 + 14 * Math.sin(t * 0.2 + ph);
        hz.strokeStyle = withAlpha(i === 1 ? '#8A3A28' : CORAL, (0.05 + 0.02 * Math.sin(t * 0.4 + ph)) * ribbonAlpha * amount);
        hz.stroke();
      }
      ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.filter = 'blur(10px)';
      ctx.drawImage(hazeC, -60, -60, W + 120, H + 120);
      ctx.restore();
    }

    // ---------- beam ----------
    // beam state: apex (ax,ay), axis angle (rad, canvas coords), half-angle (rad), intensity 0..1, length
    function beamState(t) {
      const s = (a, b) => span(t, a, b);
      let st = { ax: -180, ay: -260, ang: d2r(59), half: d2r(0.5), inten: 0, len: 3000 };
      if (t < 1.0) {
        // hairline phase (drawn separately) — the cone is off
        st.inten = 0;
      } else if (t < 3.0) {
        st.ang = d2r(lerp(59, 41, ease.inOutSine(s(1, 3))));
        st.half = d2r(lerp(0.5, 6, ease.outCubic(s(1, 1.6))));
        st.inten = lerp(0, 0.75, ease.outCubic(s(1, 1.6)));
      } else if (t < 4.0) { // shot A: axis along the tilted header (-14deg) through (640,640)
        const P = { x: 640 - 18 * s(3, 4), y: 640 - 18 * s(3, 4) }, a = d2r(-14 + 0.3 * Math.sin(TAU * 0.4 * t));
        st = { ax: P.x - Math.cos(a) * 1400, ay: P.y - Math.sin(a) * 1400, ang: a, half: d2r(3.2), inten: 0.7, len: 3200 };
      } else if (t < 5.0) { // shot B: horizontal band scanning down
        const y = lerp(700, 1250, ease.inOutQuad(s(4, 5)));
        st = { ax: -1400, ay: y, ang: 0, half: d2r(2.2), inten: 0.6, len: 3200 };
      } else if (t < 6.0) { // shot C: raking specular from upper left, following the streak
        const sx = lerp(-200, 1300, ease.inOutCubic(s(5, 6)));
        const a = Math.atan2(900 - (-500), sx - (-700));
        st = { ax: -700, ay: -500, ang: a, half: d2r(4), inten: 0.45, len: 3200 };
      } else if (t < 7.0) { // shot D: thin vertical slit sweeping right -> left
        const x = lerp(1180, -100, ease.inOutQuart(s(6, 7)));
        st = { ax: x, ay: -500, ang: d2r(90), half: d2r(1.4), inten: 0.5, len: 3000 };
      } else if (t < 8.0) { // shot E: soft key light from top-left
        st = { ax: -400, ay: -300, ang: d2r(52), half: d2r(7), inten: 0.35, len: 3200 };
      } else if (t < 8.5) { // shot F: beam across the % macro, rotating 4deg
        st = { ax: -180, ay: -260, ang: d2r(lerp(52, 56, ease.inOutSine(s(8, 8.5)))), half: d2r(5), inten: 0.6, len: 3200 };
      } else if (t < 9.0) { // flare: the beam swings toward the lens
        st = { ax: -180, ay: -260, ang: d2r(56), half: d2r(lerp(5, 14, s(8.5, 9))), inten: lerp(0.6, 0.2, s(8.5, 9)), len: 3200 };
      }
      return st;
    }
    function drawBeam(bs, alphaMul = 1) {
      if (bs.inten <= 0) return;
      bm.setTransform(0.5, 0, 0, 0.5, 0, 0); bm.globalCompositeOperation = 'source-over'; bm.filter = 'none';
      bm.clearRect(0, 0, W, H);
      bm.globalCompositeOperation = 'screen';
      const dir = { x: Math.cos(bs.ang), y: Math.sin(bs.ang) };
      const nrm = { x: -dir.y, y: dir.x };
      const layers = [[1, 0.12], [0.7, 0.16], [0.4, 0.22]];
      for (const [k, a] of layers) {
        const h = Math.tan(bs.half * k);
        const L1 = bs.len;
        const p1 = { x: bs.ax + dir.x * L1 + nrm.x * h * L1, y: bs.ay + dir.y * L1 + nrm.y * h * L1 };
        const p2 = { x: bs.ax + dir.x * L1 - nrm.x * h * L1, y: bs.ay + dir.y * L1 - nrm.y * h * L1 };
        const g = bm.createLinearGradient(bs.ax, bs.ay, bs.ax + dir.x * L1, bs.ay + dir.y * L1);
        g.addColorStop(0, 'rgba(255,241,232,0)');
        g.addColorStop(0.08, `rgba(255,241,232,${a * bs.inten * alphaMul})`);
        g.addColorStop(0.45, `rgba(255,225,210,${a * bs.inten * alphaMul * 0.55})`);
        g.addColorStop(1, 'rgba(253,119,85,0)');
        bm.fillStyle = g;
        bm.beginPath(); bm.moveTo(bs.ax, bs.ay); bm.lineTo(p1.x, p1.y); bm.lineTo(p2.x, p2.y); bm.closePath(); bm.fill();
      }
      ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.filter = 'blur(9px)';
      ctx.drawImage(beamC, 0, 0, W, H); ctx.restore();
    }
    function beamAt(bs, x, y) {
      if (bs.inten <= 0) return 0;
      const dx = x - bs.ax, dy = y - bs.ay;
      const dir = { x: Math.cos(bs.ang), y: Math.sin(bs.ang) };
      const d = dx * dir.x + dy * dir.y; if (d <= 0) return 0;
      const p = Math.abs(-dx * dir.y + dy * dir.x);
      const edge = d * Math.tan(bs.half) + 8;
      const across = 1 - smoothstep(edge * 0.55, edge, p);
      const along = smoothstep(0, 0.08 * bs.len, d) * (1 - smoothstep(0.45 * bs.len, bs.len, d));
      return across * along * bs.inten;
    }
    // hairline for 0..1 s (the ignition)
    function drawHairline(t, idx) {
      const grow = ease.outExpo(span(t, 0, 0.35));
      const len = lerp(240, 640, grow);
      let flick = 1; if (idx === 1) flick = 0.55; if (idx === 3) flick = 0.9; if (idx === 2) flick = 1.0;
      const breathe = 1 + 0.06 * Math.sin(TAU * 1.2 * t);
      const tilt = d2r(lerp(0, 59, ease.inOutCubic(span(t, 0.7, 1.0))));
      const thick = lerp(2, 5, span(t, 0.7, 1.0));
      const alpha = flick * breathe * (1 - span(t, 1.0, 1.3));
      ctx.save(); ctx.translate(CX, CY); ctx.rotate(tilt);
      ctx.globalCompositeOperation = 'lighter';
      // halo
      const g = ctx.createLinearGradient(-len / 2, 0, len / 2, 0);
      g.addColorStop(0, 'rgba(253,119,85,0)'); g.addColorStop(0.15, withAlpha(CORAL, 0.35 * alpha)); g.addColorStop(0.85, withAlpha(CORAL, 0.35 * alpha)); g.addColorStop(1, 'rgba(253,119,85,0)');
      ctx.fillStyle = g; ctx.filter = 'blur(7px)'; ctx.fillRect(-len / 2, -7 - thick, len, 14 + thick * 2); ctx.filter = 'none';
      // core
      const g2 = ctx.createLinearGradient(-len / 2, 0, len / 2, 0);
      g2.addColorStop(0, 'rgba(255,241,232,0)'); g2.addColorStop(0.1, `rgba(255,241,232,${alpha})`); g2.addColorStop(0.9, `rgba(255,241,232,${alpha})`); g2.addColorStop(1, 'rgba(255,241,232,0)');
      ctx.fillStyle = g2; ctx.fillRect(-len / 2, -thick / 2, len, thick);
      ctx.restore();
    }

    // ---------- motes & bokeh ----------
    function drawMotes(t, bs, opts = {}) {
      const { gateByBeam = true, base = 0.0, count = 140, attract = null } = opts;
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < count; i++) {
        const m = motes[i];
        let x = m.x0 + 14 * Math.sin(0.6 * t + m.ph) * m.z, y = ((m.y0 + m.vy * m.z * t) % (H + 40)) - 20;
        if (attract) { // pulled toward a point and absorbed
          const k = attract.k; x = lerp(x, attract.x, k); y = lerp(y, attract.y, k);
        }
        let a = (gateByBeam ? beamAt(bs, x, y) : 0) + base;
        if (a <= 0.01) continue;
        const tw = 0.7 + 0.3 * Math.sin(m.tw * t + m.ph);
        a *= tw * (attract ? (1 - attract.k) : 1);
        const near = m.z < 0.6;
        const r = near ? 10 + (0.6 - m.z) * 30 : m.w * (0.6 + m.z * 0.5);
        const col = m.coral ? CORAL : '#FFE9DE';
        if (near) {
          glow(ctx, x, y, r, col, 0.10 * a);
          ctx.strokeStyle = withAlpha(col, 0.12 * a); ctx.lineWidth = 1.2; ctx.beginPath(); ctx.arc(x, y, r * 0.8, 0, TAU); ctx.stroke();
        } else {
          glow(ctx, x, y, r * 2.2, col, 0.5 * a, 0.0);
          ctx.fillStyle = withAlpha(col, 0.9 * a); ctx.beginPath(); ctx.arc(x, y, r * 0.5, 0, TAU); ctx.fill();
        }
      }
      ctx.restore();
    }
    function drawBokeh(t, n, color, alpha = 0.05, drift = 1) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < n; i++) {
        const b = bokehSeeds[i];
        const x = b.x * W + 40 * Math.sin(b.sp * t + b.ph) * drift, y = b.y * H + 30 * Math.cos(b.sp * 0.8 * t + b.ph) * drift;
        glow(ctx, x, y, b.r, color, alpha, 0.5);
      }
      ctx.restore();
    }

    // ---------- lit fragments ----------
    // Draw `drawFn(fx)` into fxC, then composite: dim blurred context + sharp band-masked region.
    // mask: {x,y,angle,core,feather} band along a line through (x,y) with direction angle; extra: optional extra mask fn(fx)
    function litLayer(drawFn, mask, dof = { blur: 10, dim: 0.14 }, extraMask = null, tint = 1) {
      fx.setTransform(1, 0, 0, 1, 0, 0); fx.globalCompositeOperation = 'source-over'; fx.globalAlpha = 1; fx.filter = 'none';
      fx.clearRect(0, 0, W, H);
      fx.save(); drawFn(fx); fx.restore();
      fx.setTransform(1, 0, 0, 1, 0, 0); fx.filter = 'none'; fx.globalAlpha = 1;
      if (tint < 1) { // warm the whites slightly
        fx.globalCompositeOperation = 'multiply'; fx.fillStyle = `rgba(243,230,222,1)`; fx.fillRect(0, 0, W, H);
        fx.globalCompositeOperation = 'source-over';
      }
      if (extraMask) { fx.globalCompositeOperation = 'destination-in'; extraMask(fx); fx.globalCompositeOperation = 'source-over'; }
      // dim, defocused context
      if (dof && dof.dim > 0) {
        ctx.save(); ctx.globalAlpha = dof.dim; ctx.filter = `blur(${dof.blur}px)`; ctx.drawImage(fxC, 0, 0); ctx.restore();
      }
      // band mask
      if (mask) {
        const dir = { x: Math.cos(mask.angle), y: Math.sin(mask.angle) }, n = { x: -dir.y, y: dir.x };
        const R = mask.core + mask.feather;
        const g = fx.createLinearGradient(mask.x - n.x * R, mask.y - n.y * R, mask.x + n.x * R, mask.y + n.y * R);
        const f = mask.feather / (2 * R);
        g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(f, 'rgba(0,0,0,1)'); g.addColorStop(1 - f, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)');
        fx.globalCompositeOperation = 'destination-in'; fx.fillStyle = g; fx.fillRect(0, 0, W, H);
        fx.globalCompositeOperation = 'source-over';
      }
      ctx.save(); ctx.globalAlpha = mask && mask.alpha != null ? mask.alpha : 1; ctx.drawImage(fxC, 0, 0); ctx.restore();
    }
    // horizontal fade mask helper (alpha 0 at x0 -> 1 at x1)
    const fadeX = (x0, x1) => c => { const g = c.createLinearGradient(x0, 0, x1, 0); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,1)'); c.fillStyle = g; c.fillRect(0, 0, W, H); };
    const fadeY = (y0, y1) => c => { const g = c.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,1)'); c.fillStyle = g; c.fillRect(0, 0, W, H); };

    // 'dark glass' version of a white UI crop: invert + hue-rotate keeps red/green/coral hues while turning the card dark
    function drawGlassAt(c, img, cx, cy, scale, rot, src, lift = 0.07) {
      c.save(); c.translate(cx, cy); c.rotate(rot); c.scale(scale, scale);
      c.filter = 'invert(1) hue-rotate(180deg) saturate(1.15)';
      const w = src ? src[2] : img.width, h = src ? src[3] : img.height;
      if (src) c.drawImage(img, src[0], src[1], src[2], src[3], -w / 2, -h / 2, w, h); else c.drawImage(img, -w / 2, -h / 2);
      c.filter = 'none';
      // lift blacks a little so the card reads as smoked glass, and a hairline edge
      c.globalCompositeOperation = 'source-atop'; c.fillStyle = `rgba(255,236,228,${lift})`; c.fillRect(-w / 2, -h / 2, w, h);
      c.globalCompositeOperation = 'source-over'; c.strokeStyle = 'rgba(255,255,255,0.10)'; c.lineWidth = 1 / scale; c.strokeRect(-w / 2 + 0.5 / scale, -h / 2 + 0.5 / scale, w - 1 / scale, h - 1 / scale);
      c.restore();
    }
    function drawImgAt(c, img, cx, cy, scale, rot, src) {
      c.save(); c.translate(cx, cy); c.rotate(rot); c.scale(scale, scale);
      if (src) c.drawImage(img, src[0], src[1], src[2], src[3], -src[2] / 2, -src[3] / 2, src[2], src[3]);
      else c.drawImage(img, -img.width / 2, -img.height / 2);
      c.restore();
    }

    // ---------- shots ----------
    function shotOpen(t, idx, bs) {
      // 2.4-2.6: the beam grazes the corner of fragment A
      const g = span(t, 2.38, 2.62);
      if (g > 0 && g < 1) {
        const a = Math.sin(g * Math.PI) * 0.7;
        const P = { x: 640, y: 640 }, rot = d2r(-14);
        litLayer(c => drawGlassAt(c, A.kar_detayi_header, P.x, P.y, 1.9, rot, null, 0.12), { x: P.x - 300, y: P.y + 75, angle: rot, core: 30, feather: 110, alpha: a * 0.6 }, { blur: 0, dim: 0 }, null, 1);
      }
    }
    function shotA(t, idx, bs) {
      const u = span(t, 3, 4);
      const drift = 18 * ease.outSine(u);
      const P = { x: 640 - drift, y: 640 - drift }, rot = d2r(-14);
      // whole card (dim, blurred) with the header sharp under the beam
      litLayer(c => {
        // card body below the header, same transform
        drawGlassAt(c, A.kar_detayi_card_b, P.x, P.y + 501, 1.9, rot, null, 0.06);
      }, { x: P.x - 150, y: P.y + 37, angle: rot, core: 110, feather: 150 }, { blur: 10, dim: 0.35 }, fadeY(P.y + 300, P.y - 120), 1);
      // luminance bump on the strike (2 frames)
      if (idx === 90 || idx === 91) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = `rgba(255,241,232,${idx === 90 ? 0.12 : 0.06})`; ctx.fillRect(0, 0, W, H); ctx.restore(); }
      drawBokeh(t, 6, '#FFE9DE', 0.05);
    }
    function shotB(t, idx, bs) {
      const u = span(t, 4, 5);
      const yBand = lerp(700, 1250, ease.inOutQuad(u));
      const P = { x: 300, y: 1001 }, rot = d2r(8);
      litLayer(c => drawGlassAt(c, A.kar_detayi_card_b, P.x, P.y, 1.9, rot, null, 0.06), { x: 540, y: yBand, angle: 0, core: 48, feather: 95 }, { blur: 8, dim: 0.4 }, fadeX(380, 600), 1);
      // faint specular of the band on the card
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const g = ctx.createLinearGradient(0, yBand - 60, 0, yBand + 60); g.addColorStop(0, 'rgba(255,241,232,0)'); g.addColorStop(0.5, 'rgba(255,241,232,0.06)'); g.addColorStop(1, 'rgba(255,241,232,0)');
      ctx.fillStyle = g; ctx.fillRect(380, yBand - 60, 700, 120); ctx.restore();
    }
    function shotC(t, idx, bs) {
      const u = span(t, 5, 6);
      const img = A.pill_big_332_cut; const sc = 1.9; const pw = img.width * sc, ph = img.height * sc;
      const floorY = 820;
      const pillBottom = 800 + 24 * ease.outCubic(u);
      const pillCx = 540, pillCy = pillBottom - ph / 2;
      // the pill itself: only its lower part is lit (fade to black upward)
      litLayer(c => drawImgAt(c, img, pillCx, pillCy, sc, 0), null, { blur: 0, dim: 0 }, fadeY(pillCy + ph * 0.10, pillCy + ph * 0.42), 1);
      // reflection: mirrored, rippled strips, fading downward, lit by a passing specular streak
      const streakX = lerp(-200, 1300, ease.inOutCubic(u));
      fx.setTransform(1, 0, 0, 1, 0, 0); fx.globalCompositeOperation = 'source-over'; fx.globalAlpha = 1; fx.filter = 'none'; fx.clearRect(0, 0, W, H);
      fx.save(); fx.translate(pillCx, floorY + 20 + ph / 2); fx.scale(sc, -sc); fx.drawImage(img, -img.width / 2, -img.height / 2); fx.restore();
      // vertical fade + horizontal streak lighting
      fx.globalCompositeOperation = 'destination-in';
      const gv = fx.createLinearGradient(0, floorY + 20, 0, floorY + 20 + ph + 60); gv.addColorStop(0, 'rgba(0,0,0,0.55)'); gv.addColorStop(0.7, 'rgba(0,0,0,0.12)'); gv.addColorStop(1, 'rgba(0,0,0,0)'); fx.fillStyle = gv; fx.fillRect(0, 0, W, H);
      fx.globalCompositeOperation = 'source-over';
      // draw rippled strips
      ctx.save(); ctx.globalAlpha = 0.85; ctx.filter = 'blur(2.5px)';
      const y0 = floorY + 20, y1 = y0 + ph + 60;
      for (let y = y0; y < y1; y += 3) {
        const off = 6 * Math.sin(y * 0.05 + 4 * t) + 2.5 * Math.sin(y * 0.13 - 3 * t);
        ctx.drawImage(fxC, 0, y, W, 3, off, y, W, 3);
      }
      ctx.restore();
      // specular streak over the floor
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.save(); ctx.translate(streakX, floorY + 90); ctx.scale(1, 0.45);
      const gs = ctx.createRadialGradient(0, 0, 0, 0, 0, 320); gs.addColorStop(0, 'rgba(255,241,232,0.12)'); gs.addColorStop(1, 'rgba(255,241,232,0)');
      ctx.fillStyle = gs; ctx.fillRect(-320, -320, 640, 640); ctx.restore();
      // floor line glint
      const gl = ctx.createLinearGradient(streakX - 200, 0, streakX + 200, 0); gl.addColorStop(0, 'rgba(255,241,232,0)'); gl.addColorStop(0.5, 'rgba(255,241,232,0.35)'); gl.addColorStop(1, 'rgba(255,241,232,0)');
      ctx.fillStyle = gl; ctx.fillRect(streakX - 200, floorY + 8, 400, 2);
      ctx.restore();
      drawBokeh(t, 3, GREEN, 0.05);
      // 3-frame dip to black at the cut (a breath)

    }
    function shotD(t, idx, bs) {
      const u = span(t, 6, 7);
      const img = A.dash_netkar_row; const sc = 2.3;
      const slitX = lerp(1180, -100, ease.inOutQuart(u));
      const left = 140 + 30 * u; const cx = left + img.width * sc / 2, cy = 900;
      litLayer(c => drawGlassAt(c, img, cx, cy, sc, 0, null, 0.14), { x: slitX, y: cy, angle: d2r(90), core: 120, feather: 240 }, { blur: 8, dim: 0.65 }, null, 1);
      drawBokeh(t, 2, '#FFE9DE', 0.05);
    }
    function shotE(t, idx, bs) {
      const u = span(t, 7, 8);
      const fig = A.kar_detayi_figures; // 230x305 : figure column, rows at y 68,111,154,196 (Ürün Maliyeti..Hizmet)
      const rows = [68, 111, 154, 196];
      const sc = 3.4, slatW = 120 * sc, slatH = 44 * sc;
      const xRight = 860, tilt = d2r(-3);
      const stackDrift = -30 * u;
      fx.setTransform(1, 0, 0, 1, 0, 0); fx.globalCompositeOperation = 'source-over'; fx.globalAlpha = 1; fx.filter = 'none'; fx.clearRect(0, 0, W, H);
      // slats rendered "dark glass": invert + hue-rotate turns the white card dark while keeping red figures red
      for (let i = 0; i < 4; i++) {
        const t0 = 7 + 0.25 * i; const k = span(t, t0, t0 + 0.22); if (k <= 0) continue;
        const drop = 90 * (1 - ease.outExpo(k));
        const y = 540 + i * 190 - drop, x = xRight - slatW + stackDrift;
        fx.save(); fx.translate(x + slatW / 2, y + slatH / 2); fx.rotate(tilt);
        fx.filter = 'invert(1) hue-rotate(180deg)';
        fx.globalAlpha = 0.92 * Math.min(1, k * 3);
        fx.drawImage(fig, 110, rows[i] - 22, 120, 44, -slatW / 2, -slatH / 2, slatW, slatH);
        fx.filter = 'none';
        // edge highlight (flashes on landing)
        const flash = 0.35 + 0.65 * (1 - smoothstep(0.85, 1.0, k)) * (k > 0.6 ? 1 : 0);
        fx.globalAlpha = 1;
        fx.strokeStyle = `rgba(255,241,232,${0.25 + 0.5 * flash})`; fx.lineWidth = 1.5;
        fx.beginPath(); fx.moveTo(-slatW / 2, -slatH / 2 + 0.75); fx.lineTo(slatW / 2, -slatH / 2 + 0.75); fx.stroke();
        fx.strokeStyle = 'rgba(255,255,255,0.08)'; fx.strokeRect(-slatW / 2 + 0.5, -slatH / 2 + 0.5, slatW - 1, slatH - 1);
        fx.restore();
      }
      // slats
      ctx.save(); ctx.drawImage(fxC, 0, 0); ctx.restore();
      // reflection of the stack on a glossy plane below the last slat
      const planeY = 540 + 3 * 190 + slatH + 30;
      ctx.save(); ctx.globalAlpha = 0.18; ctx.filter = 'blur(6px)';
      ctx.translate(0, planeY * 2); ctx.scale(1, -1);
      ctx.drawImage(fxC, 0, planeY - 420, W, 420, 0, planeY - 420, W, 420);
      ctx.restore();
      ctx.save(); const gf = ctx.createLinearGradient(0, planeY, 0, planeY + 300); gf.addColorStop(0, 'rgba(11,6,5,0.2)'); gf.addColorStop(1, 'rgba(11,6,5,1)'); ctx.fillStyle = gf; ctx.fillRect(0, planeY, W, 320); ctx.restore();
      // divider draws from centre outward 7.75-8.0 (a sum is coming)
      const dv = ease.outExpo(span(t, 7.75, 8.0));
      if (dv > 0) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = 'rgba(255,241,232,0.45)'; const w = 560 * dv; ctx.fillRect(xRight - slatW / 2 - w / 2 + stackDrift, planeY - 12, w, 1.5); ctx.restore(); }
      drawBokeh(t, 3, CORAL, 0.04);
    }
    function shotF(t, idx, bs) {
      const u = span(t, 8, 8.5);
      const R = 900, cx = 1500 - 20 * u, cy = 1700 - 20 * u;
      litLayer(c => {
        logoMark(c, cx, cy, R, CORAL, PALE, 1);
        // shading: darker away from the light (upper-left is lit)
        const sg = c.createRadialGradient(cx - R * 0.55, cy - R * 0.55, R * 0.2, cx, cy, R * 1.05);
        sg.addColorStop(0, 'rgba(0,0,0,0)'); sg.addColorStop(0.55, 'rgba(20,6,4,0.35)'); sg.addColorStop(1, 'rgba(20,6,4,0.8)');
        c.globalCompositeOperation = 'source-atop'; c.fillStyle = sg; c.beginPath(); c.arc(cx, cy, R, 0, TAU); c.fill(); c.globalCompositeOperation = 'source-over';
      }, { x: 760, y: 1300, angle: bs.ang, core: 240, feather: 420 }, { blur: 12, dim: 0.25 }, null, 1);
      // rim light along the disc edge where the beam hits
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = 'rgba(255,241,232,0.35)'; ctx.lineWidth = 2; ctx.filter = 'blur(2px)';
      ctx.beginPath(); ctx.arc(cx, cy, R + 1, d2r(195), d2r(262)); ctx.stroke(); ctx.restore();
      drawBokeh(t, 4, CORAL, 0.04);
    }
    function drawFlare(t) {
      const u = span(t, 8.5, 9.0);
      const k = ease.inQuad(u);
      const sx = lerp(140, 540, k), sy = lerp(200, 960, k);
      const coreR = lerp(90, 230, k), streakA = lerp(0.25, 0.9, u);
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      // chromatic core: three channel copies offset
      const offs = [[-2, 'rgba(255,60,40,'], [0, 'rgba(120,255,140,'], [2, 'rgba(90,120,255,']];
      for (const [ox, col] of offs) {
        const g = ctx.createRadialGradient(sx + ox, sy, 0, sx + ox, sy, coreR * 3);
        g.addColorStop(0, col + (0.55 + 0.3 * k) + ')'); g.addColorStop(0.25, col + (0.25 * (0.5 + k)) + ')'); g.addColorStop(1, col + '0)');
        ctx.fillStyle = g; ctx.fillRect(sx - coreR * 3, sy - coreR * 3, coreR * 6, coreR * 6);
      }
      // anamorphic streak
      ctx.save(); ctx.translate(sx, sy); ctx.scale(7, 1);
      const gs = ctx.createRadialGradient(0, 0, 0, 0, 0, coreR * 1.6);
      gs.addColorStop(0, `rgba(255,241,232,${0.7 * streakA})`); gs.addColorStop(0.5, `rgba(253,119,85,${0.25 * streakA})`); gs.addColorStop(1, 'rgba(253,119,85,0)');
      ctx.fillStyle = gs; ctx.fillRect(-coreR * 1.6, -coreR * 1.6, coreR * 3.2, coreR * 3.2); ctx.restore();
      // ghosts along the axis toward the frame centre
      for (let i = 1; i <= 3; i++) {
        const gx = lerp(sx, 540, 0.4 * i), gy = lerp(sy, 960, 0.4 * i);
        glow(ctx, gx, gy, 30 + 20 * i, CORAL, 0.10 * u, 0.6);
      }
      ctx.restore();
      // whiteout to 92% by 8.9, hold, then the cut to black at 9.0 handles the snap
      const wo = 0.92 * ease.inQuart(span(t, 8.55, 8.9));
      if (wo > 0) { ctx.save(); ctx.fillStyle = `rgba(255,241,232,${wo})`; ctx.fillRect(0, 0, W, H); ctx.restore(); }
    }

    // ---------- tagline ----------
    function layoutLetters(str, font, letterSpacing) {
      ctx.save(); ctx.font = font; ctx.letterSpacing = '0px';
      const glyphs = Array.from(str);
      const widths = glyphs.map(g => ctx.measureText(g).width);
      const total = widths.reduce((a, b) => a + b, 0) + letterSpacing * (glyphs.length - 1);
      let x = -total / 2; const out = [];
      glyphs.forEach((g, i) => { out.push({ g, x: x + widths[i] / 2, w: widths[i] }); x += widths[i] + letterSpacing; });
      ctx.restore(); return out;
    }
    function drawTagline(t, idx) {
      const TG = tl.tagline;
      const colX = lerp(-260, 1340, ease.inOutCubic(span(t, 9.1, 10.5)));
      const outK = ease.inQuad(span(t, tl.hits.text_out, 13.0));
      const alphaOut = 1 - outK;
      const lines = [];
      if (TG.kicker) lines.push({ s: TG.kicker, font: '500 40px Inter', y: 900, ls: 9, color: 'rgba(255,247,244,0.85)', small: true });
      lines.push({ s: TG.line1, font: '800 138px Montserrat', y: 1035, ls: -1.5, color: TG.accent_line === 1 ? CORAL : WARM });
      lines.push({ s: TG.line2, font: '800 138px Montserrat', y: 1180, ls: -1.5, color: TG.accent_line === 2 ? CORAL : WARM });
      ctx.save(); ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
      for (const ln of lines) {
        const letters = layoutLetters(ln.s, ln.font, ln.ls + (ln.small ? 0 : 3.4 * outK));
        ctx.font = ln.font;
        for (const L2 of letters) {
          const x = CX + L2.x;
          const reveal = smoothstep(x - 60, x + 50, colX);        // 1 once the column has passed this letter
          if (reveal <= 0.001) continue;
          const settle = 8 * (1 - ease.outCubic(clamp((colX - x) / 260, 0, 1)));
          const near = Math.exp(-Math.pow((colX - x) / 120, 2));
          const a = reveal * alphaOut * (0.92 + 0.08 * near) * (1 + 0.02 * Math.sin(TAU * 0.5 * t));
          if (near > 0.02) { ctx.save(); ctx.shadowColor = CORAL; ctx.shadowBlur = 26; ctx.globalAlpha = near * alphaOut * 0.9; ctx.fillStyle = '#FFD9CD'; ctx.fillText(L2.g, x, ln.y + settle); ctx.restore(); }
          ctx.globalAlpha = a; ctx.fillStyle = ln.color; ctx.fillText(L2.g, x, ln.y + settle);
        }
      }
      ctx.restore();
      // coral rule above the block (the brand's headline dash); from text_out it lifts and contracts into the dot the logo grows from
      const ra = smoothstep(10.3, 10.6, t);
      if (ra > 0) {
        const mk = ease.inOutCubic(span(t, tl.hits.text_out, 12.95));
        const ry = lerp(838, 790, mk), rw = lerp(72, 26, mk), rh = lerp(6, 26, mk);
        const pulse = 1 + 1.0 * Math.exp(-Math.pow((t - 12.9) / 0.05, 2));
        ctx.save(); ctx.globalAlpha = ra; ctx.fillStyle = CORAL;
        roundRect(ctx, CX - rw / 2 * pulse, ry - rh / 2 * pulse, rw * pulse, rh * pulse, Math.min(rw, rh) / 2 * pulse); ctx.fill();
        if (mk > 0) { ctx.globalCompositeOperation = 'lighter'; glow(ctx, CX, ry, 60 + 140 * mk, CORAL, 0.28 * mk * pulse, 0); ctx.fillStyle = `rgba(255,241,232,${0.6 * mk})`; ctx.beginPath(); ctx.arc(CX, ry, rh * 0.28 * pulse, 0, TAU); ctx.fill(); }
        ctx.restore();
      }
      // light column
      const ca = (1 - smoothstep(10.3, 10.6, t));
      if (ca > 0 && colX > -300 && colX < 1400) {
        ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.filter = 'blur(30px)';
        const g = ctx.createLinearGradient(colX - 130, 0, colX + 130, 0); g.addColorStop(0, 'rgba(255,241,232,0)'); g.addColorStop(0.5, `rgba(255,241,232,${0.18 * ca})`); g.addColorStop(1, 'rgba(255,241,232,0)');
        ctx.fillStyle = g; ctx.fillRect(colX - 130, 0, 260, H); ctx.restore();
      }
    }

    // ---------- end card ----------
    function drawEndcard(t, idx) {
      const cx = 540, cy = 790, R = 128;
      const u = span(t, 13.0, 13.35);
      const sc = Math.max(0.1, ease.outBack(u));
      // hit flash + breathing glow
      const flash = 0.5 * Math.pow(1 - span(t, 13.0, 13.27), 2);
      const breathe = 0.25 + 0.05 * Math.sin(TAU * 0.6 * (t - 13));
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      glow(ctx, cx, cy, 320, CORAL, (breathe + flash) * 0.9, 0.35);
      // expanding thin ring
      const rk = span(t, 13.0, 13.8);
      if (rk < 1) { ctx.strokeStyle = withAlpha(CORAL, 0.5 * (1 - ease.outQuad(rk))); ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(cx, cy, lerp(R, 720, ease.outExpo(rk)), 0, TAU); ctx.stroke(); }
      ctx.restore();
      // disc
      ctx.save(); ctx.translate(cx, cy); ctx.scale(sc, sc);
      ctx.fillStyle = CORAL; ctx.beginPath(); ctx.arc(0, 0, R, 0, TAU); ctx.fill();
      // subtle top-right specular (studio key light)
      const sg = ctx.createRadialGradient(R * 0.35, -R * 0.45, 0, R * 0.35, -R * 0.45, R * 0.9);
      sg.addColorStop(0, 'rgba(255,255,255,0.14)'); sg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = sg; ctx.beginPath(); ctx.arc(0, 0, R, 0, TAU); ctx.fill();
      // % glyph drawn by light
      ctx.strokeStyle = PALE; ctx.fillStyle = PALE; ctx.lineCap = 'butt'; ctx.lineJoin = 'miter';
      const w = 0.137 * R;
      const r1 = ease.outBack(span(t, 13.15, 13.32)), r2 = ease.outBack(span(t, 13.27, 13.44));
      ctx.lineWidth = w;
      if (r1 > 0) { ctx.beginPath(); ctx.arc(-0.287 * R, -0.287 * R, 0.19 * R * r1, 0, TAU); ctx.stroke(); }
      if (r2 > 0) { ctx.beginPath(); ctx.arc(0.313 * R, 0.313 * R, 0.19 * R * r2, 0, TAU); ctx.stroke(); }
      const sk = ease.outCubic(span(t, 13.2, 13.45));
      if (sk > 0) { ctx.beginPath(); ctx.moveTo(-0.327 * R, 0.358 * R); ctx.lineTo(lerp(-0.327, 0.30, sk) * R, lerp(0.358, -0.27, sk) * R); ctx.stroke(); }
      const ak = ease.outCubic(span(t, 13.45, 13.56));
      if (ak > 0) { const ox = 0.43 * R, oy = -0.40 * R, arm = 0.32 * R * ak; ctx.fillRect(ox - arm, oy, arm, w); ctx.fillRect(ox - w, oy, w, arm); }
      // glint riding the slash tip
      if (sk > 0 && sk < 1) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; glow(ctx, lerp(-0.327, 0.30, sk) * R, lerp(0.358, -0.27, sk) * R, 0.35 * R, '#FFFFFF', 0.6, 0); ctx.restore(); }
      ctx.restore();
      // wordmark, letter by letter
      const wm = 'melontik';
      const font = '800 165px Montserrat';
      const letters = layoutLetters(wm, font, -1.5);
      ctx.save(); ctx.font = font; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
      letters.forEach((L2, i) => {
        const k = ease.outQuint(span(t, 13.32 + i * 0.04, 13.32 + i * 0.04 + 0.34));
        if (k <= 0) return;
        ctx.globalAlpha = k; ctx.fillStyle = WARM; ctx.fillText(L2.g, cx + L2.x, 1068 + 20 * (1 - k));
      });
      ctx.restore();
      // coral hairline + date
      const hk = ease.outExpo(span(t, 13.72, 13.92));
      if (hk > 0) { ctx.save(); ctx.fillStyle = withAlpha(CORAL, 0.9); ctx.fillRect(cx - 80 * hk, 1118, 160 * hk, 2); ctx.restore(); }
      const dk = ease.outCubic(span(t, tl.hits.date_in, tl.hits.date_in + 0.38));
      if (dk > 0) {
        ctx.save(); ctx.font = '500 58px Inter'; ctx.letterSpacing = '9px'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
        // soft clip-wipe left to right
        const tw = measure(ctx, tl.launch_date, '500 58px Inter', 9);
        ctx.beginPath(); ctx.rect(cx - tw / 2 - 20, 1132, (tw + 40) * dk, 90); ctx.clip();
        ctx.globalAlpha = Math.min(1, dk * 1.5); ctx.fillStyle = PALE; ctx.fillText(tl.launch_date, cx + 4, 1192);
        ctx.restore();
        if (tl.caption) { ctx.save(); ctx.globalAlpha = dk * 0.55; ctx.font = '400 30px Inter'; ctx.letterSpacing = '2px'; ctx.textAlign = 'center'; ctx.fillStyle = WARM; ctx.fillText(tl.caption, cx, 1262); ctx.restore(); }
      }
    }

    // ---------- main ----------
    function render(t, idx) {
      const D = tl.duration; t = clamp(t, 0, D);
      ctx.save();
      ctx.setTransform(ctx.getTransform()); // keep any scale set by the host
      ctx.fillStyle = '#0B0605'; ctx.fillRect(0, 0, W, H);
      const bs = beamState(t);
      const cm = camera(t);

      if (t < 9.0) {
        ctx.save(); applyCamera(cm);
        drawBase(t);
        drawHaze(t, t < 3 ? lerp(0.5, 1, span(t, 0, 3)) : 1, t < 3 ? 0.5 : 1);
        if (t < 1.3) drawHairline(t, idx);
        // fragments
        if (t < 3) shotOpen(t, idx, bs);
        else if (t < 4) shotA(t, idx, bs);
        else if (t < 5) shotB(t, idx, bs);
        else if (t < 6) shotC(t, idx, bs);
        else if (t < 7) shotD(t, idx, bs);
        else if (t < 8) shotE(t, idx, bs);
        else if (t < 8.5) shotF(t, idx, bs);
        drawBeam(bs, t >= 8.5 ? 0.6 : 1);
        drawMotes(t, bs, { gateByBeam: true, base: t >= 3 ? 0.03 : 0 });
        if (t >= 8.5) drawFlare(t);
        ctx.restore();
        vignette(ctx, W, H, 0.62, 0.78);
      } else if (t < 13.0) {
        drawBase(t);
        const bk = smoothstep(9.0, 9.1, t);                    // black holds 3 frames after the snap
        drawHaze(t, 0.35 * bk, 0.4);
        drawMotes(t, bs, { gateByBeam: false, base: 0.08 * bk, count: 40 });
        drawTagline(t, idx);
        vignette(ctx, W, H, 0.7, 0.75);
      } else {
        drawBase(t);
        const flashHaze = 1 + 0.6 * Math.pow(1 - span(t, 13.0, 13.4), 2);
        drawHaze(t, 0.5 * flashHaze, 0.6);
        const k = ease.inCubic(span(t, 13.0, 13.6));
        drawMotes(t, bs, { gateByBeam: false, base: 0.08, count: 24, attract: { x: 540, y: 790, k } });
        drawMotes(t, bs, { gateByBeam: false, base: 0.06, count: 10 });
        drawEndcard(t, idx);
        vignette(ctx, W, H, 0.66, 0.78);
      }
      grain(ctx, W, H, idx | 0, 0.05);
      ctx.restore();
      if (window.DEBUG_SAFE) { ctx.save(); ctx.strokeStyle = 'rgba(0,255,255,0.6)'; ctx.setLineDash([12, 12]); ctx.strokeRect(0, SAFE_TOP, W, SAFE_BOTTOM - SAFE_TOP); ctx.restore(); }
    }

    return { render };
  }
  global.Scene = { create };
})(window);
