"""Career skill table gate regressions."""

import pytest

from app.engine import dice, lifepath
from app.engine.character import CareerTerm, Character, Characteristics


def test_believer_assignment_table_is_available_for_matching_assignment():
    character = Character(phase="career")
    character.characteristics = Characteristics(
        STR=7, DEX=7, END=7, INT=7, EDU=8, SOC=7
    )
    character.current_term = CareerTerm(
        career_id="believer",
        assignment_id="mainstream_believer",
        term_number=1,
        overall_term_number=1,
        rank=0,
    )

    dice.set_forced_rolls([2])
    try:
        result = lifepath.roll_on_skill_table(character, "mainstream_believer")
    finally:
        dice.clear_forced_rolls()

    assert result["roll"]["total"] == 2
    assert any(
        skill.name == "Profession" and skill.speciality == "Religion"
        for skill in character.skills
    )


def test_believer_advanced_education_uses_requires_edu_gate():
    character = Character(phase="career")
    character.characteristics = Characteristics(
        STR=7, DEX=7, END=7, INT=7, EDU=7, SOC=7
    )
    character.current_term = CareerTerm(
        career_id="believer",
        assignment_id="mainstream_believer",
        term_number=1,
        overall_term_number=1,
        rank=0,
    )

    with pytest.raises(ValueError, match="Advanced Education requires EDU 8"):
        lifepath.roll_on_skill_table(character, "advanced_education")
