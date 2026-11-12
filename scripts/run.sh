#!/bin/bash
# run.sh --input --config --output : DS (nvinfer) -> tracks.jsonl -> mvp.py
set -e
exec 9>/tmp/smart_radar_run.lock
flock -n 9 || { echo "run.sh ya en marcha, salgo"; exit 1; }
IN=/home/marti/yolo-nvidia/carros.mp4
CFG=/home/marti/yolo-nvidia/configs/default.yaml
OUT=/home/marti/yolo-nvidia/outputs
while [ $# -gt 0 ]; do case $1 in
  --input) IN=$2; shift 2;; --config) CFG=$2; shift 2;; --output) OUT=$2; shift 2;;
  *) shift;; esac; done
mkdir -p "$OUT"
export PATH="$HOME/.local/bin:$PATH"
export TRACKS_JSONL="$OUT/tracks.jsonl"
: > "$TRACKS_JSONL"
YML=/home/marti/yolo-nvidia/thirdparty/deepstream_tao_apps/configs/app/lpr_app_yolo.yml
docker run --rm --gpus all \
  -v /home/marti/yolo-nvidia/thirdparty/deepstream_tao_apps:/workspace \
  -v /home/marti/yolo-nvidia:/work \
  -e TRACKS_JSONL=/work/outputs/tracks.jsonl \
  -w /workspace/apps/tao_others/deepstream_lpr_app \
  ghcr.io/nvidia/deepstream:9.2-triton-multiarch ./deepstream-lpr-app /workspace/configs/app/lpr_app_yolo.yml
sudo chown -R "$(id -u):$(id -g)" "$OUT" 2>/dev/null || true
uv run --project /home/marti/yolo-nvidia python /home/marti/yolo-nvidia/src/mvp.py \
  "$OUT/tracks.jsonl" "$CFG" "$OUT" "$OUT/lpr_annotated.mp4"
uv run --project /home/marti/yolo-nvidia python /home/marti/yolo-nvidia/tests/unit/test_speed.py
