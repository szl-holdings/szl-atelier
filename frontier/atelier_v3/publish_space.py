#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Publish one exact Atelier package and prove provider/runtime convergence.

This is the only provider-mutating program in Atelier v3. It is intentionally
narrow: one source repository, one Docker Space target, one package directory,
and one secret-free report. It never prints or serializes the token.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any, Final

from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.errors import HfHubHTTPError

from build_publication import HERE as SOURCE_ROOT, duplicate_guard, load_contract

TARGET: Final = "SZLHOLDINGS/szl-atelier"
REPO_TYPE: Final = "space"
SOURCE_RE = re.compile(r"^[0-9a-f]{40}$")
TOKEN_RE = re.compile(r"(?:github_pat_|gh[pousr]_|hf_)[A-Za-z0-9_]{12,}")
MAX_REPORT_BYTES: Final = 1_000_000
MAX_HTTP_BYTES: Final = 512_000
EXPECTED_CORE: Final = {
    "README.md",
    "Dockerfile",
    "requirements.txt",
    "run.py",
    "app.py",
    "catalog.py",
    "static/index.html",
    "static/app.js",
    "static/styles.css",
    "SOURCE_REVISION",
    "PUBLICATION_RECEIPT.json",
}
ALLOWED_PROVIDER_EXTRAS: Final = {".gitattributes"}


class PublishError(RuntimeError):
    """The release cannot be completed without weakening its proof boundary."""


