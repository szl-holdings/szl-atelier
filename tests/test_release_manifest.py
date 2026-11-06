"""RELEASE.json must describe the interpreter the root image actually ships."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = re.compile(r"FROM python:(?P<minor>\d+\.\d+)[^@\s]*@sha256:[0-9a-f]{64}")


def test_release_manifest_declares_the_docker_base_python():
    (line,) = [
        text.strip()
        for text in (ROOT / "Dockerfile").read_text(encoding="utf-8").splitlines()
        if text.strip().upper().startswith("FROM ")
    ]
    match = BASE.fullmatch(line)
    assert match, line
    release = json.loads((ROOT / "RELEASE.json").read_text(encoding="utf-8"))
    assert release["runtime_contract"]["language"] == f"Python {match['minor']}"
