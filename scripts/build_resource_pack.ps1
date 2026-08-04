param(
    [Parameter(Mandatory)][string]$ResourceId,
    [Parameter(Mandatory)][string]$Version,
    [string]$OutputDirectory = "resource-dist"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$output = [System.IO.Path]::GetFullPath((Join-Path $root $OutputDirectory))
$safeId = $ResourceId -replace '[^A-Za-z0-9._-]', '-'
$stage = Join-Path $output "stage-$safeId"
if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage -Force | Out-Null

$pythonUrl = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"
$pythonSha256 = "4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3"
$lockMap = @{
    "runtime:torch:cpu" = "torch-cpu.lock"
    "runtime:torch:cuda" = "torch-cuda.lock"
    "runtime:whisper:cpu" = "whisper.lock"
    "runtime:whisper:cuda" = "whisper.lock"
    "runtime:rapidocr:cpu" = "rapidocr.lock"
    "runtime:demucs" = "demucs.lock"
    "runtime:opus-mt" = "opus-mt.lock"
    "runtime:funasr" = "funasr.lock"
    "runtime:omnivoice" = "omnivoice.lock"
}

if ($ResourceId -eq "runtime:python:3.12") {
    $archive = Join-Path $output "python-embed.zip"
    Invoke-WebRequest -Uri $pythonUrl -OutFile $archive
    $actualHash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $pythonSha256) {
        throw "CPython Embedded SHA-256 mismatch: $actualHash"
    }
    Expand-Archive -LiteralPath $archive -DestinationPath $stage
    $pth = Join-Path $stage "python312._pth"
    [System.IO.File]::WriteAllLines(
        $pth,
        @("python312.zip", ".", "import site"),
        [System.Text.UTF8Encoding]::new($false)
    )
}
elseif ($lockMap.ContainsKey($ResourceId)) {
    $site = Join-Path $stage "site-packages"
    New-Item -ItemType Directory -Path $site -Force | Out-Null
    $lock = Join-Path $root ("resource-packs\locks\" + $lockMap[$ResourceId])
    # Source distributions are permitted only in CI while constructing the
    # prebuilt archive (for example jieba and Demucs). End-user machines never
    # run pip or compile packages.
    $pipArgs = @("install", "--target", $site, "-r", $lock)
    if ($ResourceId -eq "runtime:omnivoice") {
        # The complete lock deliberately excludes torch/torchaudio because
        # those are supplied by the shared runtime:torch:cuda pack.
        $pipArgs += "--no-deps"
    }
    if ($ResourceId -eq "runtime:torch:cpu") {
        $pipArgs += @(
            "--index-url", "https://download.pytorch.org/whl/cpu",
            "--extra-index-url", "https://pypi.org/simple"
        )
    }
    elseif ($ResourceId -eq "runtime:torch:cuda") {
        $pipArgs += @(
            "--index-url", "https://download.pytorch.org/whl/cu128",
            "--extra-index-url", "https://pypi.org/simple"
        )
    }
    python -m pip @pipArgs
    if ($LASTEXITCODE -ne 0) { throw "Failed to build $ResourceId from $lock" }
    if (-not $ResourceId.StartsWith("runtime:torch:")) {
        Get-ChildItem -LiteralPath $site -Force | Where-Object {
            $_.Name -match '^(torch|torchaudio|torchvision)(-|\.|$)'
        } | Remove-Item -Recurse -Force
    }
    Get-ChildItem -LiteralPath $site -Directory -Recurse -Filter __pycache__ |
        Remove-Item -Recurse -Force
    $runtime = [ordered]@{
        protocol = "ndjson-v1"
        resource_id = $ResourceId
        version = $Version
        python = "3.12"
        platform = "windows"
        arch = "x86_64"
    }
    [System.IO.File]::WriteAllText(
        (Join-Path $stage "runtime.json"),
        ($runtime | ConvertTo-Json),
        [System.Text.UTF8Encoding]::new($false)
    )
}
else {
    throw "Model/tool pack '$ResourceId' must be staged by its pinned source job."
}

$metadata = [ordered]@{
    id = $ResourceId
    version = $Version
    platform = "windows"
    arch = "x86_64"
}
[System.IO.File]::WriteAllText(
    (Join-Path $stage "pack-metadata.json"),
    ($metadata | ConvertTo-Json),
    [System.Text.UTF8Encoding]::new($false)
)
$zip = Join-Path $output "$safeId-$Version.zip"
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip -CompressionLevel Optimal
Write-Host $zip
