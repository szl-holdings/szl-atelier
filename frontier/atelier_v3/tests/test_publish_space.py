# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_publication  # noqa: E402
import publish_space  # noqa: E402


def build_exact(tmp_path: Path, source_sha: str = "a" * 40) -> Path:
    package = tmp_path / "package"
    build_publication.build(source_sha, package)
    return package


def test_validate_package_accepts_only_exact_projection(tmp_path: Path) -> None:
    package = build_exact(tmp_path)
    measured = publish_space.validate_package(package, "a" * 40)
    assert set(measured) == publish_space.EXPECTED_CORE
    assert all(value["bytes"] >= 0 and len(value["sha256"]) == 64 for value in measured.values())


def test_validate_package_rejects_missing_and_unexpected_files(tmp_path: Path) -> None:
    package = build_exact(tmp_path)
    (package / "app.py").unlink()
    with pytest.raises(publish_space.PublishError, match="package file set drifted"):
        publish_space.validate_package(package, "a" * 40)

    package = build_exact(tmp_path / "second")
    (package / "unexpected.txt").write_text("not admitted", encoding="utf-8")
    with pytest.raises(publish_space.PublishError, match="package file set drifted"):
        publish_space.validate_package(package, "a" * 40)


def test_validate_package_rejects_source_mismatch_and_symlink(tmp_path: Path) -> None:
    package = build_exact(tmp_path)
    with pytest.raises(publish_space.PublishError, match="SOURCE_REVISION"):
        publish_space.validate_package(package, "b" * 40)

    package = build_exact(tmp_path / "linked")
    target = package / "catalog.py"
    target.unlink()
    try:
        target.symlink_to(package / "app.py")
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(publish_space.PublishError, match="symlink"):
        publish_space.validate_package(package, "a" * 40)


def test_publish_requires_exact_nonserialized_token(monkeypatch, tmp_path: Path) -> None:
    package = build_exact(tmp_path)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(publish_space.PublishError, match="HF_TOKEN is unavailable"):
        publish_space.publish("a" * 40, package, tmp_path / "report.json", 60)
    assert not (tmp_path / "report.json").exists()

    monkeypatch.setenv("HF_TOKEN", "wrong")
    with pytest.raises(publish_space.PublishError, match="credential shape"):
        publish_space.publish("a" * 40, package, tmp_path / "report.json", 60)


def test_runtime_identity_helpers_are_bounded() -> None:
    info = SimpleNamespace(subdomain="szlholdings-szl-atelier", runtime={"stage": "RUNNING"})
    assert publish_space.runtime_stage(info) == "RUNNING"
    assert publish_space.public_base_url(info) == "https://szlholdings-szl-atelier.hf.space"

    malformed = SimpleNamespace(subdomain="https://evil.test", runtime=None)
    assert publish_space.runtime_stage(malformed) == "UNAVAILABLE"
    assert publish_space.public_base_url(malformed) == "https://szlholdings-szl-atelier.hf.space"


def test_read_json_rejects_non_hf_space_origin() -> None:
    with pytest.raises(publish_space.PublishError, match="origin family"):
        publish_space.read_json("https://example.com/healthz")


def test_safe_write_rejects_credential_shaped_material(tmp_path: Path) -> None:
    with pytest.raises(publish_space.PublishError, match="credential-shaped"):
        publish_space.safe_write(tmp_path / "report.json", {"value": "hf_" + "a" * 40})
