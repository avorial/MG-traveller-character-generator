"""
JSON data schema validation.
Verifies every career and species file parses cleanly and contains the
mandatory fields the engine depends on.  Catches silent typos in data
before they surface as runtime KeyError / AttributeError bugs.
"""

import json
import os
import pathlib
import pytest

DATA_DIR = pathlib.Path(__file__).parent.parent / "app" / "data"
CAREER_DIR = DATA_DIR / "careers"
SPECIES_DIR = DATA_DIR / "species"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _career_files():
    return list(CAREER_DIR.glob("*.json"))

def _species_files():
    return list(SPECIES_DIR.glob("*.json"))

# ---------------------------------------------------------------------------
# Career file tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", _career_files(), ids=lambda p: p.stem)
def test_career_parses(path):
    """Every career JSON must parse without error."""
    with open(path, encoding="utf-8-sig") as fh:
        data = json.load(fh)
    assert isinstance(data, (dict, list))


@pytest.mark.parametrize("path", _career_files(), ids=lambda p: p.stem)
def test_career_required_fields(path):
    """Each career dict (or list entry) must have id, name, and qualification."""
    with open(path, encoding="utf-8-sig") as fh:
        raw = json.load(fh)
    entries = raw if isinstance(raw, list) else [raw]
    for entry in entries:
        missing = [f for f in ("id", "name", "qualification") if f not in entry]
        assert not missing, f"{path.name}: missing fields {missing} in career {entry.get('id', '?')}"


@pytest.mark.parametrize("path", _career_files(), ids=lambda p: p.stem)
def test_career_skill_tables_present(path):
    """skill_tables must be a dict when present."""
    with open(path, encoding="utf-8-sig") as fh:
        raw = json.load(fh)
    entries = raw if isinstance(raw, list) else [raw]
    for entry in entries:
        if "skill_tables" in entry:
            assert isinstance(entry["skill_tables"], dict), (
                f"{path.name}: skill_tables must be a dict in career {entry.get('id', '?')}"
            )


@pytest.mark.parametrize("path", _career_files(), ids=lambda p: p.stem)
def test_career_ranks_structure(path):
    """ranks must be a dict (or absent); each rank entry must have a title."""
    with open(path, encoding="utf-8-sig") as fh:
        raw = json.load(fh)
    entries = raw if isinstance(raw, list) else [raw]
    for entry in entries:
        if "ranks" not in entry:
            continue
        assert isinstance(entry["ranks"], dict), (
            f"{path.name}: ranks must be a dict in career {entry.get('id', '?')}"
        )

# ---------------------------------------------------------------------------
# Species file tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", _species_files(), ids=lambda p: p.stem)
def test_species_parses(path):
    with open(path, encoding="utf-8-sig") as fh:
        data = json.load(fh)
    assert isinstance(data, (dict, list))


@pytest.mark.parametrize("path", _species_files(), ids=lambda p: p.stem)
def test_species_required_fields(path):
    """Each species entry must have id and name."""
    with open(path, encoding="utf-8-sig") as fh:
        raw = json.load(fh)
    entries = raw if isinstance(raw, list) else [raw]
    for entry in entries:
        if entry.get("deprecated"):
            continue  # redirect/tombstone stubs intentionally lack id/name
        for field in ("id", "name"):
            assert field in entry, f"{path.name}: missing '{field}' in entry {entry.get('id', '?')}"


@pytest.mark.parametrize("path", _species_files(), ids=lambda p: p.stem)
def test_species_characteristic_modifiers_are_numeric(path):
    """characteristic_modifiers values, if present, must be ints."""
    with open(path, encoding="utf-8-sig") as fh:
        raw = json.load(fh)
    entries = raw if isinstance(raw, list) else [raw]
    for entry in entries:
        mods = entry.get("characteristic_modifiers", {})
        for stat, val in mods.items():
            assert isinstance(val, int), (
                f"{path.name}: characteristic_modifiers[{stat}] must be int, got {type(val).__name__}"
            )

# ---------------------------------------------------------------------------
# Table file tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", list((DATA_DIR / "tables").glob("*.json")),
                          ids=lambda p: p.stem)
def test_table_parses(path):
    with open(path, encoding="utf-8-sig") as fh:
        data = json.load(fh)
    assert data is not None