class ProviderRevisionError(PublishError):
    """The provider head changed after the upload was observed."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise urllib.error.HTTPError(req.full_url, code, "redirect rejected", headers, fp)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_write(path: Path, value: dict[str, Any]) -> None:
    raw = json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if len(raw) > MAX_REPORT_BYTES:
        raise PublishError("publication report exceeded byte limit")
    if TOKEN_RE.search(raw.decode("utf-8", "replace")):
        raise PublishError("credential-shaped material reached publication report")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def validate_package(package: Path, source_sha: str) -> dict[str, dict[str, Any]]:
    if package.is_symlink():
        raise PublishError("publication package is unavailable or symlinked")
    if not SOURCE_RE.fullmatch(source_sha):
        raise PublishError("source SHA must be exact lowercase 40-character hex")
    package = package.resolve()
    if not package.is_dir() or package.is_symlink():
        raise PublishError("publication package is unavailable or symlinked")
    observed: set[str] = set()
    files: dict[str, dict[str, Any]] = {}
    for path in sorted(package.rglob("*")):
        if path.is_symlink():
            raise PublishError(f"symlink is forbidden in package: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(package).as_posix()
        posix = PurePosixPath(relative)
        if posix.is_absolute() or any(part in {"", ".", ".."} for part in posix.parts):
            raise PublishError(f"unsafe package path: {relative}")
        data = path.read_bytes()
        if TOKEN_RE.search(data.decode("utf-8", "replace")):
            raise PublishError(f"credential-shaped material in package: {relative}")
        observed.add(relative)
        files[relative] = {"bytes": len(data), "sha256": sha256(data)}
    if observed != EXPECTED_CORE:
        raise PublishError(
            f"package file set drifted: missing={sorted(EXPECTED_CORE-observed)} "
            f"unexpected={sorted(observed-EXPECTED_CORE)}"
        )
    source_value = (package / "SOURCE_REVISION").read_text(encoding="ascii").strip()
    if source_value != source_sha:
        raise PublishError("SOURCE_REVISION does not match requested source SHA")
    validate_package_receipt(package, source_sha, files)
    return files


def validate_package_receipt(
    package: Path, source_sha: str, files: dict[str, dict[str, Any]]
) -> None:
    """Compare the preparation receipt and package to this qualified checkout."""
    try:
        raw = (package / "PUBLICATION_RECEIPT.json").read_bytes()
        if len(raw) > MAX_REPORT_BYTES:
            raise PublishError("package receipt exceeded byte limit")
        if {"bytes": len(raw), "sha256": sha256(raw)} != files.get("PUBLICATION_RECEIPT.json"):
            raise PublishError("package receipt changed after inventory")
        receipt = json.loads(raw.decode("utf-8"), object_pairs_hook=duplicate_guard)
        contract = load_contract()
    except (OSError, ValueError, UnicodeError) as exc:
        raise PublishError("package receipt or publication contract is invalid") from exc
    source_files: dict[str, dict[str, Any]] = {}
    target_files: dict[str, dict[str, Any]] = {}
    for row in contract["mapping"]:
        source = SOURCE_ROOT / row["source"]
        if source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(SOURCE_ROOT):
            raise PublishError("canonical source file is unavailable or outside the source root")
        data = source.read_bytes()
        measurement = {"bytes": len(data), "sha256": sha256(data)}
        source_files[row["source"]] = measurement
        target_files[row["target"]] = measurement
    revision_bytes = (source_sha + "\n").encode("ascii")
    target_files["SOURCE_REVISION"] = {
        "bytes": len(revision_bytes), "sha256": sha256(revision_bytes)
    }
    measured_payload = {name: value for name, value in files.items() if name != "PUBLICATION_RECEIPT.json"}
    if measured_payload != target_files:
        raise PublishError("package bytes do not match the canonical source projection")
    expected = {
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
    expected["package_receipt_sha256"] = sha256(canonical_bytes(expected))
    if canonical_bytes(receipt) != canonical_bytes(expected):
        raise PublishError("package receipt does not match the canonical preparation evidence")


def runtime_stage(info: Any) -> str:
    runtime = getattr(info, "runtime", None)
    if isinstance(runtime, dict):
        return str(runtime.get("stage") or "UNAVAILABLE")
    return str(getattr(runtime, "stage", None) or "UNAVAILABLE")


def runtime_revision(info: Any) -> str | None:
    runtime = getattr(info, "runtime", None)
    raw = runtime if isinstance(runtime, dict) else getattr(runtime, "raw", None)
    value = raw.get("sha") if isinstance(raw, dict) else None
    return value if isinstance(value, str) and SOURCE_RE.fullmatch(value) else None


def require_provider_revision(info: Any, hub_sha: str) -> None:
    if getattr(info, "sha", None) != hub_sha:
        raise ProviderRevisionError("provider head does not match the uploaded Hub commit")


def public_base_url(info: Any) -> str:
    subdomain = getattr(info, "subdomain", None)
    if isinstance(subdomain, str) and re.fullmatch(r"[a-z0-9-]{1,128}", subdomain):
        return f"https://{subdomain}.hf.space"
    return "https://szlholdings-szl-atelier.hf.space"


def read_json(url: str) -> dict[str, Any]:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".hf.space"):
        raise PublishError("runtime URL left the exact hf.space origin family")
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "szl-atelier-publisher/1.0"},
    )
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(request, timeout=8.0) as response:
        final = urllib.parse.urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname != parsed.hostname:
            raise PublishError("runtime origin changed")
        body = response.read(MAX_HTTP_BYTES + 1)
        if len(body) > MAX_HTTP_BYTES:
            raise PublishError("runtime response exceeded byte limit")
        value = json.loads(body.decode("utf-8"))
        if not isinstance(value, dict):
            raise PublishError("runtime response was not a JSON object")
        return value


def verify_remote_bytes(
    *, token: str, hub_sha: str, local_files: dict[str, dict[str, Any]], api: HfApi
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    remote_files = set(api.list_repo_files(TARGET, repo_type=REPO_TYPE, revision=hub_sha, token=token))
    missing = EXPECTED_CORE - remote_files
    unexpected = remote_files - EXPECTED_CORE - ALLOWED_PROVIDER_EXTRAS
    if missing or unexpected:
        raise PublishError(
            f"remote file set drifted: missing={sorted(missing)} unexpected={sorted(unexpected)}"
        )
    measured: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="atelier-hf-readback-") as cache:
        for relative in sorted(EXPECTED_CORE):
            downloaded = Path(
                hf_hub_download(
                    repo_id=TARGET,
                    filename=relative,
                    repo_type=REPO_TYPE,
                    revision=hub_sha,
                    token=token,
                    cache_dir=cache,
                    force_download=True,
                )
            )
            data = downloaded.read_bytes()
            digest = sha256(data)
            expected = local_files[relative]
            if len(data) != expected["bytes"] or digest != expected["sha256"]:
                raise PublishError(f"remote byte mismatch: {relative}")
            measured[relative] = {"bytes": len(data), "sha256": digest}
    return sorted(remote_files), measured


def wait_for_runtime(
    api: HfApi, source_sha: str, timeout_seconds: int, *, hub_sha: str
) -> dict[str, Any]:
    if not SOURCE_RE.fullmatch(source_sha) or not SOURCE_RE.fullmatch(hub_sha):
        raise PublishError("runtime verification requires exact source and Hub commits")
    deadline = time.monotonic() + timeout_seconds
    observations: list[dict[str, Any]] = []
    last_error = "runtime not observed"
    while time.monotonic() < deadline:
        try:
            info = api.space_info(
                TARGET,
                expand=["sha", "runtime", "sdk", "subdomain"],
            )
            require_provider_revision(info, hub_sha)
            stage = runtime_stage(info)
            running_sha = runtime_revision(info)
            base_url = public_base_url(info)
            observation = {
                "at_unix": int(time.time()),
                "hub_sha": getattr(info, "sha", None),
                "runtime_sha": running_sha,
                "runtime_stage": stage,
                "base_url": base_url,
            }
            observations.append(observation)
            observations = observations[-40:]
            if stage == "RUNNING":
                if running_sha != hub_sha:
                    raise PublishError("running revision is unavailable or does not match the uploaded Hub commit")
                health = read_json(base_url + "/healthz")
                readiness = read_json(base_url + "/readyz")
                source = read_json(base_url + "/api/source")
                if health.get("status") != "ok":
                    raise PublishError("runtime health contract failed")
                if readiness.get("status") != "READY":
                    raise PublishError("runtime readiness contract failed")
                source_value = source.get("source") if isinstance(source.get("source"), dict) else {}
                if source_value.get("state") != "MEASURED" or source_value.get("revision") != source_sha:
                    raise PublishError("runtime source revision does not match approved GitHub source")
                final_info = api.space_info(
                    TARGET, expand=["sha", "runtime", "sdk", "subdomain"]
                )
                require_provider_revision(final_info, hub_sha)
                if runtime_stage(final_info) != "RUNNING" or runtime_revision(final_info) != hub_sha:
                    raise PublishError("running revision changed during application readback")
                return {
                    "state": "EXACT_RUNTIME_READBACK_VERIFIED",
                    "runtime_stage": stage,
                    "hub_sha": hub_sha,
                    "runtime_sha": running_sha,
                    "base_url": base_url,
                    "health": health,
                    "readiness": readiness,
                    "source": source,
                    "observations": observations,
                }
            last_error = f"runtime stage {stage}"
        except ProviderRevisionError:
            raise
        except (HfHubHTTPError, OSError, urllib.error.URLError, json.JSONDecodeError, PublishError) as exc:
            last_error = f"{type(exc).__name__}: {str(exc)[:240]}"
        time.sleep(15)
    raise PublishError(f"runtime readback timed out: {last_error}")


def publish(source_sha: str, package: Path, report_path: Path, timeout_seconds: int) -> dict[str, Any]:
    if not SOURCE_RE.fullmatch(source_sha):
        raise PublishError("source SHA must be exact lowercase 40-character hex")
    token = os.getenv("HF_TOKEN", "")
    if not token:
        raise PublishError("HF_TOKEN is unavailable; no provider mutation attempted")
    if not (token.startswith("hf_") and len(token) >= 20):
        raise PublishError("HF_TOKEN does not match the required credential shape")

    local_files = validate_package(package, source_sha)
    api = HfApi(token=token)
    api.create_repo(
        repo_id=TARGET,
        repo_type=REPO_TYPE,
        space_sdk="docker",
        private=False,
        exist_ok=True,
        token=token,
    )
    before = api.space_info(TARGET, token=token, expand=["sha", "runtime", "sdk", "subdomain"])
    parent = getattr(before, "sha", None)
    if not isinstance(parent, str) or not SOURCE_RE.fullmatch(parent):
        raise PublishError("exact provider parent is unavailable; no upload attempted")
    commit = api.upload_folder(
        repo_id=TARGET,
        repo_type=REPO_TYPE,
        folder_path=str(package.resolve()),
        revision="main",
        parent_commit=parent,
        delete_patterns=["*"],
        commit_message=f"Deploy SZL Atelier v3 from GitHub {source_sha}",
        commit_description="Source-bound package generated by frontier/atelier_v3/build_publication.py",
        token=token,
    )
    content_commit = (
        getattr(commit, "oid", None)
        or getattr(commit, "commit_id", None)
        or getattr(commit, "commit_oid", None)
    )
    if not isinstance(content_commit, str) or not SOURCE_RE.fullmatch(content_commit):
        raise PublishError("upload did not return an exact Hub commit")
    after = api.space_info(TARGET, token=token, expand=["sha", "runtime", "sdk", "subdomain"])
    hub_sha = str(getattr(after, "sha", None) or "")
    if not SOURCE_RE.fullmatch(hub_sha):
        raise PublishError("Hub commit readback is unavailable")
    if content_commit != hub_sha:
        raise PublishError(f"upload commit {content_commit} does not match Hub head {hub_sha}")

    remote_files, measured_files = verify_remote_bytes(
        token=token,
        hub_sha=hub_sha,
        local_files=local_files,
        api=api,
    )
    runtime = wait_for_runtime(api, source_sha, timeout_seconds, hub_sha=hub_sha)
    result = {
        "schema": "szl.atelier-provider-readback/v1",
        "state": "EXACT_READBACK_VERIFIED",
        "source_repository": "szl-holdings/szl-atelier",
        "source_sha": source_sha,
        "target": TARGET,
        "hub_content_commit": hub_sha,
        "package_receipt_file_sha256": local_files["PUBLICATION_RECEIPT.json"]["sha256"],
        "remote_files": remote_files,
        "measured_files": measured_files,
        "runtime": runtime,
        "secrets_recorded": False,
    }
    result["receipt_sha256"] = sha256(canonical_bytes(result))
    safe_write(report_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()
    if not 60 <= args.timeout_seconds <= 1_800:
        print(json.dumps({"status": "BLOCKED", "error": "timeout must be between 60 and 1800 seconds"}))
        return 2
    try:
        value = publish(args.source_sha, args.package, args.report, args.timeout_seconds)
    except Exception as exc:  # fail closed while preserving a secret-free terminal receipt
        failure = {
            "schema": "szl.atelier-provider-readback/v1",
            "state": "BLOCKED",
            "source_sha": args.source_sha if SOURCE_RE.fullmatch(args.source_sha) else "INVALID",
            "target": TARGET,
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
            "secrets_recorded": False,
        }
        failure["receipt_sha256"] = sha256(canonical_bytes(failure))
        try:
            safe_write(args.report, failure)
        except Exception:
            pass
        print(json.dumps({"status": "BLOCKED", "error_type": type(exc).__name__}, sort_keys=True))
        return 2
    print(json.dumps({
        "status": "PASS",
        "state": value["state"],
        "source_sha": value["source_sha"],
        "hub_content_commit": value["hub_content_commit"],
        "receipt_sha256": value["receipt_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
