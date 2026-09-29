# SPDX-License-Identifier: Apache-2.0
"""Base-image pins, the Hub write lock, and the card's source link.

These checks read committed files only. They make no network request and do
not touch the Hub.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[1]
WORKFLOWS = REPOSITORY / ".github" / "workflows"
WRITER = WORKFLOWS / "hf-space.yml"

DIGEST_FROM = re.compile(
    r"^FROM (?P<image>[a-z0-9./_-]+):(?P<tag>[A-Za-z0-9._-]+)@sha256:(?P<digest>[0-9a-f]{64})$"
)
HF_SECRET = re.compile(r"secrets\.(?:HF_[A-Z0-9_]*|HUGGING[A-Z0-9_]*)")


def space_target() -> str:
    contract = json.loads((ROOT / "PUBLICATION.json").read_text(encoding="utf-8"))
    return contract["target"]["repository"]


def from_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip().upper().startswith("FROM ")
    ]


@pytest.mark.parametrize(
    "dockerfile",
    [
        REPOSITORY / "Dockerfile",
        ROOT / "Dockerfile",
        ROOT / "SPACE_DOCKERFILE",
    ],
    ids=["root", "atelier-v3-ci", "space"],
)
def test_every_base_image_is_digest_pinned(dockerfile: Path) -> None:
    lines = from_lines(dockerfile)
    assert len(lines) == 1, lines
    assert DIGEST_FROM.fullmatch(lines[0]), f"{dockerfile.name}: {lines[0]!r} is not tag@sha256-pinned"


def test_ci_container_and_space_use_the_same_base_image() -> None:
    # atelier-v3.yml builds frontier/atelier_v3/Dockerfile; the Space builds SPACE_DOCKERFILE.
    assert from_lines(ROOT / "Dockerfile") == from_lines(ROOT / "SPACE_DOCKERFILE")


def test_publication_contract_names_the_space_dockerfile() -> None:
    contract = json.loads((ROOT / "PUBLICATION.json").read_text(encoding="utf-8"))
    rows = {row["target"]: row["source"] for row in contract["mapping"]}
    assert rows["Dockerfile"] == "SPACE_DOCKERFILE"


def test_hub_writer_holds_the_canonical_asset_lock() -> None:
    text = WRITER.read_text(encoding="utf-8")
    expected = (
        "concurrency:\n"
        f"  group: hf-write/space/{space_target()}\n"
        "  cancel-in-progress: false\n"
    )
    assert expected in text
    assert "event_name }}" not in text.split("concurrency:", 1)[1].split("jobs:", 1)[0]


def test_only_the_hub_writer_reads_a_hugging_face_secret() -> None:
    readers = sorted(
        path.name
        for path in WORKFLOWS.glob("*.y*ml")
        if HF_SECRET.search(path.read_text(encoding="utf-8"))
    )
    assert readers == [WRITER.name]


def test_no_other_workflow_claims_a_hub_write_lock() -> None:
    for path in WORKFLOWS.glob("*.y*ml"):
        if path == WRITER:
            continue
        assert "hf-write/" not in path.read_text(encoding="utf-8"), path.name


def test_space_card_links_its_github_source() -> None:
    card = (ROOT / "SPACE_README.md").read_text(encoding="utf-8")
    assert "https://github.com/szl-holdings/szl-atelier" in card
    assert ".github/workflows/hf-space.yml" in card
