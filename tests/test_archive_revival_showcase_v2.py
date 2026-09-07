# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIVAL = ROOT / "revival"
CARDS = ROOT / "cards"
EXPECTED_SOURCES = {
    "szl-atelier",
    "szl-mesh",
    "szl-router",
    "uds-bundles",
}
EXPECTED_HISTORY = {
    "evidence-typed-formula-governance",
    "fail-closed-governed-ai-services",
    "szl-fleet-overlay",
    "szl-otel-mesh",
    "szl-uds-deployment",
    "warhacker-demo",
}
EXPECTED_TRUTH_LADDER = [
    "CLASSIFIED",
    "UNARCHIVED",
    "SOURCE_PR",
    "MERGED",
    "HUB_PUBLISHED",
    "RUNTIME_READY",
    "EXACT_READBACK_VERIFIED",
]


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self.stylesheets: list[str] = []
        self.anchors: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(str(values["id"]))
        if tag == "script" and values.get("src"):
            self.scripts.append(str(values["src"]))
        if (
            tag == "link"
            and values.get("rel") == "stylesheet"
            and values.get("href")
        ):
            self.stylesheets.append(str(values["href"]))
        if tag == "a" and values.get("href"):
            self.anchors.append(str(values["href"]))


def load_catalog() -> dict[str, object]:
    return json.loads(
        (REVIVAL / "catalog.json").read_text(encoding="utf-8")
    )


def test_portfolio_arithmetic_and_canonical_manifest() -> None:
    catalog = load_catalog()
    governance = catalog["governance"]
    assert catalog["schema"] == "szl.archive-revival-showcase/v2"
    assert governance["repository"] == "szl-holdings/.github"
    assert governance["path"] == "governance/archive-portfolio-v2.json"
    assert governance["state"] == "CANONICAL_SOURCE_OF_DISPOSITION"
    assert (
        governance["restored_source_owners"]
        + governance["consolidation_tombstones"]
        + governance["immutable_historical_records"]
        == governance["portfolio_total"]
        == 34
    )


def test_exact_restored_source_owner_set() -> None:
    rows = load_catalog()["source_authorities"]
    ids = [row["id"] for row in rows]
    repositories = [row["repository"] for row in rows]
    assert set(ids) == EXPECTED_SOURCES
    assert len(ids) == len(set(ids)) == 4
    assert repositories == [f"szl-holdings/{value}" for value in ids]
    assert all(row["source_state"] == "ACTIVE_SOURCE_OWNER" for row in rows)


def test_atelier_is_the_only_peer_hub_target() -> None:
    catalog = load_catalog()
    rows = catalog["source_authorities"]
    targets = [row["standalone_hub_target"] for row in rows if row["standalone_hub_target"]]
    assert targets == ["SZLHOLDINGS/szl-atelier"]
    assert catalog["presentation"]["canonical_artifact_space"] == "SZLHOLDINGS/szl-atelier"
    assert catalog["presentation"]["estate_navigation_space"] == "SZLHOLDINGS/szl-constellation"
    assert catalog["presentation"]["new_peer_spaces_created"] is False

    for row in rows:
        if row["id"] == "szl-atelier":
            assert row["hub_publication_state"].startswith("UNAVAILABLE")
            assert row["runtime_state"].startswith("UNAVAILABLE")
        else:
            assert row["standalone_hub_target"] is None
            assert row["presentation_surfaces"] == [
                "SZLHOLDINGS/szl-atelier",
                "SZLHOLDINGS/szl-constellation",
            ]
            assert row["hub_publication_state"] == "NOT_APPLICABLE_NO_PEER_SPACE"


def test_historical_records_and_tombstones_remain_non_sources() -> None:
    catalog = load_catalog()
    assert set(catalog["historical_records"]) == EXPECTED_HISTORY
    assert len(catalog["historical_records"]) == 6
    assert not EXPECTED_SOURCES.intersection(catalog["historical_records"])
    consolidation = catalog["consolidation"]
    assert consolidation["count"] == 24
    assert consolidation["state"] == "READ_ONLY_TOMBSTONES"
    assert consolidation["source_copied_into_atelier"] is False
    assert consolidation["history_rewritten"] is False
    assert consolidation["archive_true_mutations"] is False
    assert consolidation["canonical_mapping"] == {
        "repository": "szl-holdings/.github",
        "path": "governance/archive-portfolio-v2.json",
    }


def test_truth_ladder_is_exact_and_non_collapsed() -> None:
    catalog = load_catalog()
    assert catalog["truth_ladder"] == EXPECTED_TRUTH_LADDER
    assert len(catalog["truth_ladder"]) == len(
        set(catalog["truth_ladder"])
    )


def test_html_uses_local_assets_and_accessible_controls() -> None:
    html = (REVIVAL / "index.html").read_text(encoding="utf-8")
    parser = AssetParser()
    parser.feed(html)
    assert parser.scripts == ["./app.js"]
    assert parser.stylesheets == ["./styles.css"]
    assert {"main", "constellation", "source-list", "source-detail"}.issubset(
        parser.ids
    )
    assert 'href="#main"' in html
    assert 'aria-live="polite"' in html
    assert 'target="_blank" rel="noopener noreferrer"' in html
    assert not any(
        source.startswith(("http://", "https://"))
        for source in parser.scripts + parser.stylesheets
    )


def test_javascript_fetches_only_the_local_catalog() -> None:
    script = (REVIVAL / "app.js").read_text(encoding="utf-8")
    fetch_arguments = re.findall(r"fetch\(\s*([^,\n]+)", script)
    assert fetch_arguments == ['"./catalog.json"']
    for forbidden in (
        "localStorage",
        "sessionStorage",
        "document.cookie",
        "WebSocket(",
        "EventSource(",
        "eval(",
        "new Function(",
        "innerHTML",
    ):
        assert forbidden not in script
    assert "crypto.subtle.digest" in script
    assert "prefers-reduced-motion: reduce" in script


def test_css_covers_mobile_accessibility_and_print() -> None:
    css = (REVIVAL / "styles.css").read_text(encoding="utf-8")
    for contract in (
        "min-width: 320px",
        ":focus-visible",
        "prefers-reduced-motion",
        "prefers-contrast",
        "forced-colors",
        "@media print",
        "overflow-wrap: anywhere",
    ):
        assert contract in css
    assert "min-height: 48px" in css


def test_source_cards_exist_and_preserve_ownership() -> None:
    expected = {
        "ARCHIVE-REVIVAL-V2.md": "CLASSIFIED",
        "SZL-MESH-COMMAND.md": "szl-holdings/szl-mesh",
        "SZL-SOVEREIGN-ROUTER.md": "szl-holdings/szl-router",
        "UDS-BUNDLE-OBSERVATORY.md": "szl-holdings/uds-bundles",
    }
    for filename, marker in expected.items():
        text = (CARDS / filename).read_text(encoding="utf-8")
        assert marker in text
        assert "license: apache-2.0" in text
    combined = "\n".join(
        (CARDS / filename).read_text(encoding="utf-8")
        for filename in expected
    )
    assert "peer Space created by this wave: **no**" in combined
    assert "does not absorb source ownership" in combined


def test_catalog_contains_no_secret_or_live_success_claim() -> None:
    text = (REVIVAL / "catalog.json").read_text(encoding="utf-8")
    lowered = text.lower()
    for forbidden in (
        "github_pat_",
        "ghp_",
        "hf_",
        "api_key",
        "access_token",
        '"hub_publication_state": "published"',
        '"runtime_state": "ready"',
    ):
        assert forbidden not in lowered
