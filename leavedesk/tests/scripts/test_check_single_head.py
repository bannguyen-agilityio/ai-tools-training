import subprocess
import sys

from scripts import check_single_head


def test_repository_has_a_single_head(capsys) -> None:  # type: ignore[no-untyped-def]
    assert check_single_head.main() == 0
    assert "single Alembic head" in capsys.readouterr().out


def test_script_runs_as_a_command() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_single_head.py"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
