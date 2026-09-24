#!/usr/bin/env bash
# Encode build/frames + build/audio.wav into the final MP4 and regenerate the contact sheet and poster.
# Used by build.sh; run directly after re-rendering a range of frames (node scripts/render_frames.cjs --start A --end B).
set -euo pipefail
cd "$(dirname "$0")/.."
FFMPEG="${FFMPEG:-$(command -v ffmpeg || echo /usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2)}"
OUT_NAME="${OUT_NAME:-melontik_chrome_teaser_9x16}"
FPS=30
mkdir -p output
"$FFMPEG" -hide_banner -loglevel error -y \
  -framerate $FPS -i build/frames/f_%04d.png \
  -i build/audio.wav \
  -vf "scale=in_range=pc:out_range=tv:out_color_matrix=bt709" \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -profile:v high -level 4.2 \
  -tune film -x264-params aq-mode=3:aq-strength=1.1:deblock=-1,-1 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart \
  "output/${OUT_NAME}.mp4"
"$FFMPEG" -hide_banner -loglevel error -y -i "output/${OUT_NAME}.mp4" \
  -vf "fps=2,scale=270:-1,tile=10x3" -frames:v 1 "output/${OUT_NAME}_contact_sheet.png"
"$FFMPEG" -hide_banner -loglevel error -y -ss 14.5 -i "output/${OUT_NAME}.mp4" -frames:v 1 "output/${OUT_NAME}_poster.png"
"$FFMPEG" -hide_banner -i "output/${OUT_NAME}.mp4" 2>&1 | grep -E "Duration|Stream" || true
ls -la output/
