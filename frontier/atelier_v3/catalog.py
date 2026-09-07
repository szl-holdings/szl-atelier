# SPDX-License-Identifier: Apache-2.0
"""Curated, source-owned public catalog for Atelier v3.

The catalog is intentionally descriptive. It never treats a declared Hub slug,
repository, benchmark, or runtime as independently verified. Provider evidence
is attached only by the bounded read-only adapter in :mod:`app`.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final, Literal

ArtifactKind = Literal["model", "dataset", "space", "capability", "research"]
EvidenceState = Literal["DECLARED", "MEASURED", "PARTIAL", "UNAVAILABLE"]


@dataclass(frozen=True, slots=True)
class Artifact:
    slug: str
    title: str
    kind: ArtifactKind
    group: str
    summary: str
    source_repository: str
    hub_slug: str | None = None
    evidence_state: EvidenceState = "DECLARED"
    commercial_flagship: bool = False
    inventory_only: bool = False

    def public(self) -> dict[str, object]:
        return asdict(self)


CATALOG: Final[tuple[Artifact, ...]] = (
    Artifact(
        slug="a11oy",
        title="A11oy Command Fabric",
        kind="space",
        group="flagships",
        summary="Governed orchestration, evidence chains, approvals, and execution receipts.",
        source_repository="szl-holdings/a11oy",
        hub_slug="SZLHOLDINGS/a11oy",
        commercial_flagship=True,
    ),
    Artifact(
        slug="killinchu",
        title="Killinchu",
        kind="space",
        group="flagships",
        summary="Public-source maritime, sanctions, ownership, and operational evidence surface.",
        source_repository="szl-holdings/killinchu",
        hub_slug="SZLHOLDINGS/killinchu",
        commercial_flagship=True,
    ),
    Artifact(
        slug="szl-constellation",
        title="SZL Constellation",
        kind="space",
        group="discovery",
        summary="Cross-estate navigation and evidence discovery without absorbing source ownership.",
        source_repository="szl-holdings/szl-constellation",
        hub_slug="SZLHOLDINGS/szl-constellation",
    ),
    Artifact(
        slug="szl-khipu",
        title="KHIPU Model Family",
        kind="model",
        group="models-kernels",
        summary="Receipt-aware governed model research and compact inference artifacts.",
        source_repository="szl-holdings/szl-khipu",
        hub_slug="SZLHOLDINGS/SZL-Khipu-1.5B",
    ),
    Artifact(
        slug="lutar-lean",
        title="Lutar Lean",
        kind="capability",
        group="models-kernels",
        summary="Formula, proof, and deterministic governance kernel source authority.",
        source_repository="szl-holdings/lutar-lean",
    ),
    Artifact(
        slug="uds-bundles",
        title="UDS Bundle Observatory",
        kind="capability",
        group="delivery",
        summary="Read-only inspection of repository-owned UDS and Zarf air-gap bundle definitions.",
        source_repository="szl-holdings/uds-bundles",
    ),
    Artifact(
        slug="ouroboros",
        title="Ouroboros Thesis",
        kind="research",
        group="research-history",
        summary="Looped computation as a systems primitive; preserved as research evidence.",
        source_repository="szl-holdings/ouroboros",
        inventory_only=True,
    ),
    Artifact(
        slug="warhacker-demo",
        title="WarHacker Demonstration Record",
        kind="research",
        group="research-history",
        summary="Immutable historical demonstration record; not an active product or runtime.",
        source_repository="szl-holdings/warhacker-demo",
        inventory_only=True,
    ),
)


def catalog_rows() -> list[dict[str, object]]:
    """Return a deterministic JSON-compatible catalog copy."""

    return [item.public() for item in CATALOG]


def find_artifact(kind: str, slug: str) -> Artifact | None:
    """Resolve one exact curated artifact without fuzzy matching."""

    return next((item for item in CATALOG if item.kind == kind and item.slug == slug), None)
