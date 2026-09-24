#!/usr/bin/env python3
"""
Procedural soundtrack for the Melontik Chrome-extension teaser (15 s, 9:16).
Everything is synthesized with numpy from the shared timeline (src/timeline.json)
so the pulses line up with the picture cuts and the drop lands on the logo hit.

Layers
  1. sub drone        - low, slowly breathing pad (A1/E2), gives the dark bed
  2. pad shimmer      - detuned saw-ish pad, high-passed, slowly opening filter
  3. riser            - filtered noise + rising sine sweep building to the drop
  4. pulses           - short filtered clicks on every picture cut (beat grid)
  5. heartbeat        - soft kick-like thumps on the beat during the fragment block
  6. drop             - sub boom + noise burst + tail at the logo hit
  7. shimmer/ding     - bright bell partials on the logo settle
  8. tail             - reverb-ish tail so the ending does not stop dead
Output: 48 kHz stereo 16-bit WAV, peak-normalized to -1 dBFS.
"""
import argparse, json, math, os, wave, struct
import numpy as np

SR = 48000

def load_timeline(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def t_axis(dur):
    return np.arange(int(dur * SR)) / SR

def env_adsr(n, a, d, s_level, r, sr=SR):
    a_n, d_n, r_n = int(a * sr), int(d * sr), int(r * sr)
    s_n = max(0, n - a_n - d_n - r_n)
    env = np.concatenate([
        np.linspace(0, 1, a_n, endpoint=False),
        np.linspace(1, s_level, d_n, endpoint=False),
        np.full(s_n, s_level),
        np.linspace(s_level, 0, r_n, endpoint=True)])
    return env[:n] if len(env) >= n else np.pad(env, (0, n - len(env)))

def exp_decay(n, tau, sr=SR):
    return np.exp(-np.arange(n) / (tau * sr))

def place(buf, sig, start):
    i = int(start * SR)
    if i >= len(buf): return
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n]

