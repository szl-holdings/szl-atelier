# SPDX-License-Identifier: Apache-2.0
"""Start Atelier after binding the generated artifact to its GitHub source SHA."""
from __future__ import annotations

import os
import re
from pathlib import Path

import uvicorn

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SOURCE_FILE = Path(__file__).resolve().parent / "SOURCE_REVISION"


def bind_source_revision() -> None:
    """Load an exact publication-generated source SHA without executing a shell."""

    if os.getenv("SOURCE_REVISION", "").strip():
        return
    try:
        value = SOURCE_FILE.read_text(encoding="utf-8").strip().lower()
    except (OSError, UnicodeError):
        return
    if SHA40.fullmatch(value):
        os.environ["SOURCE_REVISION"] = value


if __name__ == "__main__":
    bind_source_revision()
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "7860")),
        server_header=False,
        access_log=True,
    )
