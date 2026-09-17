# SPDX-License-Identifier: Apache-2.0
"""Exercise real publisher/SDK byte operations with synthetic source and no network."""
from __future__ import annotations

import json
import os
import shutil
import socket
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from huggingface_hub import CommitOperationAdd, CommitOperationDelete

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_publication as builder  # noqa: E402
import publish_space as publisher  # noqa: E402

SOURCE = "a" * 40
PARENT = "b" * 40
HUB = "c" * 40


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail("offline publication test attempted a network connection")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)


@pytest.fixture
def package(tmp_path, monkeypatch):
    """Run the actual builder/receipt validator against an explicit tiny fixture."""
    source = tmp_path / "qualified-source"
    mapping = [
        {"source": name, "target": name}
        for name in sorted(publisher.EXPECTED_CORE - {"SOURCE_REVISION", "PUBLICATION_RECEIPT.json"})
    ]
    contract = {
        "schema": "szl.hf-publication-contract/v1",
        "source_repository": "szl-holdings/szl-atelier",
        "canonical_writer": ".github/workflows/hf-space.yml",
        "target": {"repository": publisher.TARGET, "type": "space", "sdk": "docker"},
        "mapping": mapping,
    }
    for row in mapping:
        path = source / row["source"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(("synthetic qualified bytes: " + row["source"] + "\n").encode())
    contract_path = source / "PUBLICATION.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    real_load = builder.load_contract
    monkeypatch.setattr(builder, "HERE", source)
    monkeypatch.setattr(builder, "load_contract", lambda: real_load(contract_path))
    monkeypatch.setattr(publisher, "SOURCE_ROOT", source)
    monkeypatch.setattr(publisher, "load_contract", lambda: real_load(contract_path))
    target = tmp_path / "package"
    builder.build(SOURCE, target)
    return target


class RecordingProvider:
    """No transport; retain the old method solely for predecessor regression runs."""
    def __init__(self, package, callback=lambda stage: None):
        self.package = package
        self.callback = callback
        self.calls = []
        self.uploaded = {}
        self.operations = ()

    def create_repo(self, **kwargs):
        self.calls.append(("create_repo", kwargs))
        self.callback("create_repo")

    def space_info(self, *args, **kwargs):
        self.calls.append(("space_info", kwargs))
        self.callback("space_info")
        return SimpleNamespace(sha=HUB if self.uploaded else PARENT)

    def list_repo_files(self, *args, **kwargs):
        self.calls.append(("list_repo_files", kwargs))
        self.callback("list_repo_files")
        return ["old/app.js", ".gitattributes", *sorted(publisher.EXPECTED_CORE)]

    def create_commit(self, **kwargs):
        self.calls.append(("create_commit", kwargs))
        self.callback("create_commit")
        self.operations = kwargs["operations"]
        for operation in self.operations:
            if isinstance(operation, CommitOperationAdd):
                assert type(operation.path_or_fileobj) is bytes
                with operation.as_file() as stream:
                    self.uploaded[operation.path_in_repo] = stream.read()
        return SimpleNamespace(oid=HUB)

    def upload_folder(self, **kwargs):
        self.calls.append(("upload_folder", kwargs))
        self.uploaded = {
            p.relative_to(self.package).as_posix(): p.read_bytes()
            for p in self.package.rglob("*") if p.is_file()
        }
        return SimpleNamespace(oid=HUB)


def configure(monkeypatch, package, callback=lambda stage: None):
    api = RecordingProvider(package, callback)
    monkeypatch.setenv("HF_TOKEN", "hf_" + "x" * 20)
    monkeypatch.setattr(publisher, "HfApi", lambda **kwargs: api)
    def verify(**kwargs):
        observed = {name: {"bytes": len(raw), "sha256": publisher.sha256(raw)}
                    for name, raw in api.uploaded.items()}
        if observed != kwargs["local_files"]:
            raise publisher.PublishError("recorded upload differs from validated bytes")
        assert kwargs["hub_sha"] == HUB and kwargs["api"] is api
        return sorted(observed), observed
    monkeypatch.setattr(publisher, "verify_remote_bytes", verify)
    monkeypatch.setattr(publisher, "wait_for_runtime", lambda *args, **kwargs: {
        "state": "EXACT_RUNTIME_READBACK_VERIFIED", "runtime_sha": kwargs["hub_sha"]})
    return api


@pytest.mark.parametrize("relative", ["app.py", "static/app.js", "PUBLICATION_RECEIPT.json", "SOURCE_REVISION"])
def test_mutation_after_validation_blocks_first_provider_call(package, tmp_path, monkeypatch, relative):
    real_validate = publisher.validate_package
    def validate_then_change(path, source):
        measured = real_validate(path, source)
        data = (path / relative).read_bytes()
        (path / relative).write_bytes(b"!" + data[1:])  # Same size is not sufficient.
        return measured
    monkeypatch.setattr(publisher, "validate_package", validate_then_change)
    api = configure(monkeypatch, package)
    with pytest.raises(publisher.PublishError):
        publisher.publish(SOURCE, package, tmp_path / "report.json", 60)
    assert api.calls == []
    assert not (tmp_path / "report.json").exists()


@pytest.mark.parametrize("change", ["remove", "extra", "root-link", "file-link", "directory-link", "fifo"])
def test_file_set_and_type_changes_block_first_provider_call(package, tmp_path, monkeypatch, change):
    real_validate = publisher.validate_package
    def validate_then_change(path, source):
        measured = real_validate(path, source)
        if change == "extra":
            (path / "extra.py").write_bytes(b"unqualified")
        elif change == "root-link":
            moved = path.with_name("producer-moved")
            path.rename(moved)
            path.symlink_to(moved, target_is_directory=True)
        elif change == "directory-link":
            moved = path.with_name("producer-static")
            (path / "static").rename(moved)
            (path / "static").symlink_to(moved, target_is_directory=True)
        else:
            target = path / "app.py"
            target.unlink()
            if change == "file-link":
                target.symlink_to(path / "catalog.py")
            elif change == "fifo":
                if not hasattr(os, "mkfifo"):
                    pytest.skip("OS does not expose FIFO creation")
                os.mkfifo(target)
        return measured
    monkeypatch.setattr(publisher, "validate_package", validate_then_change)
    api = configure(monkeypatch, package)
    with pytest.raises(publisher.PublishError):
        publisher.publish(SOURCE, package, tmp_path / "report.json", 60)
    assert api.calls == []


@pytest.mark.parametrize("stage", ["create_repo", "space_info", "list_repo_files", "create_commit"])
@pytest.mark.parametrize("change", ["payload", "receipt", "extra", "remove"])
def test_late_producer_change_cannot_change_uploaded_bytes(package, tmp_path, monkeypatch, stage, change):
    expected = {name: (package / name).read_bytes() for name in publisher.EXPECTED_CORE}
    did_change = []
    def mutate(current):
        if current != stage or did_change:
            return
        did_change.append(current)
        if change == "remove":
            shutil.rmtree(package)
        elif change == "extra":
            (package / "unqualified.py").write_bytes(b"new producer file")
        else:
            path = package / ("app.py" if change == "payload" else "PUBLICATION_RECEIPT.json")
            path.write_bytes(b"unqualified replacement")
    api = configure(monkeypatch, package, mutate)
    result = publisher.publish(SOURCE, package, tmp_path / "report.json", 60)
    assert did_change == [stage]
    assert api.uploaded == expected
    assert all(name != "upload_folder" for name, _ in api.calls)
    assert sum(name == "create_commit" for name, _ in api.calls) == 1
    assert result["package_receipt_file_sha256"] == publisher.sha256(expected["PUBLICATION_RECEIPT.json"])
    assert json.loads((tmp_path / "report.json").read_text()) == result
    for name, kwargs in api.calls:
        if name == "list_repo_files":
            assert kwargs["revision"] == PARENT
        if name == "create_commit":
            assert kwargs["parent_commit"] == PARENT
            assert kwargs["repo_id"] == publisher.TARGET and kwargs["repo_type"] == "space"
            assert kwargs["revision"] == "main"
    deletes = [op.path_in_repo for op in api.operations if isinstance(op, CommitOperationDelete)]
    assert deletes == ["old/app.js"]


def test_frozen_payload_is_bounded_immutable_and_reusable(package):
    measured = publisher.validate_package(package, SOURCE)
    frozen = publisher.freeze_validated_package(package, measured)
    assert type(frozen) is tuple and all(type(item) is tuple and type(item[1]) is bytes for item in frozen)
    for name, raw in frozen:
        operation = CommitOperationAdd(path_in_repo=name, path_or_fileobj=raw)
        for _ in range(2):
            with operation.as_file() as stream:
                assert publisher.sha256(stream.read()) == measured[name]["sha256"]


@pytest.mark.parametrize("size", [True, -1, 1.5, None, "2"])
def test_invalid_size_cannot_reach_file_open(package, monkeypatch, size):
    measured = publisher.validate_package(package, SOURCE)
    measured["app.py"]["bytes"] = size
    monkeypatch.setattr(os, "open", lambda *a, **k: pytest.fail("invalid size reached file open"))
    with pytest.raises(publisher.PublishError, match="measurement"):
        publisher.freeze_validated_package(package, measured)


def test_memory_budget_is_enforced_before_file_open(package, monkeypatch):
    measured = publisher.validate_package(package, SOURCE)
    monkeypatch.setattr(publisher, "MAX_FROZEN_BYTES", 1)
    monkeypatch.setattr(os, "open", lambda *a, **k: pytest.fail("budget overflow reached file open"))
    with pytest.raises(publisher.PublishError, match="byte limit"):
        publisher.freeze_validated_package(package, measured)


def test_capture_detects_growth_without_reading_unbounded_bytes(package, monkeypatch):
    measured = publisher.validate_package(package, SOURCE)
    real_open = os.open
    observed_reads = []
    real_fdopen = os.fdopen
    class ObservedFile:
        def __init__(self, fd, mode):
            self.file = real_fdopen(fd, mode)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.file.close()
        def fileno(self):
            return self.file.fileno()
        def read(self, count):
            observed_reads.append(count)
            return self.file.read(count)
    def growing_open(path, flags):
        if Path(path).name == "app.py":
            Path(path).write_bytes(b"x" * 100_000)
        return real_open(path, flags)
    monkeypatch.setattr(os, "open", growing_open)
    monkeypatch.setattr(os, "fdopen", ObservedFile)
    with pytest.raises(publisher.PublishError, match="changed after validation"):
        publisher.freeze_validated_package(package, measured)
    assert observed_reads and max(observed_reads) <= max(v["bytes"] for v in measured.values()) + 1


@pytest.mark.parametrize("names", [None, "old.py", ["../escape"], ["/absolute"], ["a//b"],
                                  ["a/./b"], ["a\\b"], ["x\x00y"], [True], ["dup", "dup"]])
def test_invalid_remote_inventory_never_creates_deletions(names):
    api = SimpleNamespace(list_repo_files=lambda *a, **k: names)
    with pytest.raises(publisher.PublishError, match="remote file inventory"):
        publisher.remote_deletions(api, parent=PARENT, token="offline")


def test_remote_deletion_inventory_bound(monkeypatch):
    monkeypatch.setattr(publisher, "MAX_REMOTE_FILES", 1)
    api = SimpleNamespace(list_repo_files=lambda *a, **k: ["one", "two"])
    with pytest.raises(publisher.PublishError, match="outside bounds"):
        publisher.remote_deletions(api, parent=PARENT, token="offline")


def test_uncertain_content_commit_is_not_retried_or_certified(package, tmp_path, monkeypatch):
    api = configure(monkeypatch, package)
    attempted = []
    def uncertain(**kwargs):
        attempted.append(kwargs)
        raise ConnectionError("offline uncertain-response fixture")
    api.create_commit = uncertain
    with pytest.raises(ConnectionError):
        publisher.publish(SOURCE, package, tmp_path / "report.json", 60)
    assert len(attempted) == 1
    assert not (tmp_path / "report.json").exists()


def test_qualification_guard_tracks_real_frozen_byte_controls():
    import ast
    import textwrap
    workflow = (ROOT.parents[1] / ".github/workflows/atelier-v3.yml").read_text()
    snippet = workflow.split("          required_publisher = (", 1)[1].split("          required_workflow = (", 1)[0]
    tree = ast.parse(textwrap.dedent("          required_publisher = (" + snippet))
    required = ast.literal_eval(tree.body[0].value)
    source = (ROOT / "publish_space.py").read_text()
    assert all(control in source for control in required)
    for control in ("freeze_validated_package(package, local_files)", "path_or_fileobj=data",
                    "parent_commit=parent", "observed - EXPECTED_CORE - ALLOWED_PROVIDER_EXTRAS"):
        assert control in required
        mutated = source.replace(control, "REMOVED_CONTROL")
        assert any(item not in mutated for item in required)
    assert "'api.upload_folder('" in snippet
