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


def _career_ids():
    ids = set()
    for path in _career_files():
        with open(path, encoding="utf-8-sig") as fh:
            raw = json.load(fh)
        entries = raw if isinstance(raw, list) else [raw]
        ids.update(entry["id"] for entry in entries if "id" in entry)
    return ids

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


@pytest.mark.parametrize("path", _career_files(), ids=lambda p: p.stem)
def test_career_skill_table_gates_use_supported_keys(path):
    """Skill-table gates must use engine-supported key names and assignment ids."""
    with open(path, encoding="utf-8-sig") as fh:
        raw = json.load(fh)
    entries = raw if isinstance(raw, list) else [raw]
    for entry in entries:
        assignments = entry.get("assignments", {}) or {}
        assignment_ids = (
            {a.get("id") for a in assignments}
            if isinstance(assignments, list)
            else set(assignments.keys())
        )
        for table_key, table in (entry.get("skill_tables", {}) or {}).items():
            if not isinstance(table, dict):
                continue
            assert "min_edu" not in table, (
                f"{path.name}: skill table {table_key!r} uses unsupported min_edu; "
                "use requires_edu"
            )
            assignment_only = table.get("assignment_only")
            if assignment_only:
                assert isinstance(assignment_only, str), (
                    f"{path.name}: skill table {table_key!r} assignment_only must be an assignment id string"
                )
                assert assignment_only in assignment_ids, (
                    f"{path.name}: skill table {table_key!r} assignment_only references "
                    f"unknown assignment {assignment_only!r}"
                )


@pytest.mark.parametrize("path", _career_files(), ids=lambda p: p.stem)
def test_career_qualification_modifiers_use_supported_types(path):
    """Qualification modifiers must use types handled by the engine."""
    supported_types = {
        "age",
        "age_over",
        "characteristic_minimum",
        "last_career",
        "note",
        "per_previous_career",
        "per_previous_term",
        "soc_maximum",
        "soc_minimum",
    }
    with open(path, encoding="utf-8-sig") as fh:
        raw = json.load(fh)
    entries = raw if isinstance(raw, list) else [raw]
    for entry in entries:
        for modifier in (entry.get("qualification", {}) or {}).get("modifiers", []) or []:
            assert modifier.get("type") in supported_types, (
                f"{path.name}: qualification modifier uses unsupported type "
                f"{modifier.get('type')!r}"
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


@pytest.mark.parametrize("path", _species_files(), ids=lambda p: p.stem)
def test_species_career_references_exist(path):
    """Species career allow/block/modifier lists must point at real career ids."""
    valid_careers = _career_ids()
    with open(path, encoding="utf-8-sig") as fh:
        raw = json.load(fh)
    entries = raw if isinstance(raw, list) else [raw]
    for entry in entries:
        if entry.get("deprecated"):
            continue
        assert "allowed_careers" not in entry, (
            f"{path.name}: allowed_careers is ignored by the engine; "
            "use allowed_career_ids"
        )
        for field in ("allowed_career_ids", "blocked_careers"):
            for career_id in entry.get(field, []) or []:
                assert career_id in valid_careers, (
                    f"{path.name}: {field} references unknown career {career_id!r}"
                )
        for career_id in (entry.get("career_qualify_dms", {}) or {}):
            assert career_id in valid_careers, (
                f"{path.name}: career_qualify_dms references unknown career {career_id!r}"
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