def one_pole_lp(x, cutoff, sr=SR, block=256):
    """one-pole low-pass. cutoff may be a scalar or a per-sample array (applied block-wise)."""
    from scipy.signal import lfilter
    if np.isscalar(cutoff):
        a = math.exp(-2 * math.pi * cutoff / sr)
        return lfilter([1 - a], [1, -a], x)
    y = np.empty_like(x)
    zi = np.zeros(1)
    for i in range(0, len(x), block):
        c = float(np.clip(cutoff[min(i + block // 2, len(x) - 1)], 10, sr / 2 - 1))
        a = math.exp(-2 * math.pi * c / sr)
        y[i:i + block], zi = lfilter([1 - a], [1, -a], x[i:i + block], zi=zi)
    return y

def hp_var(x, cutoff, sr=SR):
    """one-pole high-pass with a scalar or per-sample cutoff"""
    return x - one_pole_lp(x, cutoff, sr)

def biquad_lp(x, cutoff, q=0.707, sr=SR):
    w0 = 2 * math.pi * cutoff / sr
    alpha = math.sin(w0) / (2 * q)
    cosw = math.cos(w0)
    b0 = (1 - cosw) / 2; b1 = 1 - cosw; b2 = (1 - cosw) / 2
    a0 = 1 + alpha; a1 = -2 * cosw; a2 = 1 - alpha
    return _biquad(x, b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0)

def biquad_hp(x, cutoff, q=0.707, sr=SR):
    w0 = 2 * math.pi * cutoff / sr
    alpha = math.sin(w0) / (2 * q)
    cosw = math.cos(w0)
    b0 = (1 + cosw) / 2; b1 = -(1 + cosw); b2 = (1 + cosw) / 2
    a0 = 1 + alpha; a1 = -2 * cosw; a2 = 1 - alpha
    return _biquad(x, b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0)

def biquad_bp(x, center, q=2.0, sr=SR):
    w0 = 2 * math.pi * center / sr
    alpha = math.sin(w0) / (2 * q)
    b0 = alpha; b1 = 0; b2 = -alpha
    a0 = 1 + alpha; a1 = -2 * math.cos(w0); a2 = 1 - alpha
    return _biquad(x, b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0)

def _biquad(x, b0, b1, b2, a1, a2):
    from scipy.signal import lfilter
    return lfilter([b0, b1, b2], [1, a1, a2], x)

def sweep_lp(x, f_start, f_end, curve=2.0):
    """time-varying low-pass: cutoff moves f_start -> f_end along the buffer"""
    n = len(x)
    k = (np.arange(n) / max(1, n - 1)) ** curve
    cutoff = f_start + (f_end - f_start) * k
    return one_pole_lp(x, cutoff)

def reverb(x, decay=1.8, mix=0.35, sr=SR, seed=7):
    """cheap Schroeder-style reverb: 4 parallel feedback combs + 1 allpass per channel (chunk-vectorized)."""
    def comb(sig, delay_ms, fb):
        d = int(delay_ms * sr / 1000)
        n = len(sig)
        out = np.zeros(n + d)
        out[:n] = sig
        for k in range(d, n + d, d):
            hi = min(k + d, n + d)
            out[k:hi] += out[k - d:k - d + (hi - k)] * fb
        return out[:n]
    def allpass(sig, delay_ms, g=0.5):
        d = int(delay_ms * sr / 1000)
        n = len(sig)
        v = np.zeros(n + d)
        v[:n] = sig
        for k in range(d, n + d, d):
            hi = min(k + d, n + d)
            v[k:hi] += v[k - d:k - d + (hi - k)] * g
        out = -g * v[:n]
        out[d:] += v[:n - d]
        return out
    fb = math.exp(-3.0 * 0.03 / decay)
    delays_L = [29.7, 37.1, 41.1, 43.7]
    delays_R = [31.1, 35.7, 42.3, 45.1]
    wet_L = sum(comb(x, d, fb) for d in delays_L) / 4
    wet_R = sum(comb(x, d, fb) for d in delays_R) / 4
    wet_L = allpass(wet_L, 5.0); wet_R = allpass(wet_R, 6.1)
    return x * (1 - mix) + wet_L * mix, x * (1 - mix) + wet_R * mix

def soft_clip(x, drive=1.0):
    return np.tanh(x * drive) / math.tanh(drive)

def build(tl, seed=42):
    dur = tl['duration']
    n = int(dur * SR)
    t = t_axis(dur)
    rng = np.random.default_rng(seed)
    bpm = tl.get('bpm', 120)
    beat = 60.0 / bpm
    H = tl['hits']
    drop_t = H['drop']; mid_t = H.get('mid_hit', 9.0); settle_t = H.get('logo_settle', drop_t + 0.45)
    date_t = H.get('date_in', 13.9); text_t = H.get('text_start', 9.1)
    parts0, parts1 = tl['blocks']['parts']['start'], tl['blocks']['parts']['end']
    cuts = tl.get('cuts', [])
    silences = tl.get('silences', [])

    L = np.zeros(n); R = np.zeros(n)
    def add(sig, start, gL=1.0, gR=1.0):
        place(L, sig * gL, start); place(R, sig * gR, start)

    # --- 0.00 ignition: lamp click + low thump; electrical hum with 8 Hz flutter for 0.4 s
    ln = int(0.4 * SR); tt = np.arange(ln) / SR
    click = biquad_bp(rng.standard_normal(ln), 3200, q=4) * exp_decay(ln, 0.004) * 1.2
    thump = np.sin(2 * np.pi * (48 + 30 * np.exp(-tt / 0.05)) * tt) * exp_decay(ln, 0.12) * 1.0
    hum = (np.sin(2 * np.pi * 110 * tt) + 0.3 * np.sin(2 * np.pi * 220 * tt)) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 8 * tt))) * 0.05
    add(click + thump + hum, 0.0)
    add(click * 0.5, 0.08)                                         # a second, softer click: one of the two survives player start-up
    # room tone / hum, very low, until 9 s
    hum2 = (np.sin(2 * np.pi * 110 * t) + 0.3 * np.sin(2 * np.pi * 220 * t)) * 0.03 * np.clip((mid_t - t) / 0.2, 0, 1) * np.clip(t / 0.4, 0, 1)
    L += hum2; R += hum2

    # --- 1. sub drone: two detuned saws at A1 through a low-pass that opens slowly; ducked on pulses
    def saw(f, ph=0.0):
        return 2 * ((f * t + ph) % 1.0) - 1
    drone = (saw(55.0) + saw(55.3, 0.37)) * 0.5
    cutoff = np.interp(t, [0, 3, 9, drop_t], [180, 260, 600, 700])
    drone = one_pole_lp(drone, cutoff); drone = one_pole_lp(drone, cutoff)
    drone_env = np.clip(t / 1.2, 0, 1) ** 1.2
    drone_env *= np.where(t < mid_t, 1.0, np.where(t < mid_t + 0.15, 0.0, 0.7))        # cut at the 9 s snap, back softer
    drone_env *= np.where(t < drop_t, 1.0, np.exp(-(t - drop_t) / 0.5))
    drone *= drone_env * 0.30
    L += drone; R += drone

    # --- 2. air: pink-ish noise band 6-10 kHz, slow LFO, panned with the beam (L->R over 1-3, wander after)
    air = biquad_bp(rng.standard_normal(n), 7500, q=0.9)
    air *= (0.55 + 0.45 * np.sin(2 * np.pi * 0.2 * t)) * 0.028 * np.clip((t - 0.15) / 0.8, 0, 1) * np.clip((mid_t - t) / 0.1, 0, 1)
    pan = np.clip(np.interp(t, [1.0, 3.0, 5.0, 6.0, 7.0], [0.2, 0.8, 0.5, 0.75, 0.3]), 0, 1)
    L += air * (1 - pan) * 1.4; R += air * pan * 1.4

    # --- 3. pad (9-13): Am add9 in a higher register, low-pass opening; resolves to A major at the drop
    def pad_chord(freqs, start, end, amp, lp0, lp1):
        ln = int((end - start) * SR); tt = np.arange(ln) / SR
        sig = np.zeros(ln)
        for f in freqs:
            for det in (0.997, 1.0, 1.004):
                ph = rng.uniform(0, 1)
                sig += (2 * ((f * det * tt + ph) % 1.0) - 1) * 0.12
        sig = one_pole_lp(sig, np.interp(np.arange(ln), [0, ln], [lp0, lp1]))
        return sig * amp
    pad = pad_chord([220.0, 261.63, 329.63, 493.88], mid_t + 0.1, drop_t, 0.22, 500, 2400)
    ln = len(pad); env = env_adsr(ln, 0.5, 0.5, 0.9, 0.08)
    add(pad * env, mid_t + 0.1, 0.95, 1.05)
    res = pad_chord([220.0, 277.18, 329.63, 440.0], drop_t, dur, 0.28, 900, 2600)
    ln = len(res); env = env_adsr(ln, 0.12, 0.4, 0.75, 1.2)
    add(res * env, drop_t, 1.0, 1.0)

    # --- 4. pulses: soft thud on beats 3-7, 8ths 7-8.9 rising; 16th noise ticks 7-8.9; half-time thuds 9.5/10.5/11.5
    def thud(amp, decay=0.12, f0=60, f1=45):
        ln = int(0.3 * SR); tt = np.arange(ln) / SR
        f = f1 + (f0 - f1) * np.exp(-tt / 0.08)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * exp_decay(ln, decay) * amp
    b = parts0
    while b < 7.0 - 1e-6:
        amp = 0.30 + 0.18 * (b - parts0) / 4.0
        add(thud(amp), b); b += beat
    b = 7.0
    while b < 8.9 - 1e-6:
        amp = 0.42 + 0.14 * (b - 7.0) / 1.9
        add(thud(amp, 0.10), b); b += beat / 2
    b = 7.0
    while b < 8.9 - 1e-6:
        ln = int(0.04 * SR)
        tick = biquad_bp(rng.standard_normal(ln), 8000, q=3) * exp_decay(ln, 0.008) * 0.12
        add(tick, b, 0.6 + 0.4 * ((int(round((b - 7.0) / (beat / 4))) % 2)), 1.0 - 0.4 * ((int(round((b - 7.0) / (beat / 4))) % 2)))
        b += beat / 4
    for b in (9.5, 10.5, 11.5):
        add(thud(0.26, 0.16), b)

    # --- 5. cut transients on every picture cut: 20 ms noise 1.5-4 kHz + 180 Hz thock; pitched glass tinks (A minor pentatonic)
    pent = [880.0, 523.25, 783.99, 659.25, 493.88, 587.33, 880.0, 659.25, 523.25, 1046.5]
    for i, c in enumerate(cuts):
        ln = int(0.25 * SR); tt = np.arange(ln) / SR
        nz = biquad_bp(rng.standard_normal(ln), 2600, q=1.2) * exp_decay(ln, 0.012) * 0.55 * (1 + 2.0 * ((c - 3.0) / 5.9) ** 2)
        thock = np.sin(2 * np.pi * 180 * tt) * exp_decay(ln, 0.03) * 0.35
        f = pent[i % len(pent)]
        tink = (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 2.76 * tt)) * exp_decay(ln, 0.09) * 0.16
        pan = 0.5 + 0.18 * math.sin(i * 1.9)
        add(nz + thock + tink, c, (1 - pan) * 2, pan * 2)
    # glass ticks where the light touches something (graze at 2.4, row crossings in the ledger scan, slit crossings)
    for tk, f, a in [(2.4, 2400, 0.14), (4.7, 1800, 0.08), (4.95, 1800, 0.08), (5.2, 1800, 0.08), (5.45, 1800, 0.08), (5.7, 1800, 0.08), (6.35, 1320, 0.12), (6.7, 1320, 0.12)]:
        ln = int(0.12 * SR); tt = np.arange(ln) / SR
        add(np.sin(2 * np.pi * f * tt) * exp_decay(ln, 0.02) * a, tk)
    # whoosh following the beam sweep 1.2-2.2
    ln = int(1.0 * SR); tt = np.arange(ln) / SR
    wh = one_pole_lp(rng.standard_normal(ln), 300 + 2200 * (tt / 1.0) ** 1.5); wh = biquad_hp(wh, 250)
    wh *= np.sin(np.pi * tt / 1.0) ** 1.5 * 0.10
    pan_w = tt / 1.0
    place(L, wh * (1 - pan_w) * 1.4, 1.2); place(R, wh * pan_w * 1.4, 1.2)

    # --- 6. risers: main riser 3.0 -> 8.92 (saw glide + band-passed noise + accelerating tremolo); second riser 11.0 -> 12.9
    def riser(start, end, amp_noise, amp_tone, f0, f1, trem0, trem1):
        ln = int((end - start) * SR); tt = np.arange(ln) / SR; u = tt / (end - start)
        nz = one_pole_lp(rng.standard_normal(ln), 600 + 7000 * u ** 1.8); nz = hp_var(nz, 250 + 1500 * u ** 2); nz = biquad_lp(nz, 10000)
        f_inst = f0 * (f1 / f0) ** (u ** 1.3)
        tone = 2 * ((np.cumsum(f_inst) / SR) % 1.0) - 1
        tone = one_pole_lp(tone, 400 + 5000 * u ** 2)
        trem_f = trem0 + (trem1 - trem0) * u ** 2
        trem = 0.55 + 0.45 * np.sin(2 * np.pi * np.cumsum(trem_f) / SR)
        env = u ** 1.6
        return (nz * amp_noise + tone * trem * amp_tone) * env
    r1 = riser(parts0, 8.875, 0.30, 0.10, 110, 440, 2, 16)
    # duck the riser 6 dB for 40 ms on every cut so the cut accents stay audible
    for c in cuts:
        i0 = int((c - parts0) * SR); i1 = min(len(r1), i0 + int(0.04 * SR))
        if 0 <= i0 < len(r1): r1[i0:i1] *= 0.5
    add(r1, parts0, 0.95, 1.05)
    r2 = riser(11.0, 12.9, 0.26, 0.09, 110, 330, 3, 18)
    add(r2, 11.0, 1.05, 0.95)
    # accelerating tick rolls (0.25 -> 0.0625 s spacing), humanised by +/-25 ms
    for roll0, roll1, a0 in [(11.0, 12.88, 0.06), (8.5, 8.875, 0.07)]:
        tb = roll0
        while tb < roll1:
            u = (tb - roll0) / (roll1 - roll0)
            ln = int(0.03 * SR)
            tick = biquad_bp(rng.standard_normal(ln), 6000 + 3000 * u, q=4) * exp_decay(ln, 0.006) * (a0 + 0.06 * u ** 2)
            jitter = rng.uniform(-0.025, 0.025) * (1 - u)
            add(tick, tb + jitter, 0.5 + 0.4 * math.sin(tb * 7), 0.5 - 0.4 * math.sin(tb * 7))
            tb += max(0.0625, 0.25 * (1 - u) ** 1.5)
    # reverse-cymbal swell into the 9.0 snap (8.5-8.92) and into the drop (12.5-12.9)
    for s0, s1, a in [(8.5, 8.875, 0.22), (12.55, 12.9, 0.16)]:
        ln = int((s1 - s0) * SR); tt = np.arange(ln) / SR; u = tt / (s1 - s0)
        cym = biquad_lp(hp_var(rng.standard_normal(ln), 2000 - 1800 * u), 9000) * (u ** 2.5) * a
        add(cym, s0)

    # --- 7. the 9.0 mid-hit (snap to black): kick + low-passed impact + tink; text tone at 9.1
    ln = int(1.2 * SR); tt = np.arange(ln) / SR
    kick = np.sin(2 * np.pi * np.cumsum(46 + 90 * np.exp(-tt / 0.05)) / SR) * exp_decay(ln, 0.22) * 0.65
    kick += np.sin(2 * np.pi * np.cumsum(120 + 260 * np.exp(-tt / 0.04)) / SR) * exp_decay(ln, 0.08) * 0.45  # 200-400 Hz body for phone speakers
    imp = biquad_lp(rng.standard_normal(ln), 5000) * exp_decay(ln, 0.07) * 0.6
    add(kick + imp, mid_t)
    ln = int(0.5 * SR); tt = np.arange(ln) / SR
    tone = (np.sin(2 * np.pi * 220 * tt) + 0.5 * np.sin(2 * np.pi * 330 * tt)) * env_adsr(ln, 0.02, 0.1, 0.6, 0.3) * 0.10
    add(tone, text_t)
    ln = int(0.3 * SR); tt = np.arange(ln) / SR
    add(np.sin(2 * np.pi * 1320 * tt) * exp_decay(ln, 0.05) * 0.08, 10.35)                         # coral rule reveal

    # --- 8. THE DROP at 13.0: sub boom (with a 90-110 Hz body so phone speakers hear it) + click + noise boom + tail
    ln = int(2.4 * SR); tt = np.arange(ln) / SR
    f = 38 + 112 * np.exp(-tt / 0.09)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * (exp_decay(ln, 0.6) * 0.9 + exp_decay(ln, 0.9) * 0.3)
    body = np.sin(2 * np.pi * np.cumsum(95 + 60 * np.exp(-tt / 0.06)) / SR) * exp_decay(ln, 0.25) * 0.45
    clickd = biquad_lp(biquad_hp(rng.standard_normal(int(0.004 * SR)), 2000), 10000) * 0.25
    boom = biquad_lp(rng.standard_normal(ln), 2500) * exp_decay(ln, 0.35) * 0.55
    knock = np.sin(2 * np.pi * np.cumsum(250 + 350 * np.exp(-tt / 0.05)) / SR) * exp_decay(ln, 0.12) * 0.4   # 300-600 Hz knock so the hit reads on phones
    impact = soft_clip((sub + body) * 1.3, 1.6) * 0.95 + boom + knock
    add(impact, drop_t); add(clickd, drop_t)

    # --- 9. logo shimmer (bell partials) at the settle, wordmark shimmer, date tick
    ln = int(2.6 * SR); tt = np.arange(ln) / SR
    bell = np.zeros(ln)
    for f, a, tau in [(880, 0.5, 0.9), (1320, 0.3, 0.7), (1760, 0.22, 0.55), (2637, 0.12, 0.4), (3520, 0.07, 0.3)]:
        bell += a * np.sin(2 * np.pi * f * tt + 0.3) * exp_decay(ln, tau)
    bell *= 0.14 * (1 - np.exp(-tt / 0.004))
    add(bell, settle_t, 0.9, 1.1)
    ln = int(0.7 * SR); tt = np.arange(ln) / SR
    shim = biquad_bp(rng.standard_normal(ln), 4500, q=1.5) * exp_decay(ln, 0.18) * 0.05
    add(shim, H.get('wordmark_in', 13.3))
    ln = int(0.4 * SR); tt = np.arange(ln) / SR
    tinkE6 = np.sin(2 * np.pi * 1318.5 * tt) * exp_decay(ln, 0.12) * 0.09
    add(tinkE6, date_t)

    # --- 10. breaths: hard dips before the hits (8.92-9.0 and 12.9-13.0), sidechain ducking on beats 3-9
    duck = np.ones(n)
    b = parts0
    while b < 9.0:
        i0 = int(b * SR); i1 = min(n, i0 + int(0.18 * SR))
        env = 1 - 0.45 * np.exp(-np.arange(i1 - i0) / (0.06 * SR))
        duck[i0:i1] *= env
        b += beat
    for s0, s1 in silences:
        i0, i1 = int(s0 * SR), int(s1 * SR)
        duck[i0:i1] *= np.linspace(0.6, 0.02, i1 - i0)
    L *= duck; R *= duck

    # --- 11. reverb send on a copy of the mix, master HP, soft clip, normalise, end fade (audio only; picture holds)
    wetL, _ = reverb(L, decay=1.7, mix=1.0)
    _, wetR = reverb(R, decay=1.7, mix=1.0, seed=9)
    L = L + wetL * 0.20; R = R + wetR * 0.20
    gate = np.ones(n)
    for s0, s1 in silences:
        i0, i1 = int(s0 * SR), int(s1 * SR)
        gate[i0:i1] = np.linspace(0.5, 0.0, i1 - i0) ** 4
    L *= gate; R *= gate
    L = biquad_hp(L, 24); R = biquad_hp(R, 24)
    fade_out = np.clip((dur - t) / 0.8, 0, 1) ** 1.3
    fade_in = np.clip(t / 0.005, 0, 1)
    L *= fade_out * fade_in; R *= fade_out * fade_in
    L = soft_clip(L, 1.15); R = soft_clip(R, 1.15)
    from scipy.signal import resample_poly
    tp = max(np.max(np.abs(resample_poly(L, 4, 1))), np.max(np.abs(resample_poly(R, 4, 1))), 1e-9)   # true peak estimate
    gain = 10 ** (-1.0 / 20) / tp
    return L * gain, R * gain

def write_wav(path, L, R):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    data = np.empty(len(L) * 2, dtype=np.int16)
    data[0::2] = np.clip(L * 32767, -32768, 32767).astype(np.int16)
    data[1::2] = np.clip(R * 32767, -32768, 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--timeline', default=os.path.join(os.path.dirname(__file__), '..', 'src', 'timeline.json'))
    ap.add_argument('--out', default=os.path.join(os.path.dirname(__file__), '..', 'build', 'audio.wav'))
    a = ap.parse_args()
    tl = load_timeline(a.timeline)
    L, R = build(tl)
    write_wav(a.out, L, R)
    print(f'wrote {a.out}: {len(L)/SR:.2f}s, peak {20*math.log10(max(np.max(np.abs(L)),np.max(np.abs(R)))):.1f} dBFS')
