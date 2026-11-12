#!/bin/bash
# setup.sh - verifica WSL2 + GPU + docker + uv + ffmpeg
set -e
set -x
nvidia-smi
docker info --format '{{.ServerVersion}} runtimes={{json .Runtimes}}'
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
/home/marti/.local/bin/uv --version
ffprobe -version | head -n 1
vim --version | head -n 1
