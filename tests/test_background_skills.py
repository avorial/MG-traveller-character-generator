"""Background skill regression tests."""

import pytest

from app.engine import lifepath
from app.engine.character import Character, Characteristics


def test_caprisap_can_choose_astrogation_as_background_skill():
    character = Character(phase="background", species_id="boar_caprisap")
    character.characteristics = Characteristics(
        STR=7, DEX=7, END=7, INT=7, EDU=8, SOC=7
    )

    result = lifepath.set_background_skills(
        character, ["Astrogation", "Mechanic", "Survival"]
    )

    assert result["chosen"] == ["Astrogation", "Mechanic", "Survival"]
    assert character.phase == "pre_career"
    assert any(skill.name == "Astrogation" and skill.level == 0 for skill in character.skills)


def test_unknown_background_skill_still_rejected():
    character = Character(phase="background", species_id="imperial_human")
    character.characteristics = Characteristics(
        STR=7, DEX=7, END=7, INT=7, EDU=8, SOC=7
    )

    with pytest.raises(ValueError, match="Not a background skill"):
        lifepath.set_background_skills(character, ["Astrogation"])


def test_species_starting_skills_are_applied():
    character = Character(phase="species")

    lifepath.apply_species(character, "teakhea")

    assert isinstance(character.traits[0], dict)
    assert character.traits[0]["name"] == "Amphibious"
    assert any(
        skill.name == "Language"
        and skill.speciality == "Trokh"
        and skill.level == 2
        for skill in character.skills
    )
