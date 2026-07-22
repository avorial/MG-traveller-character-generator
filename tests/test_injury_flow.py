"""Injury flow regressions."""

import pytest

from app.engine import dice, lifepath
from app.engine.character import CareerTerm, Character, Characteristics


def _scout_with_active_term() -> Character:
    character = Character(phase="career")
    character.characteristics = Characteristics(
        STR=7, DEX=8, END=9, INT=8, EDU=8, SOC=7
    )
    character.current_term = CareerTerm(
        career_id="scout",
        assignment_id="surveyor",
        term_number=1,
        overall_term_number=1,
        rank=0,
        survived=True,
    )
    return character


def test_event_skill_check_triggered_mishap_surfaces_pending_injury():
    character = _scout_with_active_term()
    character.pending_career_mishap_choice = {
        "type": "skill_check",
        "skills": [{"name": "Pilot"}],
        "target": 8,
        "on_fail": [{"type": "trigger_disaster_mishap"}],
        "prompt": "Roll Pilot 8+.",
    }

    # Fail the skill check, roll Scout mishap 6 (injury), injury result 2,
    # then damage 4 for the severe-injury stat-choice prompt.
    dice.set_forced_rolls([5, 6, 2, 4])
    result = lifepath.resolve_career_mishap_choice(character, {"skill_name": "Pilot"})
    dice.clear_forced_rolls()

    assert result["injury_pending"] is True
    assert result["injury_data"] is not None
    assert result["injury_data"]["title"] == "Severely injured"
    assert character.pending_injury_choice is not None
    assert character.pending_injury_choice["damage_to_chosen"] == 4


def test_unresolved_injury_blocks_advancement_and_term_end():
    character = _scout_with_active_term()
    character.pending_injury_choice = {
        "roll": 5,
        "title": "Injured",
        "damage_to_chosen": 1,
        "auto_reduce_others": 0,
        "choices": ["STR", "DEX", "END"],
        "prompt": "Choose any physical stat to lose 1 point.",
    }

    with pytest.raises(ValueError, match="pending injury"):
        lifepath.advancement_roll(character)

    with pytest.raises(ValueError, match="pending injury"):
        lifepath.end_term(character, leaving=False)


def test_event_triggered_non_ejecting_mishap_suppresses_forced_prisoner():
    character = Character(phase="career")
    character.characteristics = Characteristics(
        STR=11, DEX=6, END=7, INT=10, EDU=7, SOC=5
    )
    character.current_term = CareerTerm(
        career_id="rogue",
        assignment_id="thief",
        term_number=1,
        overall_term_number=2,
        rank=0,
        survived=True,
    )
    character.pending_career_event_choice = {
        "type": "skill_check",
        "skills": [{"name": "Stealth"}, {"name": "Deception"}],
        "target": 8,
        "on_pass": [
            {"type": "contact", "desc": "Contact [Major Criminal Syndicate]"},
            {"type": "dm_advancement", "amount": 2},
        ],
        "on_fail": [
            {"type": "enemy", "desc": "Enemy [Crime Syndicate]"},
            {"type": "trigger_disaster_mishap"},
        ],
        "prompt": "Syndicate job.",
    }

    dice.set_forced_rolls([6, 2])
    try:
        result = lifepath.resolve_career_event_choice(
            character,
            {"skill_name": "Deception"},
        )
    finally:
        dice.clear_forced_rolls()

    assert result["skill_check"]["passed"] is False
    assert result["disaster_mishap"]["mishap_number"] == 2
    assert character.current_term.survived is True
    assert character.current_term.mishap is None
    assert character.forced_next_career_id is None
    assert character.current_term.benefit_forfeited is True
    assert any(a.description == "Enemy [Crime Syndicate]" for a in character.associates)


def test_non_ejecting_mishap_roll_ignores_forced_next_career_effect():
    character = Character(phase="career")
    character.current_term = CareerTerm(
        career_id="rogue",
        assignment_id="thief",
        term_number=1,
        overall_term_number=1,
        rank=0,
        survived=False,
    )

    dice.set_forced_rolls([2])
    try:
        result = lifepath.mishap_roll(character, suppress_ejection_effects=True)
    finally:
        dice.clear_forced_rolls()

    assert result["mishap_number"] == 2
    assert character.forced_next_career_id is None
    assert character.current_term.benefit_forfeited is True
    assert any("Ejection effect ignored" in msg for msg in result["auto_applied"])
