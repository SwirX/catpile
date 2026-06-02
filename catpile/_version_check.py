from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

from . import __version__

_CHECK_URL = "https://pypi.org/pypi/catpile/json"
_CACHE_FILE = Path.home() / ".cache" / "catpile" / "version_check.json"
_CACHE_TTL = 86400  # 24 hours


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse a semver string into a comparable tuple of ints."""
    try:
        return tuple(int(p) for p in v.split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _get_cache_dir() -> Path:
    cache_dir = _CACHE_FILE.parent
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _read_cache() -> dict | None:
    try:
        if _CACHE_FILE.exists():
            data = json.loads(_CACHE_FILE.read_text())
            if time.time() - data.get("checked_at", 0) < _CACHE_TTL:
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _write_cache(data: dict) -> None:
    try:
        _get_cache_dir()
        data["checked_at"] = time.time()
        _CACHE_FILE.write_text(json.dumps(data))
    except OSError:
        pass


def _fetch_latest_version() -> str | None:
    try:
        req = Request(_CHECK_URL, headers={"Accept": "application/json"})
        with urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return data.get("info", {}).get("version", None)
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return None


def check_for_updates() -> None:
    """Check PyPI for a newer version and print a notice if found.

    Results are cached for 24 hours to avoid spamming PyPI.
    """
    cache = _read_cache()
    if cache is not None:
        latest = cache.get("latest_version")
    else:
        latest = _fetch_latest_version()
        if latest is not None:
            _write_cache({"latest_version": latest})

    current_ver = _parse_version(__version__)
    latest_ver = _parse_version(latest or "")
    if latest_ver > current_ver:
        print(
            f"Update available: catpile {latest} (you have {__version__}). "
            f"Run: pip install --upgrade catpile",
            file=sys.stderr,
        )


def _show_whats_new() -> None:
    """Show what's new in this version (runs once per version)."""
    noticed_file = _CACHE_FILE.parent / "noticed_version"
    try:
        if noticed_file.exists():
            noticed = noticed_file.read_text().strip()
            if noticed == __version__:
                return
    except OSError:
        pass

    print(
        f"\nCatpile {__version__} — what's new:",
        file=sys.stderr,
    )
    print(
        "  • CatUI DSL: .catui files now use a clean indentation-based syntax",
        file=sys.stderr,
    )
    print(
        "  • 'cpile migrate' converts old JSON-format .catui to the new DSL",
        file=sys.stderr,
    )
    print(
        "  • JSON-format .catui files are deprecated and will be removed in a future release",
        file=sys.stderr,
    )
    print(
        "  • All page JSON now includes all metadata keys with defaults",
        file=sys.stderr,
    )
    print(file=sys.stderr)

    try:
        _get_cache_dir()
        noticed_file.write_text(__version__)
    except OSError:
        pass
