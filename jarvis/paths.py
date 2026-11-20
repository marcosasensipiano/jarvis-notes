"""Filesystem locations. Resolved lazily so tests can point JARVIS_ROOT / JARVIS_HOME elsewhere."""
import os
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent.parent


def root() -> Path:
    return Path(os.environ.get("JARVIS_ROOT") or _PKG_ROOT)


def data_dir() -> Path:
    p = Path(os.environ.get("JARVIS_HOME") or root() / "data")
    p.mkdir(parents=True, exist_ok=True)
    return p


def _sub(name: str) -> Path:
    p = root() / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def skills_dir() -> Path:
    return _sub("skills")


def library_dir() -> Path:
    return _sub("library")


def lessons_dir() -> Path:
    return _sub("lessons")


def builds_dir() -> Path:
    return _sub("builds")


def dashboard_dir() -> Path:
    return _sub("dashboard")


def config_dir() -> Path:
    return _sub("config")
