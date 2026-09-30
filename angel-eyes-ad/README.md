# Angel Eyes — "Kış Modası" 16:9 loop ad

`angel-eyes-kis.mp4` — 1920×1080, 30 fps, 12 s, H.264 MP4, ~13 MB. The last frame matches the first, so it loops without a visible cut.

## Storyboard

| Time | Scene |
|---|---|
| 0.0–5.0 s | Winter dusk street: falling snow, cold city bokeh, cool grade, slow push-in on the eyes, a light glint sweeps across the tortoiseshell frames at ~3.3 s |
| 5.0–6.5 s | Warm light-leak transition from the cold street into a warm interior |
| 6.5–11.0 s | Luxury café: amber bokeh and pendant lamps. Phone screen glow lights the face, a blue reflection sweeps across both lenses (blue-light filter). The **ANGEL EYES** watermark fades in at the bottom right |
| 11.0–12.0 s | Soft "blink" dip, then back to the winter street → loop |

## Video rules checklist

- No other e-commerce platform logos ✔
- No campaign or discount text ✔ (the only text is the Angel Eyes logo)
- Suitable for online sale, no +18 content ✔
- Top-right corner kept clear for the **Sponsorlu** label ✔
- ≤ 100 MB, .MP4, 16:9 ✔

## Re-rendering

```bash
pip install pillow numpy scipy imageio imageio-ffmpeg
python3 render.py                  # 1920x1080 @ 30 fps
python3 render.py --width 3840     # 4K (slower, larger file)
```

Source images are in `assets/`.

## Limitation and live-action prompt

This video is motion graphics built from the one studio portrait. The camera moves, the grade, snow, bokeh, the lens reflection and the logo are animated, but the model does not actually walk, sit down, pick up a phone or blink. For true live-action motion, run the prompt below in an image-to-video model (Veo, Sora, Kling or Runway Gen-4) using `assets/model.jpg` as the reference image. Add the logo afterwards in editing, because AI video models distort logos.

> Cinematic 16:9 fashion commercial, 4K, moody color grade, shallow depth of field. The freckled woman from the reference image, wearing the same clear-lens tortoiseshell aviator glasses, walks elegantly in slow motion down a snow-dusted luxury city street at blue-hour dusk. She wears a camel wool coat and a silk scarf, has tousled dark hair and holds a premium smartphone. Soft snowfall and blurred city lights (bokeh). She turns her head smoothly toward the camera and the frames catch the street glow. Match-cut through a warm light flare: she is now seated in a modern luxury café with warm amber light. She unlocks her phone, the screen lights her face and a subtle blue reflection glows across her lenses. She gives a slow, confident, satisfied blink. Keep the top-right corner clear. No text, no logos, no discounts.
