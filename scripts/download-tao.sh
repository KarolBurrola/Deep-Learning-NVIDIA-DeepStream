#!/bin/bash
set -e
BASE=~/yolo-nvidia/thirdparty/deepstream_tao_apps/models
mkdir -p "$BASE/trafficcamnet" "$BASE/LPD_us" "$BASE/LPR_us"
cd "$BASE/trafficcamnet"
[ -f resnet18_trafficcamnet_pruned.onnx ] || wget --content-disposition "https://api.ngc.nvidia.com/v2/models/org/nvidia/team/tao/trafficcamnet/pruned_onnx_v1.0.4/files?redirect=true&path=resnet18_trafficcamnet_pruned.onnx" -O resnet18_trafficcamnet_pruned.onnx
cd "$BASE/LPD_us"
[ -f LPDNet_usa_pruned_tao5.onnx ] || wget --content-disposition "https://api.ngc.nvidia.com/v2/models/org/nvidia/team/tao/lpdnet/pruned_v2.3.1/files?redirect=true&path=LPDNet_usa_pruned_tao5.onnx" -O LPDNet_usa_pruned_tao5.onnx
cd "$BASE/LPR_us"
[ -f us_lprnet_baseline18_deployable.onnx ] || wget --content-disposition "https://api.ngc.nvidia.com/v2/models/org/nvidia/team/tao/lprnet/deployable_onnx_v1.1/files?redirect=true&path=us_lprnet_baseline18_deployable.onnx" -O us_lprnet_baseline18_deployable.onnx
ls -lh "$BASE/trafficcamnet" "$BASE/LPD_us" "$BASE/LPR_us"
