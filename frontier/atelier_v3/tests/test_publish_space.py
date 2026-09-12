# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
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


def write_receipt(package: Path, receipt: dict) -> None:
    receipt.pop("package_receipt_sha256", None)
    receipt["package_receipt_sha256"] = publish_space.sha256(publish_space.canonical_bytes(receipt))
    (package / "PUBLICATION_RECEIPT.json").write_text(json.dumps(receipt), encoding="utf-8")


@pytest.mark.parametrize("rehashed", [False, True])
def test_package_rejects_payload_tampering_even_with_rehashed_receipt(tmp_path: Path, rehashed: bool) -> None:
    package = build_exact(tmp_path)
    data = (package / "app.py").read_bytes() + b"\n# modified after qualification\n"
    (package / "app.py").write_bytes(data)
    if rehashed:
        receipt = json.loads((package / "PUBLICATION_RECEIPT.json").read_text())
        measurement = {"bytes": len(data), "sha256": publish_space.sha256(data)}
        receipt["target_files"]["app.py"] = measurement
        receipt["source_files"]["app.py"] = measurement
        write_receipt(package, receipt)
    with pytest.raises(publish_space.PublishError, match="canonical source projection"):
        publish_space.validate_package(package, "a" * 40)


@pytest.mark.parametrize("field,value", [
    ("source_sha", "b" * 40),
    ("source_repository", "other/repository"),
    ("target", {"repository": "SZLHOLDINGS/other"}),
    ("state", "EXACT_READBACK_VERIFIED"),
    ("hub_commit", "b" * 40),
    ("runtime_ready", True),
    ("exact_readback_verified", True),
    ("secrets_recorded", 0),
    ("canonical_writer", "other.yml"),
    ("target_files", {}),
])
def test_package_rejects_rehashed_false_receipt_claims(tmp_path: Path, field: str, value) -> None:
    package = build_exact(tmp_path)
    receipt = json.loads((package / "PUBLICATION_RECEIPT.json").read_text())
    receipt[field] = value
    write_receipt(package, receipt)
    with pytest.raises(publish_space.PublishError, match="canonical preparation evidence"):
        publish_space.validate_package(package, "a" * 40)


@pytest.mark.parametrize("raw", ["{}", "[]", "not-json", '{"schema":1,"schema":2}'])
def test_package_rejects_invalid_receipt(tmp_path: Path, raw: str) -> None:
    package = build_exact(tmp_path)
    (package / "PUBLICATION_RECEIPT.json").write_text(raw, encoding="utf-8")
    with pytest.raises(publish_space.PublishError, match="receipt"):
        publish_space.validate_package(package, "a" * 40)


