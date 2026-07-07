#!/usr/bin/env bash
set -euo pipefail

out_dir="${1:-models}"
mkdir -p "$out_dir"

download() {
  local name="$1"
  local url="$2"
  if [[ ! -f "$out_dir/$name" ]]; then
    echo "Downloading $name"
    curl -L "$url" -o "$out_dir/$name"
  else
    echo "Exists $name"
  fi
}

download "yolov5n_tag_v7.0_detect_640x640_bernoulli2_nv12.bin" \
  "https://archive.d-robotics.cc/downloads/rdk_model_zoo/rdk_x3/yolov5n_tag_v7.0_detect_640x640_bernoulli2_nv12.bin"
download "yolov5s_tag_v7.0_detect_640x640_bernoulli2_nv12.bin" \
  "https://archive.d-robotics.cc/downloads/rdk_model_zoo/rdk_x3/yolov5s_tag_v7.0_detect_640x640_bernoulli2_nv12.bin"

(cd "$out_dir" && sha256sum \
  yolov5n_tag_v7.0_detect_640x640_bernoulli2_nv12.bin \
  yolov5s_tag_v7.0_detect_640x640_bernoulli2_nv12.bin > SHA256SUMS)

echo "Wrote $out_dir/SHA256SUMS"
