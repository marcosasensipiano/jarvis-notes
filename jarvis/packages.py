"""Writing, guarding and testing generated code packages (skills and builds)."""
import os
import subprocess
import sys
from pathlib import Path
from . import guard

ALLOWED_EXT = {".py", ".md", ".json", ".txt"}
MAX_FILES, MAX_BYTES = 12, 60_000


def write_package(dest: Path, files: dict) -> None:
    if not isinstance(files, dict) or not files or len(files) > MAX_FILES:
        raise ValueError("files must be a non-empty dict with at most %d entries" % MAX_FILES)
    dest = Path(dest)
    for rel, content in files.items():
        p = Path(rel)
        if p.is_absolute() or ".." in p.parts or p.suffix not in ALLOWED_EXT:
            raise ValueError(f"rejected file path: {rel}")
        if not isinstance(content, str) or len(content.encode()) > MAX_BYTES:
            raise ValueError(f"rejected file content: {rel}")
        target = dest / p
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


def guard_package(dest: Path) -> list:
    problems = []
    for f in sorted(Path(dest).rglob("*.py")):
        problems += guard.check_source(f.read_text(), str(f.relative_to(dest)))
    return problems


def run_tests(dest: Path, timeout: int = 60):
    """Run the package's unittest suite in an isolated interpreter. Zero tests counts as failure."""
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        r = subprocess.run(
            [sys.executable, "-I", "-m", "unittest", "discover", "-s", str(dest), "-p", "test_*.py"],
            cwd=str(dest), capture_output=True, text=True, timeout=timeout, env=env,
        )
    except subprocess.TimeoutExpired:
        return False, "tests timed out"
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        return False, out
    if "Ran 0 tests" in out:
        return False, "package has no tests"
    return True, out
