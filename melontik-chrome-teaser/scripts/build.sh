#!/usr/bin/env bash
# Full build: soundtrack -> frames -> MP4 (+ preview sheet & poster).
# Requirements: node (with playwright module), python3 (+numpy), ffmpeg (FFMPEG env var or on PATH).
set -euo pipefail
cd "$(dirname "$0")/.."
FFMPEG="${FFMPEG:-$(command -v ffmpeg || echo /usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2)}"
OUT_NAME="${OUT_NAME:-melontik_chrome_teaser_9x16}"
FPS=30
mkdir -p build output

echo "== 1/4 soundtrack"
python3 scripts/make_audio.py --out build/audio.wav

echo "== 2/4 frames"
rm -rf build/frames && mkdir -p build/frames
node scripts/render_frames.cjs --out build/frames --fps $FPS --workers "${WORKERS:-2}"

echo "== 3/4 encode + 4/4 preview sheet & poster"
bash scripts/encode.sh
