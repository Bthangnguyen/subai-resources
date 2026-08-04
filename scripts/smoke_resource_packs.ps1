param([Parameter(Mandatory)][string]$PackDirectory)

$ErrorActionPreference = "Stop"
$packRoot = (Resolve-Path -LiteralPath $PackDirectory).Path
$smokeRoot = Join-Path $packRoot ".smoke"
if (Test-Path -LiteralPath $smokeRoot) { Remove-Item -LiteralPath $smokeRoot -Recurse -Force }
New-Item -ItemType Directory -Path $smokeRoot -Force | Out-Null

function Expand-Pack([string]$Pattern, [string]$Name) {
    $archive = Get-ChildItem -LiteralPath $packRoot -Filter $Pattern | Select-Object -First 1
    if (-not $archive) { throw "Missing resource pack matching $Pattern" }
    $target = Join-Path $smokeRoot $Name
    Expand-Archive -LiteralPath $archive.FullName -DestinationPath $target
    return $target
}

$pythonPack = Expand-Pack "runtime-python-3.12-*.zip" "python"
$python = Join-Path $pythonPack "python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw "Embedded python.exe is missing" }

$torchCpu = Expand-Pack "runtime-torch-cpu-*.zip" "torch-cpu"
$torchCuda = Expand-Pack "runtime-torch-cuda-*.zip" "torch-cuda"
$whisperCpu = Expand-Pack "runtime-whisper-cpu-*.zip" "whisper-cpu"
$rapidOcr = Expand-Pack "runtime-rapidocr-cpu-*.zip" "rapidocr"
$demucs = Expand-Pack "runtime-demucs-*.zip" "demucs"
$opus = Expand-Pack "runtime-opus-mt-*.zip" "opus"
$funasr = Expand-Pack "runtime-funasr-*.zip" "funasr"
$omnivoice = Expand-Pack "runtime-omnivoice-*.zip" "omnivoice"
$whisperTiny = Expand-Pack "whisper-tiny-*.zip" "whisper-tiny-model"

function Test-Imports([string[]]$Packs, [string[]]$Modules) {
    $paths = @($Packs | ForEach-Object { Join-Path $_ "site-packages" })
    # -InputObject preserves a one-element list as a JSON array. Piping a
    # single path would serialize it as a string and insert path characters
    # into sys.path one by one.
    $pathJson = ConvertTo-Json -InputObject @($paths) -Compress
    $moduleJson = ConvertTo-Json -InputObject @($Modules) -Compress
    $code = "import json,sys; sys.path[:0]=json.loads(r'''$pathJson'''); [__import__(m) for m in json.loads(r'''$moduleJson''')]; print('ok')"
    & $python -I -c $code
    if ($LASTEXITCODE -ne 0) { throw "Resource pack import smoke-test failed: $($Modules -join ', ')" }
}

Test-Imports -Packs @($whisperCpu) -Modules @("faster_whisper", "ctranslate2")
Test-Imports -Packs @($rapidOcr) -Modules @("rapidocr_onnxruntime", "onnxruntime")
Test-Imports -Packs @($torchCpu, $demucs) -Modules @("torch", "demucs", "soundfile")
Test-Imports -Packs @($torchCpu, $opus) -Modules @("torch", "transformers", "sentencepiece")
Test-Imports -Packs @($torchCpu, $funasr) -Modules @("torch", "torchaudio", "funasr")
Test-Imports -Packs @($torchCuda, $omnivoice) -Modules @("torch", "torchaudio", "omnivoice", "soundfile")
$whisperSite = Join-Path $whisperCpu "site-packages"
$whisperCode = "import sys; sys.path.insert(0,r'''$whisperSite'''); from faster_whisper import WhisperModel; model=WhisperModel(r'''$whisperTiny''',device='cpu',compute_type='int8'); print(type(model).__name__)"
& $python -I -c $whisperCode
if ($LASTEXITCODE -ne 0) { throw "Faster-Whisper could not load the packaged Tiny model" }
Write-Host "Resource packs passed clean embedded-runtime import smoke tests."
