from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from app.resources.catalog import get_resource_definition


def download(url: str, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=180) as response, target.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    return target


def snapshot(repository: str, revision: str, stage: Path) -> None:
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=repository,
        revision=revision,
        local_dir=stage,
        local_dir_use_symlinks=False,
    )


def build_ffmpeg(stage: Path, temporary: Path, url: str) -> None:
    archive = download(url, temporary / "ffmpeg.zip")
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        for filename in ("ffmpeg.exe", "ffprobe.exe"):
            member = next(
                name
                for name in names
                if name.lower().endswith(f"/bin/{filename}")
            )
            target = stage / "bin" / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)


def build_rapidocr(stage: Path, temporary: Path) -> None:
    package = temporary / "rapidocr"
    subprocess.run(
        [
            "python",
            "-m",
            "pip",
            "install",
            "--target",
            str(package),
            "rapidocr-onnxruntime==1.4.4",
        ],
        check=True,
    )
    models = list(package.rglob("*.onnx"))
    for token in ("det", "rec", "cls"):
        source = next((item for item in models if token in item.name.lower()), None)
        if source is not None:
            shutil.copy2(source, stage / f"{token}.onnx")


def demucs_url(filename: str) -> str:
    hybrid = {
        "955717e8",
        "f7e0c4bc",
        "d12395a8",
        "92cfc3b6",
        "04573f0d",
        "75fc33f5",
        "5c90dfd2",
    }
    folder = "hybrid_transformer" if filename.split("-", 1)[0] in hybrid else "mdx_final"
    return f"https://dl.fbaipublicfiles.com/demucs/{folder}/{filename}"


def build_funasr(stage: Path) -> None:
    from modelscope.hub.snapshot_download import snapshot_download

    repositories = {
        "model": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        "vad": "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
        "punctuation": "iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
        "speaker": "iic/speech_campplus_sv_zh-cn_16k-common",
    }
    for name, repository in repositories.items():
        destination = stage / name
        source = Path(snapshot_download(repository)).resolve()
        shutil.copytree(source, destination, dirs_exist_ok=True)
        (destination / ".complete").write_text(repository, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("resource_id")
    parser.add_argument("version")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    definition = get_resource_definition(args.resource_id)
    safe_id = args.resource_id.replace(":", "-")
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="subai-resource-") as raw_temporary:
        temporary = Path(raw_temporary)
        stage = temporary / "stage"
        stage.mkdir()
        if args.resource_id == "ffmpeg":
            build_ffmpeg(stage, temporary, str(definition.download_url))
        elif args.resource_id == "yt-dlp":
            target = stage / "bin" / "yt-dlp.exe"
            download(str(definition.download_url), target)
        elif (
            args.resource_id.startswith("whisper:")
            or args.resource_id in {"opus-mt", "omnivoice"}
        ):
            snapshot(str(definition.repository_id), str(definition.revision), stage)
        elif args.resource_id == "rapidocr":
            build_rapidocr(stage, temporary)
        elif args.resource_id.startswith("demucs:"):
            for filename in definition.checkpoint_files:
                download(demucs_url(filename), stage / "hub" / "checkpoints" / filename)
        elif args.resource_id.startswith("funasr:"):
            build_funasr(stage)
        else:
            parser.error(f"Unsupported model/tool resource: {args.resource_id}")
        (stage / "pack-metadata.json").write_text(
            json.dumps(
                {"id": args.resource_id, "version": args.version},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        archive = args.output / f"{safe_id}-{args.version}.zip"
        shutil.make_archive(str(archive.with_suffix("")), "zip", stage)
        print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
