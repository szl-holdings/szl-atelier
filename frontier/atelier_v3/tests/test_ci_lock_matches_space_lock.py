# SPDX-License-Identifier: Apache-2.0
"""CI must qualify the dependency versions the Space image installs.

SPACE_DOCKERFILE installs frontier/atelier_v3/requirements.txt. atelier-v3.yml and
hf-space.yml install requirements/ci/atelier-v3.txt, which is compiled on top of
that lock, before running these tests and the publisher. If one lock is
regenerated without the other, CI would test versions the Space does not ship.

These checks read committed files only.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[1]
SPACE_LOCK = ROOT / "requirements.txt"
CI_LOCK = REPOSITORY / "requirements" / "ci" / "atelier-v3.txt"

PIN = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==(?P<version>[^\s;\\]+)")


def pinned_versions(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PIN.match(line)
        if match:
            name = re.sub(r"[-_.]+", "-", match["name"]).lower()
            assert name not in pins, f"{path.name}: {name} is pinned twice"
            pins[name] = match["version"]
    assert pins, f"{path} pins nothing"
    return pins


def test_ci_lock_pins_every_space_dependency_at_the_same_version() -> None:
    space = pinned_versions(SPACE_LOCK)
    ci = pinned_versions(CI_LOCK)
    drift = {name: (version, ci.get(name)) for name, version in space.items() if ci.get(name) != version}
    assert not drift, (
        "requirements/ci/atelier-v3.txt no longer carries the Space lock's versions "
        f"(space, ci): {drift}; regenerate it with the command in requirements/ci/atelier-v3.in"
    )
