# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_publication_contract_has_one_exact_space_target() -> None:
    value = json.loads((ROOT / "PUBLICATION.json").read_text(encoding="utf-8"))
    assert value["schema"] == "szl.hf-publication-contract/v1"
    assert value["source_repository"] == "szl-holdings/szl-atelier"
    assert value["source_ref_required"] == "main"
    assert value["target"] == {
        "type": "space",
        "repository": "SZLHOLDINGS/szl-atelier",
        "sdk": "docker",
        "app_port": 7860,
    }
    assert value["canonical_writer"] == ".github/workflows/hf-space.yml"
    assert value["confirmation"] == "PUBLISH-SZL-ATELIER-V3"
    targets = [row["target"] for row in value["mapping"]]
    assert len(targets) == len(set(targets))
    assert targets == [
        "README.md",
        "Dockerfile",
        "requirements.txt",
        "run.py",
        "app.py",
        "catalog.py",
        "static/index.html",
        "static/app.js",
        "static/styles.css",
    ]
    for row in value["mapping"]:
        assert (ROOT / row["source"]).is_file()
    assert value["mutation_boundary"] == {
        "github_source_write": False,
        "repository_settings_write": False,
        "space_target_write_only": True,
        "other_hub_repositories_write": False,
        "secrets_recorded": False,
    }


def test_space_readme_front_matter_is_docker_only() -> None:
    text = (ROOT / "SPACE_README.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "sdk: docker" in text
    assert "app_port: 7860" in text
    assert "license: apache-2.0" in text
    assert "sdk: gradio" not in text
    assert "sdk: static" not in text


def test_runtime_launcher_binds_only_exact_source_sha(monkeypatch, tmp_path: Path) -> None:
    module_path = ROOT / "run.py"
    spec = importlib.util.spec_from_file_location("atelier_run", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    source_file = tmp_path / "SOURCE_REVISION"
    monkeypatch.setattr(module, "SOURCE_FILE", source_file)
    monkeypatch.delenv("SOURCE_REVISION", raising=False)

    source_file.write_text("not-a-sha\n", encoding="utf-8")
    module.bind_source_revision()
    assert "SOURCE_REVISION" not in os.environ

    source_file.write_text("D" * 40 + "\n", encoding="utf-8")
    module.bind_source_revision()
    assert "SOURCE_REVISION" not in os.environ

    source_file.write_text("d" * 40 + "\n", encoding="utf-8")
    module.bind_source_revision()
    assert os.environ["SOURCE_REVISION"] == "d" * 40


def test_runtime_launcher_does_not_override_operator_identity(monkeypatch, tmp_path: Path) -> None:
    module_path = ROOT / "run.py"
    spec = importlib.util.spec_from_file_location("atelier_run_existing", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    source_file = tmp_path / "SOURCE_REVISION"
    source_file.write_text("e" * 40 + "\n", encoding="utf-8")
    monkeypatch.setattr(module, "SOURCE_FILE", source_file)
    monkeypatch.setenv("SOURCE_REVISION", "f" * 40)
    module.bind_source_revision()
    assert os.environ["SOURCE_REVISION"] == "f" * 40