def test_package_root_symlink_is_rejected_before_resolution(tmp_path: Path) -> None:
    package = build_exact(tmp_path)
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(package, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks unavailable")
    with pytest.raises(publish_space.PublishError, match="symlink"):
        publish_space.validate_package(alias, "a" * 40)


SOURCE = "a" * 40
HUB = "b" * 40


def provider_info(*, head=HUB, running=HUB, stage="RUNNING", sdk_object=False):
    raw = {"stage": stage, "sha": running}
    runtime = SimpleNamespace(stage=stage, raw=raw) if sdk_object else raw
    return SimpleNamespace(sha=head, runtime=runtime, subdomain="szlholdings-szl-atelier")


def short_runtime_window(monkeypatch) -> None:
    ticks = iter([0, 1, 61])
    monkeypatch.setattr(publish_space.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(publish_space.time, "sleep", lambda seconds: None)


def runtime_api(monkeypatch, infos, *, source=SOURCE):
    records = []
    queue = iter(infos)
    def space_info(*args, **kwargs):
        records.append((args, kwargs))
        return next(queue)
    def read_json(url):
        if url.endswith("/healthz"):
            return {"status": "ok"}
        if url.endswith("/readyz"):
            return {"status": "READY"}
        return {"source": {"state": "MEASURED", "revision": source}}
    monkeypatch.setattr(publish_space, "read_json", read_json)
    return SimpleNamespace(space_info=space_info), records


@pytest.mark.parametrize("sdk_object", [False, True])
def test_runtime_verifies_both_provider_observations_and_running_commit(monkeypatch, sdk_object) -> None:
    info = provider_info(sdk_object=sdk_object)
    api, records = runtime_api(monkeypatch, [info, info])
    result = publish_space.wait_for_runtime(api, SOURCE, 60, hub_sha=HUB)
    assert result["state"] == "EXACT_RUNTIME_READBACK_VERIFIED"
    assert result["runtime_sha"] == result["hub_sha"] == HUB
    assert len(records) == 2
    assert all("token" not in kwargs for _, kwargs in records)


@pytest.mark.parametrize("head", [None, "", "c" * 40])
def test_runtime_rejects_head_drift_without_retry(monkeypatch, head) -> None:
    api, _ = runtime_api(monkeypatch, [provider_info(head=head)])
    monkeypatch.setattr(publish_space.time, "sleep", lambda _: pytest.fail("head drift must not retry"))
    with pytest.raises(publish_space.ProviderRevisionError, match="uploaded Hub commit"):
        publish_space.wait_for_runtime(api, SOURCE, 60, hub_sha=HUB)


@pytest.mark.parametrize("running", [None, "", "c" * 40, "B" * 40])
def test_runtime_never_accepts_absent_or_stale_running_commit(monkeypatch, running) -> None:
    short_runtime_window(monkeypatch)
    api, _ = runtime_api(monkeypatch, [provider_info(running=running)])
    monkeypatch.setattr(publish_space, "read_json", lambda _: pytest.fail("unbound runtime must not be probed"))
    with pytest.raises(publish_space.PublishError, match="running revision"):
        publish_space.wait_for_runtime(api, SOURCE, 60, hub_sha=HUB)


def test_runtime_rejects_head_change_during_http_probes(monkeypatch) -> None:
    api, _ = runtime_api(monkeypatch, [provider_info(), provider_info(head="c" * 40)])
    with pytest.raises(publish_space.ProviderRevisionError):
        publish_space.wait_for_runtime(api, SOURCE, 60, hub_sha=HUB)


def test_runtime_rejects_running_commit_change_during_http_probes(monkeypatch) -> None:
    short_runtime_window(monkeypatch)
    api, _ = runtime_api(monkeypatch, [provider_info(), provider_info(running="c" * 40)])
    with pytest.raises(publish_space.PublishError, match="changed during"):
        publish_space.wait_for_runtime(api, SOURCE, 60, hub_sha=HUB)


def test_runtime_rejects_wrong_application_source(monkeypatch) -> None:
    short_runtime_window(monkeypatch)
    api, _ = runtime_api(monkeypatch, [provider_info()], source="c" * 40)
    with pytest.raises(publish_space.PublishError, match="approved GitHub source"):
        publish_space.wait_for_runtime(api, SOURCE, 60, hub_sha=HUB)


def test_invalid_package_is_rejected_before_provider_calls(monkeypatch, tmp_path: Path) -> None:
    package = build_exact(tmp_path)
    (package / "PUBLICATION_RECEIPT.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("HF_TOKEN", "hf_" + "x" * 20)
    monkeypatch.setattr(publish_space, "HfApi", lambda **_: pytest.fail("invalid package reached provider"))
    with pytest.raises(publish_space.PublishError, match="receipt"):
        publish_space.publish(SOURCE, package, tmp_path / "report.json", 60)


def test_receipt_swap_after_inventory_is_rejected_before_provider_calls(monkeypatch, tmp_path: Path) -> None:
    package = build_exact(tmp_path)
    receipt_path = package / "PUBLICATION_RECEIPT.json"
    canonical_receipt = receipt_path.read_bytes()
    original_read = Path.read_bytes
    receipt_reads = []
    def swapped_read(path):
        if path == receipt_path:
            receipt_reads.append(path)
            return b"{}" if len(receipt_reads) == 1 else canonical_receipt
        return original_read(path)
    monkeypatch.setattr(Path, "read_bytes", swapped_read)
    monkeypatch.setenv("HF_TOKEN", "hf_" + "x" * 20)
    monkeypatch.setattr(publish_space, "HfApi", lambda **_: pytest.fail("swapped receipt reached provider"))
    with pytest.raises(publish_space.PublishError, match="changed after inventory"):
        publish_space.publish(SOURCE, package, tmp_path / "report.json", 60)
    assert len(receipt_reads) == 2


def test_publish_binds_completion_to_uploaded_commit_and_package(monkeypatch, tmp_path: Path) -> None:
    package = build_exact(tmp_path)
    before = provider_info(head="c" * 40)
    after = provider_info()
    calls = []
    info_calls = iter([before, after])
    def upload(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(oid=HUB)
    api = SimpleNamespace(create_repo=lambda **_: None, space_info=lambda *a, **k: next(info_calls), upload_folder=upload)
    monkeypatch.setenv("HF_TOKEN", "hf_" + "x" * 20)
    monkeypatch.setattr(publish_space, "HfApi", lambda **_: api)
    measured = publish_space.validate_package(package, SOURCE)
    monkeypatch.setattr(publish_space, "verify_remote_bytes", lambda **_: (sorted(measured), measured))
    def wait(api_argument, source, timeout, *, hub_sha):
        assert api_argument is api and source == SOURCE and hub_sha == HUB
        return {"state": "EXACT_RUNTIME_READBACK_VERIFIED", "runtime_sha": HUB}
    monkeypatch.setattr(publish_space, "wait_for_runtime", wait)
    result = publish_space.publish(SOURCE, package, tmp_path / "report.json", 60)
    assert calls[0]["parent_commit"] == "c" * 40
    assert result["hub_content_commit"] == HUB
    assert result["package_receipt_file_sha256"] == measured["PUBLICATION_RECEIPT.json"]["sha256"]
    assert json.loads((tmp_path / "report.json").read_text()) == result
