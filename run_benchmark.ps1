# QAM Benchmark Runner (PowerShell)
# Set $env:IBM_QUANTUM_TOKEN before running for real QPU execution,
# or pass --local for zero-quota StatevectorSampler verification.

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = $PSScriptRoot

Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot "results") | Out-Null
    python -u -m src.qam_benchmark @args 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot "results\qam_full_benchmark.log")
}
finally {
    Pop-Location
}
