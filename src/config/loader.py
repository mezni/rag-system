from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_BASE_DIR = Path(__file__).resolve().parents[2]
_PROFILES_DIR = _BASE_DIR / "config" / "profiles"


def list_profiles() -> list[str]:
    if not _PROFILES_DIR.exists():
        return []
    return sorted(p.stem for p in _PROFILES_DIR.glob("*.json"))


def load_profile(name: str) -> dict[str, Any]:
    path = _PROFILES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Profile '{name}' not found at {path}")
    return json.loads(path.read_text(encoding="utf-8"))