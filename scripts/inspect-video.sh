#!/bin/bash
# inspect-video.sh - ffprobe + frames, sin inferencia
set -e
VID=${1:-$HOME/yolo-nvidia/carros.mp4}
OUT=${2:-$HOME/yolo-nvidia/outputs/inspect}
mkdir -p "$OUT"
ffprobe -v error -show_format -show_streams -of json "$VID" > "$OUT/ffprobe.json"
ffmpeg -v error -i "$VID" -f null - && echo "integrity OK"
for t in 5 30 55; do
  ffmpeg -y -v error -ss $t -i "$VID" -frames:v 1 -q:v 2 "$OUT/f$(printf %02d $t).jpg"
done
ls -lh "$OUT"
