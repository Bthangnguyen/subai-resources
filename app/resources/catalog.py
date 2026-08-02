from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PythonRequirement:
    module: str
    requirement: str


@dataclass(frozen=True, slots=True)
class ResourceDefinition:
    """Canonical description of a downloadable SubAI resource.

    ``resource_id`` is the stable ID used by the direct-download UI and by
    self-test results. ``install_dir`` deliberately is a separate value: some
    canonical IDs contain a variant separator (``whisper:tiny``) and all
    Demucs variants share the same Torch checkpoint directory.
    """

    resource_id: str
    name: str
    description: str
    size_label: str
    install_dir: str
    sentinels: tuple[str, ...]
    install_sentinels: tuple[str, ...] = ()
    feature: str | None = None
    required: bool = False
    default_for_feature: bool = False
    model_id: str | None = None
    python_requirements: tuple[PythonRequirement, ...] = ()
    aliases: tuple[str, ...] = ()
    legacy_install_dirs: tuple[str, ...] = ()
    download_url: str | None = None
    repository_id: str | None = None
    revision: str | None = None
    checkpoint_files: tuple[str, ...] = ()
    kind: str = "model"
    platform: str = "windows"
    arch: str = "x86_64"
    device: str = "any"
    protocol: str = ""
    capabilities: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    download_size: int = 0
    install_size: int = 0


@dataclass(frozen=True, slots=True)
class ResourceLayout:
    """Archive/runtime layout accepted by the signed ResourceManager.

    The first four fields retain the old constructor/API. ``install_dir`` and
    ``canonical_id`` let legacy manifest IDs coexist with canonical variant
    IDs without deriving a Windows path from an ID containing ``:``.
    """

    resource_id: str
    description: str
    sentinels: tuple[str, ...]
    required: bool = False
    install_dir: str = ""
    canonical_id: str = ""

    def __post_init__(self) -> None:
        if not self.install_dir:
            object.__setattr__(self, "install_dir", self.resource_id)
        if not self.canonical_id:
            object.__setattr__(self, "canonical_id", self.resource_id)


_FASTER_WHISPER = (
    PythonRequirement("faster_whisper", "faster-whisper>=1.1"),
)
_HUGGING_FACE = (
    PythonRequirement("huggingface_hub", "huggingface-hub>=0.25"),
)
_DEMUCS = (PythonRequirement("demucs", "demucs==4.1.0"),)


