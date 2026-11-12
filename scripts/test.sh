#!/bin/bash
# test.sh - checks minimos via uv (python 3.13)
set -e
export PATH="$HOME/.local/bin:$PATH"
uv run --project ~/yolo-nvidia python --version
uv run --project ~/yolo-nvidia python outputs/inspect/summ.py
echo "tests: ffprobe.json + frames existen"
test -f ~/yolo-nvidia/outputs/inspect/ffprobe.json
ls ~/yolo-nvidia/inspect/*.jpg ~/yolo-nvidia/outputs/inspect/ 2>/dev/null || true
