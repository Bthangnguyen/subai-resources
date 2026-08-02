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
$whisperCpu = Expand-Pack "runtime-whisper-cpu-*.zip" "whisper-cpu"
$rapidOcr = Expand-Pack "runtime-rapidocr-cpu-*.zip" "rapidocr"
$demucs = Expand-Pack "runtime-demucs-*.zip" "demucs"
$opus = Expand-Pack "runtime-opus-mt-*.zip" "opus"
$funasr = Expand-Pack "runtime-funasr-*.zip" "funasr"
$whisperTiny = Expand-Pack "whisper-tiny-*.zip" "whisper-tiny-model"

function Test-Imports([string[]]$Packs, [string[]]$Modules) {
    $paths = @($Packs | ForEach-Object { Join-Path $_ "site-packages" })
    $pathJson = $paths | ConvertTo-Json -Compress
    $moduleJson = $Modules | ConvertTo-Json -Compress
    $code = "import json,sys; sys.path[:0]=json.loads(r'''$pathJson'''); [__import__(m) for m in json.loads(r'''$moduleJson''')]; print('ok')"
    & $python -I -c $code
    if ($LASTEXITCODE -ne 0) { throw "Resource pack import smoke-test failed: $($Modules -join ', ')" }
}

Test-Imports -Packs @($whisperCpu) -Modules @("faster_whisper", "ctranslate2")
Test-Imports -Packs @($rapidOcr) -Modules @("rapidocr_onnxruntime", "onnxruntime")
Test-Imports -Packs @($torchCpu, $demucs) -Modules @("torch", "demucs", "soundfile")
Test-Imports -Packs @($torchCpu, $opus) -Modules @("torch", "transformers", "sentencepiece")
Test-Imports -Packs @($torchCpu, $funasr) -Modules @("torch", "torchaudio", "funasr")
$whisperSite = Join-Path $whisperCpu "site-packages"
$whisperCode = "import sys; sys.path.insert(0,r'''$whisperSite'''); from faster_whisper import WhisperModel; model=WhisperModel(r'''$whisperTiny''',device='cpu',compute_type='int8'); print(type(model).__name__)"
& $python -I -c $whisperCode
if ($LASTEXITCODE -ne 0) { throw "Faster-Whisper could not load the packaged Tiny model" }
Write-Host "CPU resource packs passed clean embedded-runtime smoke tests."
