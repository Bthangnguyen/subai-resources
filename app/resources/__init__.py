from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .catalog import (
    DEMUCS_MODEL_IDS,
    FULL_PACK_IDS,
    FULL_RESOURCE_IDS,
    RESOURCE_ALIASES,
    RESOURCE_LAYOUTS,
    RESOURCE_PACK_REGISTRY,
    RESOURCE_REGISTRY,
    WHISPER_MODEL_IDS,
    ResourceDefinition,
    ResourceLayout,
    canonical_resource_id,
    get_resource_definition,
)

if TYPE_CHECKING:
    from .manager import ResourceManager, ResourceSpec


_MANAGER_EXPORTS = {
    "ResourceError",
    "ResourceManager",
    "ResourceSpec",
    "canonical_manifest_bytes",
    "validate_manifest_public_key",
    "verify_manifest_signature",
}


def __getattr__(name: str) -> Any:
    """Load the signed manager lazily to keep runtime_paths cycle-free."""

    if name in _MANAGER_EXPORTS:
        from . import manager

        value = getattr(manager, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "DEMUCS_MODEL_IDS",
    "FULL_PACK_IDS",
    "FULL_RESOURCE_IDS",
    "RESOURCE_ALIASES",
    "RESOURCE_LAYOUTS",
    "RESOURCE_PACK_REGISTRY",
    "RESOURCE_REGISTRY",
    "WHISPER_MODEL_IDS",
    "ResourceDefinition",
    "ResourceError",
    "ResourceLayout",
    "ResourceManager",
    "ResourceSpec",
    "canonical_manifest_bytes",
    "canonical_resource_id",
    "get_resource_definition",
    "validate_manifest_public_key",
    "verify_manifest_signature",
]