_DEFINITIONS = (
    ResourceDefinition(
        "ffmpeg",
        "FFmpeg",
        "Đọc, ghép và xuất video",
        "~130 MB",
        "ffmpeg",
        ("bin/ffmpeg.exe", "bin/ffprobe.exe"),
        required=True,
        kind="tool",
        download_url=(
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
            "ffmpeg-master-latest-win64-gpl.zip"
        ),
    ),
    ResourceDefinition(
        "yt-dlp",
        "yt-dlp",
        "Tải video từ liên kết",
        "~18 MB",
        "yt-dlp",
        ("bin/yt-dlp.exe",),
        feature="download",
        default_for_feature=True,
        kind="tool",
        download_url=(
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
        ),
    ),
    ResourceDefinition(
        "whisper:tiny",
        "Faster-Whisper tiny",
        "Nhận dạng lời nói ngoại tuyến",
        "~75 MB",
        "faster-whisper-tiny",
        ("model.bin", "tokenizer.json"),
        feature="stt",
        model_id="tiny",
        python_requirements=_FASTER_WHISPER + _HUGGING_FACE,
        repository_id="Systran/faster-whisper-tiny",
        revision="d90ca5fe260221311c53c58e660288d3deb8d356",
    ),
    ResourceDefinition(
        "whisper:base",
        "Faster-Whisper base",
        "Nhận dạng lời nói ngoại tuyến",
        "~150 MB",
        "faster-whisper-base",
        ("model.bin", "tokenizer.json"),
        feature="stt",
        model_id="base",
        python_requirements=_FASTER_WHISPER + _HUGGING_FACE,
        repository_id="Systran/faster-whisper-base",
        revision="ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66",
    ),
    ResourceDefinition(
        "whisper:small",
        "Faster-Whisper small",
        "Nhận dạng lời nói ngoại tuyến",
        "~500 MB",
        "faster-whisper-small",
        ("model.bin", "tokenizer.json"),
        feature="stt",
        default_for_feature=True,
        model_id="small",
        python_requirements=_FASTER_WHISPER + _HUGGING_FACE,
        aliases=("faster-whisper",),
        legacy_install_dirs=("faster-whisper",),
        repository_id="Systran/faster-whisper-small",
        revision="536b0662742c02347bc0e980a01041f333bce120",
    ),
    ResourceDefinition(
        "whisper:medium",
        "Faster-Whisper medium",
        "Nhận dạng lời nói ngoại tuyến",
        "~1.5 GB",
        "faster-whisper-medium",
        ("model.bin", "tokenizer.json"),
        feature="stt",
        model_id="medium",
        python_requirements=_FASTER_WHISPER + _HUGGING_FACE,
        repository_id="Systran/faster-whisper-medium",
        revision="08e178d48790749d25932bbc082711ddcfdfbc4f",
    ),
    ResourceDefinition(
        "whisper:large-v3",
        "Faster-Whisper large-v3",
        "Nhận dạng lời nói ngoại tuyến",
        "~3.1 GB",
        "faster-whisper-large-v3",
        ("model.bin", "tokenizer.json"),
        feature="stt",
        model_id="large-v3",
        python_requirements=_FASTER_WHISPER + _HUGGING_FACE,
        repository_id="Systran/faster-whisper-large-v3",
        revision="edaa852ec7e145841d8ffdb056a99866b5f0a478",
    ),
    ResourceDefinition(
        "rapidocr",
        "RapidOCR",
        "Đọc phụ đề cứng trực tiếp từ khung hình",
        "~100 MB",
        "rapidocr",
        ("det.onnx", "rec.onnx"),
        feature="ocr",
        default_for_feature=True,
        python_requirements=(
            PythonRequirement("rapidocr_onnxruntime", "rapidocr-onnxruntime>=1.3"),
        ),
    ),
    ResourceDefinition(
        "demucs:htdemucs",
        "HT Demucs",
        "Cân bằng chất lượng và tốc độ",
        "~85 MB",
        "demucs",
        ("hub/checkpoints/955717e8-8726e21a.th",),
        feature="separation",
        default_for_feature=True,
        model_id="htdemucs",
        python_requirements=_DEMUCS,
        aliases=("demucs",),
        checkpoint_files=("955717e8-8726e21a.th",),
    ),
    ResourceDefinition(
        "demucs:htdemucs_ft",
        "HT Demucs FT",
        "Chất lượng cao, chạy chậm hơn",
        "~340 MB",
        "demucs",
        (
            "hub/checkpoints/f7e0c4bc-ba3fe64a.th",
            "hub/checkpoints/d12395a8-e57c48e6.th",
            "hub/checkpoints/92cfc3b6-ef3bcb9c.th",
            "hub/checkpoints/04573f0d-f3cf25b2.th",
        ),
        feature="separation",
        model_id="htdemucs_ft",
        python_requirements=_DEMUCS,
        checkpoint_files=(
            "f7e0c4bc-ba3fe64a.th",
            "d12395a8-e57c48e6.th",
            "92cfc3b6-ef3bcb9c.th",
            "04573f0d-f3cf25b2.th",
        ),
    ),
    ResourceDefinition(
        "demucs:mdx_extra",
        "MDX Extra",
        "Tách giọng chất lượng cao",
        "~670 MB",
        "demucs",
        (
            "hub/checkpoints/e51eebcc-c1b80bdd.th",
            "hub/checkpoints/a1d90b5c-ae9d2452.th",
            "hub/checkpoints/5d2d6c55-db83574e.th",
            "hub/checkpoints/cfa93e08-61801ae1.th",
        ),
        feature="separation",
        model_id="mdx_extra",
        python_requirements=_DEMUCS,
        checkpoint_files=(
            "e51eebcc-c1b80bdd.th",
            "a1d90b5c-ae9d2452.th",
            "5d2d6c55-db83574e.th",
            "cfa93e08-61801ae1.th",
        ),
    ),
    ResourceDefinition(
        "demucs:htdemucs_6s",
        "HT Demucs 6 nguồn",
        "Tách sáu nhóm âm thanh",
        "~85 MB",
        "demucs",
        ("hub/checkpoints/5c90dfd2-34c22ccb.th",),
        feature="separation",
        model_id="htdemucs_6s",
        python_requirements=_DEMUCS,
        checkpoint_files=("5c90dfd2-34c22ccb.th",),
    ),
    ResourceDefinition(
        "demucs:hdemucs_mmi",
        "Hybrid Demucs MMI",
        "Model hybrid MMI",
        "~170 MB",
        "demucs",
        ("hub/checkpoints/75fc33f5-1941ce65.th",),
        feature="separation",
        model_id="hdemucs_mmi",
        python_requirements=_DEMUCS,
        checkpoint_files=("75fc33f5-1941ce65.th",),
    ),
    ResourceDefinition(
        "demucs:mdx",
        "MDX",
        "Bộ model MDX tiêu chuẩn",
        "~690 MB",
        "demucs",
        (
            "hub/checkpoints/0d19c1c6-0f06f20e.th",
            "hub/checkpoints/7ecf8ec1-70f50cc9.th",
            "hub/checkpoints/c511e2ab-fe698775.th",
            "hub/checkpoints/7d865c68-3d5dd56b.th",
        ),
        feature="separation",
        model_id="mdx",
        python_requirements=_DEMUCS,
        checkpoint_files=(
            "0d19c1c6-0f06f20e.th",
            "7ecf8ec1-70f50cc9.th",
            "c511e2ab-fe698775.th",
            "7d865c68-3d5dd56b.th",
        ),
    ),
    ResourceDefinition(
        "opus-mt",
        "OPUS-MT Trung → Việt",
        "Dịch Trung–Việt ngoại tuyến, không cần API",
        "~320 MB",
        "opus-mt",
        ("config.json", "tokenizer_config.json"),
        install_sentinels=(
            "config.json",
            "tokenizer_config.json",
            "pytorch_model.bin",
        ),
        feature="local-translation",
        default_for_feature=True,
        python_requirements=(
            PythonRequirement("transformers", "transformers>=4.45,<5"),
            PythonRequirement("sentencepiece", "sentencepiece>=0.2"),
            *_HUGGING_FACE,
        ),
        repository_id="Helsinki-NLP/opus-mt-zh-vi",
        revision="67ea2dbfbaf13a16772a40346d3d72b59e591443",
    ),
)


