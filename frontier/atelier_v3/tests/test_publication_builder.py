# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "build_publication.py"
SPEC = importlib.util.spec_from_file_location("atelier_publication_builder", MODULE_PATH)
assert SPEC and SPEC.loader
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


def test_build_is_deterministic_and_source_bound(tmp_path: Path) -> None:
    sha = "a" * 40
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first = BUILDER.build(sha, first_dir)
    second = BUILDER.build(sha, second_dir)
    assert first == second
    assert first["state"] == "PACKAGE_BUILT_NOT_PUBLISHED"
    assert first["source_sha"] == sha
    assert first["target"]["repository"] == "SZLHOLDINGS/szl-atelier"
    assert first["hub_commit"] == "UNAVAILABLE_NOT_PUBLISHED"
    assert first["runtime_ready"] == "UNAVAILABLE_NOT_PUBLISHED"
    assert first["exact_readback_verified"] is False
    assert first["secrets_recorded"] is False
    assert (first_dir / "SOURCE_REVISION").read_text(encoding="utf-8") == sha + "\n"
    assert (first_dir / "Dockerfile").read_text(encoding="utf-8") == (ROOT / "SPACE_DOCKERFILE").read_text(encoding="utf-8")
    assert (first_dir / "README.md").read_text(encoding="utf-8") == (ROOT / "SPACE_README.md").read_text(encoding="utf-8")
    assert sorted(path.relative_to(first_dir).as_posix() for path in first_dir.rglob("*") if path.is_file()) == sorted(
        [row["target"] for row in json.loads((ROOT / "PUBLICATION.json").read_text())["mapping"]]
        + ["SOURCE_REVISION", "PUBLICATION_RECEIPT.json"]
    )
    for relative in [path.relative_to(first_dir) for path in first_dir.rglob("*") if path.is_file()]:
        assert (first_dir / relative).read_bytes() == (second_dir / relative).read_bytes()


def test_receipt_hash_commits_the_pre_receipt_package(tmp_path: Path) -> None:
    output = tmp_path / "package"
    BUILDER.build("b" * 40, output)
    receipt = json.loads((output / "PUBLICATION_RECEIPT.json").read_text(encoding="utf-8"))
    digest = receipt.pop("package_receipt_sha256")
    assert digest == BUILDER.digest(BUILDER.canonical_bytes(receipt))
    assert "PUBLICATION_RECEIPT.json" not in receipt["target_files"]
    for relative, expected in receipt["target_files"].items():
        data = (output / relative).read_bytes()
        assert expected == {"bytes": len(data), "sha256": BUILDER.digest(data)}


def test_builder_rejects_bad_sha_nonempty_output_and_source_overlap(tmp_path: Path) -> None:
    with pytest.raises(BUILDER.PublicationError, match="source SHA"):
        BUILDER.build("A" * 40, tmp_path / "bad")
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "existing").write_text("x", encoding="utf-8")
    with pytest.raises(BUILDER.PublicationError, match="empty"):
        BUILDER.build("c" * 40, occupied)
    with pytest.raises(BUILDER.PublicationError, match="overlap"):
        BUILDER.build("c" * 40, ROOT / "nested-output")


def test_contract_has_unique_safe_paths() -> None:
    contract = BUILDER.load_contract()
    sources = [row["source"] for row in contract["mapping"]]
    targets = [row["target"] for row in contract["mapping"]]
    assert len(sources) == len(set(sources))
    assert len(targets) == len(set(targets))
    for value in sources + targets:
        path = BUILDER.strict_relative(value, label="test")
        assert not path.is_absolute()
        assert ".." not in path.parts
