"""
API smoke tests — spin up the FastAPI app via TestClient and verify
the critical endpoints respond with expected shapes.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Ops endpoints
# ---------------------------------------------------------------------------

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_reload_rules():
    r = client.post("/api/reload-rules")
    assert r.status_code == 200
    assert r.json()["reloaded"] is True


# ---------------------------------------------------------------------------
# Data endpoints
# ---------------------------------------------------------------------------

def test_list_species():
    r = client.get("/api/species")
    assert r.status_code == 200
    data = r.json()
    assert "species" in data
    assert len(data["species"]) > 0


def test_list_careers():
    r = client.get("/api/careers")
    assert r.status_code == 200
    data = r.json()
    assert "careers" in data
    assert len(data["careers"]) > 0


def test_background_skills():
    r = client.get("/api/background-skills")
    assert r.status_code == 200


def test_aging_table():
    r = client.get("/api/tables/aging")
    assert r.status_code == 200


def test_injury_table():
    r = client.get("/api/tables/injury")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Character lifecycle
# ---------------------------------------------------------------------------

def test_new_character():
    r = client.post("/api/character/new")
    assert r.status_code == 200
    char = r.json()["character"]
    assert char["phase"] == "characteristics"
    assert char["age"] == 18


def test_roll_characteristics():
    r_new = client.post("/api/character/new")
    char = r_new.json()["character"]

    r = client.post("/api/character/roll-characteristics",
                    json={"character": char})
    assert r.status_code == 200
    updated = r.json()["character"]
    stats = updated["characteristics"]
    for stat in ("STR", "DEX", "END", "INT", "EDU", "SOC"):
        assert 2 <= stats[stat] <= 12, f"{stat} out of range: {stats[stat]}"


def test_roll_characteristics_gm_forced():
    """GM rolls should be consumed in order and respected."""
    r_new = client.post("/api/character/new")
    char = r_new.json()["character"]

    # 6 stats × 1 forced roll each; forced total 8 for all
    r = client.post("/api/character/roll-characteristics",
                    json={"character": char, "gm_rolls": [8, 8, 8, 8, 8, 8]})
    assert r.status_code == 200
    stats = r.json()["character"]["characteristics"]
    for stat in ("STR", "DEX", "END", "INT", "EDU", "SOC"):
        assert stats[stat] == 8, f"{stat} should be forced to 8, got {stats[stat]}"


def test_apply_species_imperial_human():
    r_new = client.post("/api/character/new")
    char = r_new.json()["character"]
    char["phase"] = "species"
    char["characteristics"] = {"STR": 7, "DEX": 7, "END": 7,
                                "INT": 7, "EDU": 7, "SOC": 7}

    r = client.post("/api/character/apply-species",
                    json={"character": char, "species_id": "imperial_human"})
    assert r.status_code == 200
    assert r.json()["character"]["species_id"] == "imperial_human"
