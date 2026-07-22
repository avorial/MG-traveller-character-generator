"""Career qualification modifier regressions."""

from app.engine import dice, lifepath
from app.engine.character import Character, Characteristics


def test_soc_minimum_dm_zero_blocks_zhodani_guard():
    character = Character(phase="career", species_id="zhodani")
    character.characteristics = Characteristics(
        STR=7, DEX=7, END=10, INT=7, EDU=7, SOC=9
    )

    result = lifepath.qualify_for_career(character, "zhodani_guard")

    assert result["succeeded"] is False
    assert result["reason"] == "SOC 10+ required"
    assert result["roll"] is None


def test_soc_maximum_blocks_zhodani_prole_above_soc_cap():
    character = Character(phase="career", species_id="imperial_human")
    character.characteristics = Characteristics(
        STR=7, DEX=7, END=7, INT=10, EDU=7, SOC=10
    )

    result = lifepath.qualify_for_career(character, "zhodani_prole")

    assert result["succeeded"] is False
    assert result["reason"] == "SOC 9- required to qualify"
    assert result["roll"] is None


def test_age_over_modifier_applies_to_suerrat_rsf():
    character = Character(age=31, phase="career", species_id="suerrat")
    character.characteristics = Characteristics(
        STR=7, DEX=7, END=7, INT=8, EDU=7, SOC=7
    )

    dice.set_forced_rolls([7])
    try:
        result = lifepath.qualify_for_career(character, "suerrat_rsf")
    finally:
        dice.clear_forced_rolls()

    assert result["roll"]["modifier"] == -2
    assert result["roll"]["total"] == 5
    assert result["succeeded"] is False
