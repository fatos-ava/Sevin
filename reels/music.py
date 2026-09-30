"""Melontik × e-adam Reels için özgün (telifsiz) arka plan müziği.

Tamamen bu scriptte sentezlenir; hiçbir örnek/kayıt kullanılmaz.
100 BPM, La minör — Am9 · Fmaj7 · C · G · Am9, 12 saniye.
Vuruşlar animasyondaki geçişlere denk gelecek şekilde yerleştirildi.

Kullanım: python3 reels/music.py  ->  reels/assets/music.wav
Gerekenler: numpy, scipy
"""
import os
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
DUR = 12.0
BPM = 100
BEAT = 60 / BPM            # 0.6 sn
BAR = BEAT * 4             # 2.4 sn
N = int(SR * DUR)
rng = np.random.default_rng(3)


def hz(note):
    """'A3' gibi nota adını frekansa çevirir."""
    names = {'C': -9, 'C#': -8, 'D': -7, 'D#': -6, 'E': -5, 'F': -4, 'F#': -3,
             'G': -2, 'G#': -1, 'A': 0, 'A#': 1, 'B': 2}
    n, o = note[:-1], int(note[-1])
    return 440 * 2 ** ((names[n] + (o - 4) * 12) / 12)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)


def env(n, a, r, sustain=True):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4))
    if sustain:
        rel = np.clip((n / SR - t) / r, 0, 1)
        return e * rel
    return e * np.exp(-t / r)


def add(buf, sig, start):
    i = int(start * SR)
    j = min(len(buf), i + len(sig))
    if i < j:
        buf[i:j] += sig[:j - i]


# ---------- harmony ----------
CHORDS = [  # (start, length, notes)
    (0 * BAR, BAR, ['A2', 'E3', 'G3', 'B3', 'C4']),        # Am9
    (1 * BAR, BAR, ['F2', 'C3', 'E3', 'A3', 'C4']),        # Fmaj7
    (2 * BAR, BAR, ['C3', 'G3', 'C4', 'E4']),              # C
    (3 * BAR, BAR, ['G2', 'D3', 'G3', 'B3', 'D4']),        # G
    (4 * BAR, BAR, ['A2', 'E3', 'G3', 'B3', 'C4']),        # Am9
]

L = np.zeros(N)
R = np.zeros(N)


def stereo(sig, start, pan=0.0, gain=1.0):
    add(L, sig * gain * np.sqrt(0.5 * (1 - pan)), start)
    add(R, sig * gain * np.sqrt(0.5 * (1 + pan)), start)


# ---------- warm pad (detuned saws, low-passed) ----------
def saw(f, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((f * t + phase) % 1) - 1


for start, length, notes in CHORDS:
    n = int((length + 0.6) * SR)
    for note in notes:
        f = hz(note)
        for det, pan in ((-0.12, -0.6), (0.12, 0.6)):
            s = saw(f * 2 ** (det / 12), n, rng.random())
            s = lp(s, 1400 if start > 0 else 900) * env(n, 0.5, 0.7)
            stereo(s, start, pan, 0.045)

# intro swell on pad
t = np.arange(N) / SR
swell = np.clip(t / 1.6, 0, 1) ** 1.5
L *= swell
R *= swell

# ---------- sub bass (from 2.4 s) ----------
for start, length, notes in CHORDS[1:]:
    for k in range(4):
        n = int(BEAT * SR * 0.95)
        f = hz(notes[0]) / 2
        tt = np.arange(n) / SR
        s = np.sin(2 * np.pi * f * tt) * env(n, 0.01, 0.12)
        stereo(s, start + k * BEAT, 0, 0.22)

# ---------- soft pluck arpeggio (8ths, from 2.4 s) ----------
def pluck(f, n):
    tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt / 0.08)
    return s * env(n, 0.004, 0.28, sustain=False)