# Runtime packs are deliberately separate from the legacy model/tool registry.
# This preserves old model IDs and layouts while giving the v2 resolver a real
# dependency graph. Archives are built by the resource-pack CI; the desktop app
# never invokes pip on a user's machine.
_RUNTIME_DEFINITIONS = (
    ResourceDefinition(
        "runtime:python:3.12",
        "Python AI 3.12",
        "Python Embedded riêng cho các worker AI",
        "~35 MB",
        "runtime-python-3.12",
        ("python.exe", "python312.dll", "python312._pth"),
        kind="runtime",
        protocol="ndjson-v1",
        capabilities=("python-worker",),
        download_size=35_000_000,
        install_size=90_000_000,
    ),
    ResourceDefinition(
        "runtime:torch:cpu",
        "PyTorch CPU",
        "Runtime PyTorch dùng chung, tương thích mọi máy Windows x64",
        "~260 MB",
        "runtime-torch-cpu",
        ("site-packages/torch/__init__.py", "runtime.json"),
        kind="runtime",
        device="cpu",
        protocol="ndjson-v1",
        capabilities=("torch",),
        requires=("runtime:python:3.12",),
        download_size=260_000_000,
        install_size=850_000_000,
    ),
    ResourceDefinition(
        "runtime:torch:cuda",
        "PyTorch CUDA",
        "Runtime PyTorch CUDA tùy chọn cho GPU NVIDIA tương thích",
        "~2.4 GB",
        "runtime-torch-cuda",
        ("site-packages/torch/__init__.py", "runtime.json"),
        kind="runtime",
        device="cuda",
        protocol="ndjson-v1",
        capabilities=("torch", "cuda"),
        requires=("runtime:python:3.12",),
        download_size=2_400_000_000,
        install_size=5_200_000_000,
    ),
    ResourceDefinition(
        "runtime:whisper:cpu",
        "Faster-Whisper CPU",
        "Thư viện nhận dạng Faster-Whisper chạy trong worker",
        "~95 MB",
        "runtime-whisper-cpu",
        ("site-packages/faster_whisper/__init__.py", "runtime.json"),
        kind="runtime",
        device="cpu",
        protocol="ndjson-v1",
        capabilities=("whisper",),
        feature="stt",
        requires=("runtime:python:3.12",),
        download_size=95_000_000,
        install_size=240_000_000,
    ),
    ResourceDefinition(
        "runtime:whisper:cuda",
        "Faster-Whisper CUDA",
        "Faster-Whisper cùng CUDA/cuDNN DLL đã kiểm thử",
        "~650 MB",
        "runtime-whisper-cuda",
        ("site-packages/faster_whisper/__init__.py", "runtime.json"),
        kind="runtime",
        device="cuda",
        protocol="ndjson-v1",
        capabilities=("whisper", "cuda"),
        feature="stt",
        # CTranslate2 reuses the CUDA/cuDNN DLLs shipped in the shared Torch
        # CUDA pack instead of depending on a system CUDA installation.
        requires=("runtime:python:3.12", "runtime:torch:cuda"),
        download_size=650_000_000,
        install_size=1_450_000_000,
    ),
    ResourceDefinition(
        "runtime:rapidocr:cpu",
        "RapidOCR / ONNX CPU",
        "RapidOCR và ONNX Runtime chạy trong worker",
        "~80 MB",
        "runtime-rapidocr-cpu",
        ("site-packages/rapidocr_onnxruntime/__init__.py", "runtime.json"),
        kind="runtime",
        device="cpu",
        protocol="ndjson-v1",
        capabilities=("rapidocr",),
        feature="ocr",
        requires=("runtime:python:3.12",),
        download_size=80_000_000,
        install_size=220_000_000,
    ),
    ResourceDefinition(
        "runtime:demucs",
        "Demucs",
        "Thư viện Demucs; dùng chung runtime PyTorch",
        "~45 MB",
        "runtime-demucs",
        ("site-packages/demucs/__init__.py", "runtime.json"),
        kind="runtime",
        protocol="ndjson-v1",
        capabilities=("demucs",),
        feature="separation",
        requires=("runtime:python:3.12", "runtime:torch:cpu"),
        download_size=45_000_000,
        install_size=130_000_000,
    ),
    ResourceDefinition(
        "runtime:opus-mt",
        "Transformers / OPUS-MT",
        "Transformers và SentencePiece; dùng chung runtime PyTorch",
        "~55 MB",
        "runtime-opus-mt",
        ("site-packages/transformers/__init__.py", "runtime.json"),
        kind="runtime",
        protocol="ndjson-v1",
        capabilities=("opus-mt",),
        feature="local-translation",
        requires=("runtime:python:3.12", "runtime:torch:cpu"),
        download_size=55_000_000,
        install_size=180_000_000,
    ),
    ResourceDefinition(
        "runtime:funasr",
        "FunASR",
        "FunASR và các adapter model; dùng chung runtime PyTorch",
        "~180 MB",
        "runtime-funasr",
        ("site-packages/funasr/__init__.py", "runtime.json"),
        kind="runtime",
        protocol="ndjson-v1",
        capabilities=("funasr",),
        feature="funasr",
        requires=("runtime:python:3.12", "runtime:torch:cpu"),
        download_size=180_000_000,
        install_size=520_000_000,
    ),
    ResourceDefinition(
        "funasr:paraformer-zh",
        "FunASR Paraformer tiếng Trung",
        "ASR, VAD, dấu câu và CAM++ cho video tiếng Trung",
        "~2.0 GB",
        "funasr-paraformer-zh",
        ("model/.complete", "vad/.complete", "punctuation/.complete"),
        feature="funasr",
        default_for_feature=True,
        model_id="paraformer-zh",
        kind="model",
        capabilities=("funasr", "vad", "punctuation", "speaker"),
        requires=("runtime:funasr",),
        download_size=2_000_000_000,
        install_size=3_400_000_000,
    ),
)


