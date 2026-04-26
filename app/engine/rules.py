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
    """Load every .json file from data/<subdir>/ keyed by stem filename.

    Files with `"deprecated": true` are read but NOT inserted under their
    own id — they only register an alias pointing at `replaced_by` so
    older saved characters can still resolve their (renamed) species or
    career. Entries may also declare an `aliases: [...]` list to accept
    legacy ids directly.
    """
    path = DATA_ROOT / subdir
    result: dict[str, dict] = {}
    pending_aliases: list[tuple[str, str]] = []  # (alias, target_id)
    if not path.exists():
        return result

    for file in sorted(path.glob("*.json")):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Deprecated stub: record the alias, don't surface the entry.
        if data.get("deprecated"):
            target = data.get("replaced_by")
            if target:
                # Use the filename stem as the alias so old saves still match.
                pending_aliases.append((file.stem, target))
            continue

        key = data.get("id", file.stem)
        result[key] = data
        # Each entry can declare its own aliases.
        for alias in data.get("aliases", []) or []:
            pending_aliases.append((alias, key))

    # Apply aliases — only if the alias doesn't collide with a real entry.
    for alias, target in pending_aliases:
        if alias in result:
            continue
        target_data = result.get(target)
        if target_data is not None:
            result[alias] = target_data

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
def skill_packages() -> dict:
    return _load_file("tables/skill_packages.json")


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


@lru_cache(maxsize=1)
def societies() -> dict:
    return _load_file("tables/societies.json")


def list_societies() -> list[dict]:
    """Return the ordered list of societies for UI enumeration."""
    return societies().get("societies", [])


@lru_cache(maxsize=1)
def education() -> dict:
    return _load_file("tables/education.json")


@lru_cache(maxsize=1)
def psionics() -> dict:
    return _load_file("tables/psionics.json")


@lru_cache(maxsize=1)
def skills() -> dict:
    return _load_file("tables/skills.json")


def all_skills_flat(exclude_jot: bool = False) -> list[str]:
    """Return every skill name as a flat list in 'Skill (Speciality)' format."""
    data = skills()
    result: list[str] = []
    for s in data["core"]:
        if exclude_jot and s == "Jack-of-All-Trades":
            continue
        result.append(s)
    for parent, specs in data["speciality"].items():
        for spec in specs:
            result.append(f"{parent} ({spec})")
    return result


def _unique_entries(data: dict[str, dict]) -> list[dict]:
    """Return unique entries from an id->entry dict, skipping aliases.

    With the alias system, multiple keys can point at the same dict
    (e.g. 'human' and 'imperial_human'). For UI enumeration we want the
    canonical entry only, in a stable order.
    """
    seen_ids: set[str] = set()
    out: list[dict] = []
    for key in sorted(data.keys()):
        entry = data[key]
        entry_id = entry.get("id", key)
        if entry_id in seen_ids:
            continue
        seen_ids.add(entry_id)
        out.append(entry)
    return out


def list_species() -> list[dict]:
    """Deduped, canonical list of species for UI enumeration.

    Entries are sorted by their ``sort_order`` field (ascending); entries
    without that field sort after those that have it, then alphabetically
    by name so the order is always deterministic.
    """
    entries = _unique_entries(species())
    entries.sort(key=lambda e: (e.get("sort_order", 9999), e.get("name", "")))
    return entries


def list_careers() -> list[dict]:
    """Deduped, canonical list of careers for UI enumeration."""
    return _unique_entries(careers())


def reload() -> None:
    """Dev helper — flush caches so edits to JSON are picked up without a restart."""
    for fn in (species, careers, background_skills, life_events,
               injury_table, aging_table, mustering_benefits, education,
               psionics, societies):
        fn.cache_clear()
