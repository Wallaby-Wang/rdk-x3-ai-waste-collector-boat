param(
  [string]$OutDir = "models"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$models = @(
  @{
    Name = "yolov5n_tag_v7.0_detect_640x640_bernoulli2_nv12.bin"
    Url = "https://archive.d-robotics.cc/downloads/rdk_model_zoo/rdk_x3/yolov5n_tag_v7.0_detect_640x640_bernoulli2_nv12.bin"
  },
  @{
    Name = "yolov5s_tag_v7.0_detect_640x640_bernoulli2_nv12.bin"
    Url = "https://archive.d-robotics.cc/downloads/rdk_model_zoo/rdk_x3/yolov5s_tag_v7.0_detect_640x640_bernoulli2_nv12.bin"
  }
)

$hashLines = @()
foreach ($model in $models) {
  $target = Join-Path $OutDir $model.Name
  if (!(Test-Path $target)) {
    Write-Host "Downloading $($model.Name)"
    curl.exe -L $model.Url -o $target
  } else {
    Write-Host "Exists $($model.Name)"
  }
  $hash = (Get-FileHash -Algorithm SHA256 $target).Hash.ToLowerInvariant()
  $hashLines += "$hash  $($model.Name)"
}

$hashLines | Set-Content -Path (Join-Path $OutDir "SHA256SUMS") -Encoding utf8
Write-Host "Wrote $(Join-Path $OutDir 'SHA256SUMS')"