RESOURCE_REGISTRY: dict[str, ResourceDefinition] = {
    definition.resource_id: definition for definition in _DEFINITIONS
}
RESOURCE_PACK_REGISTRY: dict[str, ResourceDefinition] = {
    **RESOURCE_REGISTRY,
    **{definition.resource_id: definition for definition in _RUNTIME_DEFINITIONS},
}
RESOURCE_ALIASES: dict[str, str] = {
    alias: definition.resource_id
    for definition in _DEFINITIONS
    for alias in definition.aliases
}


def canonical_resource_id(resource_id: str) -> str:
    normalized = str(resource_id).strip().lower()
    canonical = RESOURCE_ALIASES.get(normalized, normalized)
    if canonical not in RESOURCE_PACK_REGISTRY:
        raise KeyError(resource_id)
    return canonical


def get_resource_definition(resource_id: str) -> ResourceDefinition:
    return RESOURCE_PACK_REGISTRY[canonical_resource_id(resource_id)]


def resource_install_dirs(resource_id: str) -> tuple[str, ...]:
    definition = get_resource_definition(resource_id)
    return (definition.install_dir, *definition.legacy_install_dirs)


def _make_layouts() -> dict[str, ResourceLayout]:
    layouts = {
        definition.resource_id: ResourceLayout(
            definition.resource_id,
            definition.description,
            definition.sentinels,
            definition.required,
            definition.install_dir,
            definition.resource_id,
        )
        for definition in (*_DEFINITIONS, *_RUNTIME_DEFINITIONS)
    }
    for alias, canonical in RESOURCE_ALIASES.items():
        definition = RESOURCE_REGISTRY[canonical]
        alias_dir = (
            definition.legacy_install_dirs[0]
            if definition.legacy_install_dirs
            else definition.install_dir
        )
        layouts[alias] = ResourceLayout(
            alias,
            definition.description,
            definition.sentinels,
            definition.required,
            alias_dir,
            canonical,
        )
    return layouts


# Compatibility API for signed manifests and callers written before the
# canonical variant registry. It includes both canonical IDs and old aliases.
RESOURCE_LAYOUTS: dict[str, ResourceLayout] = _make_layouts()
FULL_RESOURCE_IDS = tuple(RESOURCE_REGISTRY)
FULL_PACK_IDS = tuple(RESOURCE_PACK_REGISTRY)
WHISPER_MODEL_IDS = tuple(
    definition.model_id
    for definition in _DEFINITIONS
    if definition.resource_id.startswith("whisper:") and definition.model_id
)
DEMUCS_MODEL_IDS = tuple(
    definition.model_id
    for definition in _DEFINITIONS
    if definition.resource_id.startswith("demucs:") and definition.model_id
)