for bi, (start, length, notes) in enumerate(CHORDS[1:]):
    seq = [notes[i % len(notes)] for i in (1, 2, 3, 4, 2, 3, 4, 3)]
    for k, note in enumerate(seq):
        f = hz(note) * 2
        stereo(pluck(f, int(0.6 * SR)), start + k * BEAT / 2, 0.35 if k % 2 else -0.35, 0.05)

# ---------- drums: soft kick + closed hat + clap, from 2.4 s ----------
def kick():
    n = int(0.35 * SR)
    tt = np.arange(n) / SR
    f = 45 + 90 * np.exp(-tt / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.12)


def hat():
    n = int(0.08 * SR)
    return hp(rng.standard_normal(n), 8000) * env(n, 0.001, 0.025, sustain=False)


def clap():
    n = int(0.25 * SR)
    s = hp(lp(rng.standard_normal(n), 3500), 900)
    return s * env(n, 0.002, 0.07, sustain=False)


for b in range(4, 20):             # beats 4..19  (2.4 s .. 11.4 s)
    s = b * BEAT
    stereo(kick(), s, 0, 0.35)
    stereo(hat(), s + BEAT / 2, 0.25, 0.05)
    if b % 2 == 1:
        stereo(clap(), s, -0.1, 0.07)

# ---------- accents synced to the animation ----------
def bell(f, n, decay=1.2):
    tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt / 0.25)
         + 0.2 * np.sin(2 * np.pi * f * 5.4 * tt) * np.exp(-tt / 0.1))
    return s * env(n, 0.003, decay, sustain=False)


def whoosh(length, up=True):
    n = int(length * SR)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    steps = 40
    for i in range(steps):          # sweeping band via stacked low-passes
        a, b = i * n // steps, (i + 1) * n // steps
        k = i / steps if up else 1 - i / steps
        out[a:b] = lp(noise, 300 + 5000 * k ** 2)[a:b]
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return out * e


stereo(whoosh(0.9), -0.3 + 0.3, 0, 0.05)           # intro breath (0 - 0.9)
stereo(bell(hz('E5'), int(2 * SR)), 0.6, -0.3, 0.09)  # melontik card
stereo(bell(hz('B5'), int(1.2 * SR), 0.5), 1.45, 0, 0.05)  # ×
stereo(bell(hz('A5'), int(2 * SR)), 1.9, 0.3, 0.09)   # e-adam card
stereo(whoosh(1.0), 2.9, 0, 0.06)                    # lockup settles
for tm, note in ((4.0, 'C5'), (4.5, 'E5'), (4.9, 'G5')):   # headline lines
    stereo(bell(hz(note), int(1.5 * SR), 0.7), tm, 0, 0.05)
stereo(bell(hz('A4'), int(3 * SR), 2.0), 5.6, 0, 0.08)     # accent line
stereo(kick(), 5.6, 0, 0.25)

# ---------- reverb (synthetic IR) ----------
ir_n = int(2.2 * SR)
tt = np.arange(ir_n) / SR
irL = rng.standard_normal(ir_n) * np.exp(-tt / 0.55)
irR = rng.standard_normal(ir_n) * np.exp(-tt / 0.55)
irL, irR = lp(irL, 5000), lp(irR, 5000)
wetL = fftconvolve(L, irL)[:N] * 0.018
wetR = fftconvolve(R, irR)[:N] * 0.018
L, R = L + wetL, R + wetR

# ---------- master: outro fade, soft clip, normalize ----------
fade = np.clip((DUR - t) / 0.9, 0, 1) ** 2
fade_in = np.clip(t / 0.05, 0, 1)
mix = np.stack([L, R], axis=1) * (fade * fade_in)[:, None]
mix = hp(mix.T, 30).T
mix = np.tanh(mix * 1.2)
mix *= 0.89 / np.max(np.abs(mix))           # ~ -1 dBFS peak

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'music.wav')
wavfile.write(out, SR, (mix * 32767).astype(np.int16))
print(out)
