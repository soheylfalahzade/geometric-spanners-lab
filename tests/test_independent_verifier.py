"""The independent verifier must pass on the repository's own data."""
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def test_verify_independent_passes():
    out = subprocess.run([sys.executable, "verify_independent.py"], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stdout[-1500:]
    assert "ALL CHECKS PASSED" in out.stdout
