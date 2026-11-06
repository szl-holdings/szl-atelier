# SPDX-License-Identifier: Apache-2.0
"""A BLOCKED publish must say why in the CI log, without echoing credential-shaped text."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import publish_space  # noqa: E402

SOURCE = "a" * 40


def run_main(monkeypatch, capsys, tmp_path: Path, error: Exception) -> tuple[int, dict, Path]:
    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(publish_space, "publish", fail)
    report = tmp_path / "reports" / "readback.json"
    monkeypatch.setattr(sys, "argv", [
        "publish_space.py", "--source-sha", SOURCE, "--package", str(tmp_path / "package"),
        "--report", str(report), "--timeout-seconds", "60",
    ])
    code = publish_space.main()
    line = capsys.readouterr().out.strip().splitlines()[-1]
    return code, json.loads(line), report


def test_blocked_terminal_line_states_the_bounded_reason(monkeypatch, capsys, tmp_path: Path) -> None:
    reason = "runtime readback timed out: HTTPError: HTTP Error 404: Not Found"
    code, terminal, report = run_main(monkeypatch, capsys, tmp_path, publish_space.PublishError(reason))
    assert code == 2
    assert terminal == {"status": "BLOCKED", "error_type": "PublishError", "error": reason, "report": "WRITTEN"}
    receipt = json.loads(report.read_text(encoding="utf-8"))
    assert receipt["state"] == "BLOCKED"
    assert receipt["error"] == reason
    assert receipt["secrets_recorded"] is False


def test_blocked_terminal_reason_is_bounded(monkeypatch, capsys, tmp_path: Path) -> None:
    code, terminal, _ = run_main(monkeypatch, capsys, tmp_path, publish_space.PublishError("x" * 5000))
    assert code == 2
    assert len(terminal["error"]) == 500


def test_credential_shaped_reason_is_withheld_and_never_persisted(monkeypatch, capsys, tmp_path: Path) -> None:
    credential_shaped = "hf_" + "A" * 30
    code, terminal, report = run_main(
        monkeypatch, capsys, tmp_path, RuntimeError(f"provider echoed {credential_shaped}")
    )
    assert code == 2
    assert terminal["error"] == "credential-shaped material withheld from terminal output"
    assert terminal["report"] == "UNAVAILABLE"
    assert credential_shaped not in json.dumps(terminal)
    assert not report.exists()


def test_credential_split_by_the_500_character_cut_is_withheld(monkeypatch, capsys, tmp_path: Path) -> None:
    # The token starts at index 490, so the cut keeps "hf_" plus 7 characters: too short for
    # TOKEN_RE. Scanning only the cut text would print and persist that fragment.
    reason = "x" * 490 + "hf_" + "A" * 30
    code, terminal, report = run_main(monkeypatch, capsys, tmp_path, publish_space.PublishError(reason))
    assert code == 2
    assert terminal["error"] == "credential-shaped material withheld from terminal output"
    assert terminal["report"] == "UNAVAILABLE"
    assert "hf_" not in json.dumps(terminal)
    assert not report.exists()
