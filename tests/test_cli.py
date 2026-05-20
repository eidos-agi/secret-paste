import os
import stat
import subprocess
import sys


def test_run_sets_secret_in_child_environment():
    cmd = [
        sys.executable,
        "-m",
        "secret_paste.cli",
        "run",
        "--terminal",
        "--env",
        "SECRET_PASTE_TEST",
        "--",
        sys.executable,
        "-c",
        "import os; raise SystemExit(0 if os.environ.get('SECRET_PASTE_TEST') == 's3cr3t' else 1)",
    ]
    result = subprocess.run(cmd, input="s3cr3t\n", text=True, capture_output=True, check=False)
    assert result.returncode == 0
    assert "s3cr3t" not in result.stdout
    assert "s3cr3t" not in result.stderr


def test_write_creates_0600_file(tmp_path):
    target = tmp_path / "token"
    cmd = [
        sys.executable,
        "-m",
        "secret_paste.cli",
        "write",
        "--terminal",
        "--path",
        str(target),
    ]
    result = subprocess.run(cmd, input="token-value\n", text=True, capture_output=True, check=False)
    assert result.returncode == 0
    assert target.read_text() == "token-value"
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert "token-value" not in result.stdout
    assert "token-value" not in result.stderr
