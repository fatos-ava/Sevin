"""Angel Eyes — 16:9 seamless loop ad ("Kış Modası").

Builds a cinematic motion-graphics loop from the model portrait and logo:
  0.0–5.0s   cold winter dusk: snow, city bokeh, slow push, glint on the frames
  5.0–6.5s   warm light-leak transition into a luxury cafe
  6.5–11.0s  cafe: phone glow, blue-light reflection on the lenses, logo watermark
  11.0–12.0s soft "blink" dip and crossfade back to the first frame (seamless loop)

Platform rules respected: no discount/campaign text, no other platform logos,
top-right corner kept free for the "Sponsorlu" label, 16:9, MP4, < 100 MB.

Usage: python3 render.py [--fps 30] [--width 1920] [--out angel-eyes-kis.mp4]
"""
import argparse
import os

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
DURATION = 12.0
rng = np.random.default_rng(7)


# ---------------------------------------------------------------- helpers
def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    return smooth((t - a) / (b - a))


def blur(img, sigma):
    return ndimage.gaussian_filter(img, sigma=(sigma, sigma, 0) if img.ndim == 3 else sigma)


def screen(base, light):
    return 1 - (1 - base) * (1 - np.clip(light, 0, 1))


# ---------------------------------------------------------------- subject
def load_subject(scale):
    im = Image.open(os.path.join(HERE, "assets/model.jpg")).convert("RGB")
    im = im.crop((0, 50, 621, 881))  # drop the white padding
    a = np.asarray(im).astype(np.float32) / 255

    # Key out the neutral grey studio backdrop, keeping only the region connected to the border.
    mx, mn = a.max(2), a.min(2)
    sat = mx - mn
    lum = a.mean(2)
    cand = (sat < 0.07) & (lum > 0.38) & (lum < 0.72)
    lab, _ = ndimage.label(cand)
    border = set(np.unique(np.concatenate([lab[0], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    bg = ndimage.binary_opening(bg, iterations=2)
    bg = ndimage.binary_dilation(bg, iterations=2)  # choke the matte past the grey fringe
    alpha = 1 - ndimage.gaussian_filter(bg.astype(np.float32), 1.2)
    alpha = np.clip((alpha - 0.3) / 0.6, 0, 1)
    # the sweater runs off the bottom edge: keep it solid there
    alpha[-40:] = np.maximum(alpha[-40:], (lum[-40:] < 0.3).astype(np.float32))

    # decontaminate grey spill on hair edges
    edge = ndimage.gaussian_filter(1 - alpha, 3)[..., None]
    spill = np.clip(edge * 1.6, 0, 0.85)
    a = a * (1 - spill) + (a * 0.35) * spill

    h, w = a.shape[:2]
    size = (int(w * scale), int(h * scale))
    rgb = Image.fromarray((a * 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
    al = Image.fromarray((alpha * 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    rgb = np.asarray(rgb).astype(np.float32) / 255
    al = np.asarray(al).astype(np.float32)[..., None] / 255

    # lens ellipses in source coords (after crop): (cx, cy, rx, ry)
    lenses = [(330, 325, 63, 63), (492, 305, 38, 55)]
    yy, xx = np.mgrid[0:size[1], 0:size[0]].astype(np.float32)
    lens = np.zeros(size[::-1], np.float32)
    for cx, cy, rx, ry in lenses:
        d = ((xx - cx * scale) / (rx * scale)) ** 2 + ((yy - cy * scale) / (ry * scale)) ** 2
        lens = np.maximum(lens, np.clip((1 - d) / 0.18, 0, 1))
    lens = ndimage.gaussian_filter(lens, 2)
    eyes = (np.mean([l[0] for l in lenses]) * scale, np.mean([l[1] for l in lenses]) * scale)
    return rgb, al, lens[..., None], eyes


def grade_cold(rgb):
    lum = rgb.mean(2, keepdims=True)
    g = rgb * 0.7 + lum * 0.3                       # desaturate
    g = g * np.array([0.86, 0.95, 1.08]) + np.array([0.0, 0.01, 0.035])
    return np.clip(g * 0.92, 0, 1)


def grade_warm(rgb):
    g = rgb * np.array([1.08, 0.99, 0.84]) + np.array([0.025, 0.012, 0.0])
    return np.clip(g ** 0.95, 0, 1)


# ---------------------------------------------------------------- backgrounds
def bokeh_layer(W, H, n, palette, rmin, rmax, soft, region=None):
    layer = np.zeros((H, W, 3), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    for _ in range(n):
        x = rng.uniform(0, W)
        y = rng.uniform(*(region or (0, H)))
        r = rng.uniform(rmin, rmax)
        c = np.array(palette[rng.integers(len(palette))]) * rng.uniform(0.35, 1.0)
        x0, x1 = int(max(0, x - r - 4)), int(min(W, x + r + 4))
        y0, y1 = int(max(0, y - r - 4)), int(min(H, y + r + 4))
        if x0 >= x1 or y0 >= y1:
            continue
        d = np.hypot(xx[y0:y1, x0:x1] - x, yy[y0:y1, x0:x1] - y)
        disc = np.clip((r - d) / soft, 0, 1)
        rim = np.exp(-((d - r * 0.92) / (r * 0.08)) ** 2) * 0.35   # lens-like bright rim
        layer[y0:y1, x0:x1] += (disc * 0.55 + rim * disc)[..., None] * c
    return layer


def winter_bg(W, H):
    y = np.linspace(0, 1, H)[:, None, None]
    top = np.array([0.035, 0.05, 0.09])
    mid = np.array([0.10, 0.14, 0.22])
    snow = np.array([0.30, 0.34, 0.40])
    g = np.where(y < 0.62, top + (mid - top) * (y / 0.62), mid + (snow - mid) * np.clip((y - 0.62) / 0.38, 0, 1) ** 1.3)
    g = np.broadcast_to(g, (H, W, 3)).copy()
    # distant facades: soft darker verticals
    for _ in range(14):
        x = rng.uniform(0, W); w = rng.uniform(60, 220)
        g[: int(H * 0.66), int(x):int(x + w)] *= rng.uniform(0.7, 0.9)
    g = blur(g, 18)
    cool = [(0.75, 0.85, 1.0), (0.9, 0.95, 1.0), (0.55, 0.7, 1.0)]
    warm = [(1.0, 0.72, 0.38), (1.0, 0.82, 0.55)]
    far = bokeh_layer(W, H, 90, cool + warm, 6, 22, 3, (0.05 * H, 0.7 * H))
    near = bokeh_layer(W, H, 11, cool + warm, 40, 90, 8, (0.0, 0.8 * H))
    return g, blur(far, 1.5) * 0.7, blur(near, 4) * 0.45


def cafe_bg(W, H):
    y = np.linspace(0, 1, H)[:, None, None]
    top = np.array([0.10, 0.055, 0.03])
    bot = np.array([0.22, 0.13, 0.07])
    g = np.broadcast_to(top + (bot - top) * y, (H, W, 3)).copy()
    # warm window panes / shelves
    for _ in range(10):
        x = rng.uniform(0, W); w = rng.uniform(80, 260); yy0 = rng.uniform(0.1, 0.6) * H
        g[int(yy0):int(yy0 + rng.uniform(80, 260)), int(x):int(x + w)] += np.array([0.08, 0.045, 0.02])
    g = blur(g, 22)
    warm = [(1.0, 0.68, 0.32), (1.0, 0.8, 0.5), (1.0, 0.56, 0.25), (0.95, 0.9, 0.8)]
    far = bokeh_layer(W, H, 75, warm, 8, 26, 3, (0.0, 0.75 * H)) * 0.7
    near = bokeh_layer(W, H, 9, warm, 50, 110, 10, (0.0, 0.7 * H)) * 0.45
    # pendant lamps
    lamps = np.zeros((H, W, 3), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    for lx in (0.62, 0.8, 0.95):
        lamps += np.exp(-(((xx - lx * W) / 70) ** 2 + ((yy - 0.16 * H) / 55) ** 2))[..., None] * np.array([1.0, 0.72, 0.4])
    return g + lamps * 0.5, blur(far, 1.5), blur(near, 3)


# ---------------------------------------------------------------- render
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--out", default=os.path.join(HERE, "angel-eyes-kis.mp4"))
    args = ap.parse_args()

    OW, OH = args.width, args.width * 9 // 16
    k = OW / 1920
    CW, CH = int(OW * 1.12), int(OH * 1.12)           # working canvas (room for camera moves)

    subj, alpha, lens, eyes = load_subject(1.58 * k)
    subj_cold, subj_warm = grade_cold(subj), grade_warm(subj)
    sh, sw = subj.shape[:2]
    sx, sy = int(CW * 0.17), int(14 * k)             # subject placement; sweater runs off the bottom
    ex, ey = sx + eyes[0], sy + eyes[1]

    wg, wfar, wnear = winter_bg(CW, CH)
    cg, cfar, cnear = cafe_bg(CW, CH)

    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
    vign = np.clip(1 - 0.55 * (((xx / CW - 0.45) / 0.75) ** 2 + ((yy / CH - 0.5) / 0.8) ** 2), 0.25, 1)[..., None]
    # phone glow comes from below, in front of her chin
    glow = np.exp(-(((xx - (sx + 0.62 * sw)) / (420 * k)) ** 2 + ((yy - (CH + 60 * k)) / (520 * k)) ** 2))[..., None]
    phone_col = np.array([0.55, 0.75, 1.0])

    # snow: integer loops per cycle -> identical positions at t=0 and t=12 (seamless)
    snow = []
    for layer, (n, rad, cyc, op) in enumerate([(260, 1.6, 1, 0.55), (120, 3.2, 2, 0.75), (28, 7.5, 3, 0.6)]):
        snow.append(dict(x=rng.uniform(0, CW, n), y=rng.uniform(0, CH, n), cyc=cyc,
                         amp=rng.uniform(10, 40, n) * k, ph=rng.uniform(0, 2 * np.pi, n),
                         r=rad * k * rng.uniform(0.7, 1.3, n), op=op))

    # logo -> white watermark
    logo = Image.open(os.path.join(HERE, "assets/logo.jpg")).convert("L")
    la = 1 - np.asarray(logo).astype(np.float32) / 255
    rows, cols = np.where(la > 0.2)
    logo = Image.fromarray((la[rows.min() - 4:rows.max() + 5, cols.min() - 4:cols.max() + 5] * 255).astype(np.uint8))
    lw = int(230 * k)
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    logo_a = np.asarray(logo).astype(np.float32)[..., None] / 255
    lx0, ly0 = OW - lw - int(64 * k), OH - logo_a.shape[0] - int(56 * k)

    n_frames = int(DURATION * args.fps)
    writer = imageio_ffmpeg.write_frames(
        args.out, (OW, OH), fps=args.fps, codec="libx264", quality=None,
        output_params=["-crf", "21", "-preset", "slow", "-movflags", "+faststart",
                       "-tune", "film"],
        macro_block_size=2)
    writer.send(None)

    for f in range(n_frames):
        t = f / args.fps
        ph = 2 * np.pi * t / DURATION
        cold = 1 - ramp(t, 5.0, 6.5) + ramp(t, 11.0, 12.0)
        cold = min(cold, 1.0)

        # --- background with parallax (periodic -> loops)
        def shift(img, dx, dy):
            return np.roll(np.roll(img, int(dx), 1), int(dy), 0)
        wpar = 60 * k * np.sin(ph)
        winter = wg + shift(wfar, wpar * 0.5, 0) * (0.85 + 0.15 * np.sin(ph * 3)) + shift(wnear, wpar * 1.4, 0)
        cafe = cg + shift(cfar, -wpar * 0.4, 0) * (0.85 + 0.15 * np.sin(ph * 2 + 1)) + shift(cnear, -wpar, 0)
        bg = winter * cold + cafe * (1 - cold)

        # --- subject, walking bob during winter
        bob = int(6 * k * np.sin(ph * 8) * cold)
        s = subj_cold * cold + subj_warm * (1 - cold)
        frame = bg.copy()
        y0 = sy + bob
        region = frame[y0:y0 + sh, sx:sx + sw]
        hh = region.shape[0]
        a = alpha[:hh]
        sub = s[:hh].copy()

        # cold rim light from the street lamps (winter)
        sub = screen(sub, (np.array([0.35, 0.45, 0.6]) * 0.12 * cold) * a)

        # phone glow on the face + blue-light reflection on the lenses (cafe)
        phone = ramp(t, 6.9, 7.6) * (1 - ramp(t, 10.9, 11.6))
        flick = 1 + 0.04 * np.sin(t * 23) * phone
        sub = screen(sub, glow[y0:y0 + hh, sx:sx + sw] * phone_col * 0.33 * phone * flick)
        sweep = np.clip(1 - np.abs((np.arange(sw)[None, :] / sw) - (0.25 + 0.55 * ramp(t, 7.2, 9.6))) / 0.12, 0, 1)
        refl = lens[:hh] * (0.55 + 0.45 * sweep[..., None]) * phone * flick
        sub = screen(sub, refl * np.array([0.25, 0.55, 1.0]) * 0.62)
        # ambient glint on the frames while walking
        glint = np.exp(-((t - 3.3) / 0.45) ** 2) * cold
        g_sweep = np.clip(1 - np.abs((np.arange(sw)[None, :] / sw) - (0.2 + 0.6 * ramp(t, 2.6, 4.0))) / 0.06, 0, 1)
        sub = screen(sub, lens[:hh] * g_sweep[..., None] * glint * 0.45 * np.array([0.85, 0.92, 1.0]))

        region[:] = sub * a + region * (1 - a)

        # --- snow over everything (winter only)
        if cold > 0.01:
            snowl = np.zeros((CH, CW), np.float32)
            for L in snow:
                py = (L["y"] + L["cyc"] * CH * t / DURATION) % CH
                px = (L["x"] + L["amp"] * np.sin(ph * L["cyc"] + L["ph"])) % CW
                for x, y, r in zip(px, py, L["r"]):
                    ri = int(r * 2.5) + 1
                    xa, xb, ya, yb = int(x) - ri, int(x) + ri + 1, int(y) - ri, int(y) + ri + 1
                    if xa < 0 or ya < 0 or xb > CW or yb > CH:
                        continue
                    gy, gx = np.mgrid[ya:yb, xa:xb]
                    snowl[ya:yb, xa:xb] += np.exp(-((gx - x) ** 2 + (gy - y) ** 2) / (r * r)) * L["op"]
            frame = screen(frame, snowl[..., None] * np.array([0.9, 0.95, 1.0]) * cold)

        # --- warm light-leak transition + blink dip
        leak = np.exp(-((t - 5.75) / 0.55) ** 2) + np.exp(-((t - 11.5) / 0.35) ** 2) * 0.5
        lx = CW * (-0.2 + 1.4 * ramp(t, 5.0, 6.5))
        leak_img = np.exp(-(((xx - lx) / (500 * k)) ** 2))[..., None] * np.array([1.0, 0.62, 0.3])
        frame = screen(frame, leak_img * leak * 0.75)
        frame = frame * vign
        blink = 1 - 0.35 * np.exp(-((t - 11.45) / 0.18) ** 2)
        frame *= blink

        # --- camera: slow periodic push-in toward the eyes
        z = 1.0 + 0.055 * (0.5 - 0.5 * np.cos(ph))
        vw, vh = CW / 1.12 / z, CH / 1.12 / z
        cx = CW / 2 + (ex - CW / 2) * 0.35 * (z - 1) / 0.055 + 30 * k * np.sin(ph)
        cy = CH / 2 + (ey - CH / 2) * 0.30 * (z - 1) / 0.055
        box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
        img = Image.fromarray((np.clip(frame, 0, 1) * 255).astype(np.uint8))
        out = np.asarray(img.resize((OW, OH), Image.BICUBIC, box=box)).astype(np.float32) / 255

        # --- logo watermark: cafe only, with the blue reflection
        lo = ramp(t, 7.4, 8.4) * (1 - ramp(t, 10.6, 11.2)) * 0.82
        if lo > 0:
            reg = out[ly0:ly0 + logo_a.shape[0], lx0:lx0 + lw]
            reg[:] = reg * (1 - logo_a * lo) + np.array([0.97, 0.95, 0.92]) * logo_a * lo

        # --- film grain
        out = out + rng.normal(0, 0.012, (OH, OW, 1)).astype(np.float32)
        writer.send((np.clip(out, 0, 1) * 255).astype(np.uint8))
        if f % 30 == 0:
            print(f"frame {f}/{n_frames}", flush=True)

    writer.close()
    print("wrote", args.out, os.path.getsize(args.out) // 1024, "KB")


if __name__ == "__main__":
    main()
