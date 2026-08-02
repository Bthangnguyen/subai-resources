from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.validate_resource_packs import validate_pack_directory


def canonical_manifest_bytes(payload: dict) -> bytes:
    """Serialize signed content without importing the desktop application."""

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def load_private_key(value: str) -> Ed25519PrivateKey:
    text = value.strip()
    if text.startswith("-----BEGIN"):
        key = serialization.load_pem_private_key(text.encode("ascii"), password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise TypeError("Signing key is not Ed25519")
        return key
    raw = base64.b64decode(text + "=" * (-len(text) % 4))
    if len(raw) != 32:
        raise ValueError("Ed25519 private key seed must be 32 bytes")
    return Ed25519PrivateKey.from_private_bytes(raw)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pack_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--owner", default=os.environ.get("SUBAI_RESOURCE_OWNER", ""))
    parser.add_argument("--repository", default="subai-resources")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    if not args.owner:
        parser.error("--owner or SUBAI_RESOURCE_OWNER is required")
    key_value = os.environ.get("SUBAI_RESOURCE_SIGNING_KEY", "")
    if not key_value:
        parser.error("SUBAI_RESOURCE_SIGNING_KEY GitHub Secret is required")
    packs = validate_pack_directory(
        args.pack_dir,
        require_complete=not args.allow_partial,
    )
    resources = []
    for pack in packs:
        archive = pack.archive
        definition = pack.definition
        resource_id = definition.resource_id
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        resources.append(
            {
                "id": resource_id,
                "kind": definition.kind,
                "version": pack.version,
                "platform": definition.platform,
                "arch": definition.arch,
                "device": definition.device,
                "protocol": definition.protocol,
                "capabilities": list(definition.capabilities),
                "requires": list(definition.requires),
                "download_url": (
                    f"https://github.com/{args.owner}/{args.repository}/releases/"
                    f"download/{args.tag}/{archive.name}"
                ),
                "sha256": digest,
                "download_size": archive.stat().st_size,
                "install_size": definition.install_size,
                "sentinels": list(
                    definition.install_sentinels or definition.sentinels
                ),
                "files": list(pack.files),
            }
        )
    signed = {"schema_version": 2, "resources": resources}
    signature = load_private_key(key_value).sign(canonical_manifest_bytes(signed))
    payload = {
        "signed": signed,
        "signature": {
            "algorithm": "Ed25519",
            "value": base64.b64encode(signature).decode("ascii"),
        },
    }
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
