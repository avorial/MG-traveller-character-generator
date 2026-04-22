"""
Loads and caches the rules data (species, careers, tables) from JSON files.

All rules data lives in app/data/ as JSON. Adding a species or completing
a career is just a matter of dropping a file into the right directory.
"""

import json
from pathlib import Path
from functools import lru_cache


DATA_ROOT = Path(__file__).parent.parent / "data"


def _load_dir(subdir: str) -> dict[str, dict]:
    """Load every .json file from data/<subdir>/ keyed by stem filename."""
    path = DATA_ROOT / subdir
    result = {}
    if not path.exists():
        return result
    for file in sorted(path.glob("*.json")):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Prefer explicit id field over filename
        key = data.get("id", file.stem)
        result[key] = data
    return result


def _load_file(relative_path: str) -> dict:
    """Load a single JSON file."""
    path = DATA_ROOT / relative_path
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def species() -> dict[str, dict]:
    return _load_dir("species")


@lru_cache(maxsize=1)
def careers() -> dict[str, dict]:
    return _load_dir("careers")


@lru_cache(maxsize=1)
def background_skills() -> dict:
    return _load_file("tables/background_skills.json")


@lru_cache(maxsize=1)
def life_events() -> dict:
    return _load_file("tables/life_events.json")


@lru_cache(maxsize=1)
def injury_table() -> dict:
    return _load_file("tables/injury.json")


@lru_cache(maxsize=1)
def aging_table() -> dict:
    return _load_file("tables/aging.json")


@lru_cache(maxsize=1)
def mustering_benefits() -> dict:
    return _load_file("tables/mustering_benefits.json")


def reload() -> None:
    """Dev helper — flush caches so edits to JSON are picked up without a restart."""
    for fn in (species, careers, background_skills, life_events,
               injury_table, aging_table, mustering_benefits):
        fn.cache_clear()
