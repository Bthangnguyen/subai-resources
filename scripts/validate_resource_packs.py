from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from app.resources.catalog import RESOURCE_PACK_REGISTRY, ResourceDefinition

_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")


@dataclass(frozen=True, slots=True)
class ValidatedPack:
    definition: ResourceDefinition
    version: str
    archive: Path
    files: tuple[str, ...]


def _safe_files(archive: zipfile.ZipFile) -> tuple[str, ...]:
    files: list[str] = []
    for info in archive.infolist():
        raw = info.filename.replace("\\", "/")
        path = PurePosixPath(raw)
        if (
            path.is_absolute()
            or ".." in path.parts
            or (path.parts and ":" in path.parts[0])
        ):
            raise ValueError(f"Unsafe archive path: {info.filename}")
        if not info.is_dir():
            files.append(str(path))
    return tuple(sorted(files))


def _match_archive(path: Path) -> tuple[ResourceDefinition, str] | None:
    stem = path.stem
    matches = []
    for definition in RESOURCE_PACK_REGISTRY.values():
        prefix = definition.resource_id.replace(":", "-") + "-"
        if stem.startswith(prefix):
            matches.append((definition, stem[len(prefix) :]))
    if not matches:
        return None
    definition, version = max(matches, key=lambda item: len(item[0].resource_id))
    if not _VERSION_RE.fullmatch(version):
        raise ValueError(f"Invalid pack version in filename: {path.name}")
    return definition, version


def validate_pack(path: Path) -> ValidatedPack | None:
    matched = _match_archive(path)
    if matched is None:
        return None
    definition, version = matched
    with zipfile.ZipFile(path) as archive:
        files = _safe_files(archive)
        required = definition.install_sentinels or definition.sentinels
        missing = [sentinel for sentinel in required if sentinel not in files]
        if missing:
            raise ValueError(
                f"{path.name} is missing required files: {', '.join(missing)}"
            )
        try:
            metadata = json.loads(archive.read("pack-metadata.json"))
        except KeyError as exc:
            raise ValueError(f"{path.name} has no pack-metadata.json") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"{path.name} has invalid pack metadata") from exc
        if not isinstance(metadata, dict):
            raise ValueError(f"{path.name} pack metadata must be an object")
        if metadata.get("id") != definition.resource_id:
            raise ValueError(f"{path.name} metadata resource ID does not match")
        if metadata.get("version") != version:
            raise ValueError(f"{path.name} metadata version does not match")
    return ValidatedPack(definition, version, path, files)


def validate_pack_directory(
    directory: Path,
    *,
    require_complete: bool = True,
) -> tuple[ValidatedPack, ...]:
    validated: list[ValidatedPack] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("*.zip")):
        pack = validate_pack(path)
        if pack is None:
            continue
        resource_id = pack.definition.resource_id
        if resource_id in seen:
            raise ValueError(f"Multiple archives provide resource: {resource_id}")
        seen.add(resource_id)
        validated.append(pack)
    if require_complete:
        missing = sorted(set(RESOURCE_PACK_REGISTRY) - seen)
        if missing:
            raise ValueError(
                "Resource catalog has no built archive for: " + ", ".join(missing)
            )
    if not validated:
        raise ValueError(f"No valid resource packs found under {directory}")
    return tuple(validated)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pack_dir", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    packs = validate_pack_directory(
        args.pack_dir,
        require_complete=not args.allow_partial,
    )
    print(f"Validated {len(packs)} resource pack(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
