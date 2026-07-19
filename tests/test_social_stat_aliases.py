"""SOC replacement characteristic regressions."""

from app.engine import dice, lifepath
from app.engine.character import CareerTerm, Character, Characteristics


def _character_for_soc_check(species_id: str, alias: str) -> Character:
    character = Character(phase="career", species_id=species_id)
    character.characteristics = Characteristics(
        STR=7, DEX=7, END=7, INT=7, EDU=7, SOC=0
    )
    character.extra_characteristics[alias] = 12
    character.current_term = CareerTerm(
        career_id="drifter",
        assignment_id="barbarian",
        term_number=1,
        overall_term_number=1,
        rank=0,
        survived=True,
    )
    character.pending_career_mishap_choice = {
        "type": "skill_check",
        "skills": [{"name": "SOC", "is_stat": True}],
        "target": 8,
        "on_pass": [{"type": "dm_advancement", "amount": 1}],
        "on_fail": [{"type": "dm_advancement", "amount": -1}],
        "prompt": "Roll SOC 8+.",
    }
    return character


def test_soc_check_uses_hiver_res_fallback():
    character = _character_for_soc_check("hiver", "RES")

    dice.set_forced_rolls([6])
    result = lifepath.resolve_career_mishap_choice(character, {"skill_name": "SOC"})
    dice.clear_forced_rolls()

    assert result["skill_check"]["dm"] == 2
    assert result["skill_check"]["passed"] is True
    assert character.dm_next_advancement == 1


def test_soc_check_uses_vargr_cha_fallback():
    character = _character_for_soc_check("extents_vargr", "CHA")

    dice.set_forced_rolls([6])
    result = lifepath.resolve_career_mishap_choice(character, {"skill_name": "SOC"})
    dice.clear_forced_rolls()

    assert result["skill_check"]["dm"] == 2
    assert result["skill_check"]["passed"] is True
    assert character.dm_next_advancement == 1
