#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build an exact, secret-free Hugging Face Space publication directory.

This program performs no network request and no provider mutation. The existing
canonical writer may consume the generated directory only after protected main
and the exact source SHA have been independently qualified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Final

HERE: Final = Path(__file__).resolve().parent
CONTRACT_PATH: Final = HERE / "PUBLICATION.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
TOKEN_RE = re.compile(r"(?:github_pat_|gh[pousr]_|hf_)[A-Za-z0-9_]{12,}")
MAX_CONTRACT_BYTES: Final = 128_000
MAX_FILE_BYTES: Final = 2_000_000
MAX_FILES: Final = 32


class PublicationError(ValueError):
    """The package cannot be built without violating its exact contract."""


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise PublicationError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strict_relative(value: str, *, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise PublicationError(f"invalid {label} path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise PublicationError(f"unsafe {label} path: {value!r}")
    return path


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) > MAX_CONTRACT_BYTES:
        raise PublicationError("publication contract exceeded byte limit")
    if TOKEN_RE.search(raw.decode("utf-8", "replace")):
        raise PublicationError("credential-shaped material in publication contract")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=duplicate_guard)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PublicationError(f"invalid publication contract: {type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise PublicationError("publication contract must be an object")
    if value.get("schema") != "szl.hf-publication-contract/v1":
        raise PublicationError("unexpected publication schema")
    if value.get("source_repository") != "szl-holdings/szl-atelier":
        raise PublicationError("source repository drifted")
    target = value.get("target")
    if not isinstance(target, dict) or target.get("repository") != "SZLHOLDINGS/szl-atelier":
        raise PublicationError("Space target drifted")
    if value.get("canonical_writer") != ".github/workflows/hf-space.yml":
        raise PublicationError("canonical writer drifted")
    mapping = value.get("mapping")
    if not isinstance(mapping, list) or not 1 <= len(mapping) <= MAX_FILES:
        raise PublicationError("mapping count outside bounds")
    targets: set[PurePosixPath] = set()
    for index, row in enumerate(mapping):
        if not isinstance(row, dict) or set(row) != {"source", "target"}:
            raise PublicationError(f"invalid mapping row {index}")
        strict_relative(row["source"], label="source")
        target_path = strict_relative(row["target"], label="target")
        if target_path in targets:
            raise PublicationError(f"duplicate target path: {target_path}")
        targets.add(target_path)
    if PurePosixPath("README.md") not in targets or PurePosixPath("Dockerfile") not in targets:
        raise PublicationError("Space front door is incomplete")
    return value


def build(source_sha: str, output: Path) -> dict[str, Any]:
    if not SHA40.fullmatch(source_sha):
        raise PublicationError("source SHA must be exact lowercase 40-character hex")
    contract = load_contract()
    output = output.resolve()
    if output == HERE or HERE in output.parents:
        raise PublicationError("output overlaps the source package")
    if output.exists() and any(output.iterdir()):
        raise PublicationError("output directory must be absent or empty")
    output.parent.mkdir(parents=True, exist_ok=True)

    source_files: dict[str, dict[str, Any]] = {}
    target_files: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="atelier-publish-", dir=output.parent) as temporary:
        stage = Path(temporary)
        for row in contract["mapping"]:
            source_rel = strict_relative(row["source"], label="source")
            target_rel = strict_relative(row["target"], label="target")
            source = HERE.joinpath(*source_rel.parts)
            if source.is_symlink() or not source.is_file():
                raise PublicationError(f"source file unavailable or symlinked: {source_rel}")
            data = source.read_bytes()
            if len(data) > MAX_FILE_BYTES:
                raise PublicationError(f"source file exceeded byte limit: {source_rel}")
            if TOKEN_RE.search(data.decode("utf-8", "replace")):
                raise PublicationError(f"credential-shaped material in source: {source_rel}")
            target = stage.joinpath(*target_rel.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            source_files[str(source_rel)] = {"bytes": len(data), "sha256": digest(data)}
            target_files[str(target_rel)] = {"bytes": len(data), "sha256": digest(data)}

        source_bytes = (source_sha + "\n").encode("ascii")
        (stage / "SOURCE_REVISION").write_bytes(source_bytes)
        target_files["SOURCE_REVISION"] = {"bytes": len(source_bytes), "sha256": digest(source_bytes)}

        receipt_value = {
            "schema": "szl.hf-publication-package/v1",
            "state": "PACKAGE_BUILT_NOT_PUBLISHED",
            "source_repository": contract["source_repository"],
            "source_sha": source_sha,
            "target": contract["target"],
            "canonical_writer": contract["canonical_writer"],
            "source_files": source_files,
            "target_files": target_files,
            "hub_commit": "UNAVAILABLE_NOT_PUBLISHED",
            "runtime_ready": "UNAVAILABLE_NOT_PUBLISHED",
            "exact_readback_verified": False,
            "secrets_recorded": False,
        }
        receipt_value["package_receipt_sha256"] = digest(canonical_bytes(receipt_value))
        receipt_bytes = json.dumps(receipt_value, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (stage / "PUBLICATION_RECEIPT.json").write_bytes(receipt_bytes)
        target_files["PUBLICATION_RECEIPT.json"] = {
            "bytes": len(receipt_bytes),
            "sha256": digest(receipt_bytes),
        }

        if output.exists():
            output.rmdir()
        os.replace(stage, output)
    return receipt_value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        value = build(args.source_sha, args.output)
    except (PublicationError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)[:500]}, sort_keys=True))
        return 2
    print(json.dumps({
        "status": "PASS",
        "state": value["state"],
        "source_sha": value["source_sha"],
        "target": value["target"]["repository"],
        "receipt": value["package_receipt_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
