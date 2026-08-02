"""Citizen event training regressions."""

from app.engine import dice, lifepath
from app.engine.character import CareerTerm, Character, Characteristics


def _citizen_with_known_skills() -> Character:
    character = Character(phase="career")
    character.characteristics = Characteristics(
        STR=7, DEX=7, END=7, INT=7, EDU=12, SOC=7
    )
    character.add_skill("Admin", level=0)
    character.add_skill("Mechanic", level=1)
    character.current_term = CareerTerm(
        career_id="citizen",
        assignment_id="worker",
        term_number=1,
        overall_term_number=1,
        rank=0,
        survived=True,
    )
    return character


def test_citizen_event_6_prompts_for_known_skill_after_edu_success():
    character = _citizen_with_known_skills()

    dice.set_forced_rolls([6])
    try:
        event = lifepath.event_roll(character)
    finally:
        dice.clear_forced_rolls()

    assert event["roll"]["total"] == 6
    assert character.pending_career_event_choice["type"] == "skill_check"

    dice.set_forced_rolls([8])
    try:
        result = lifepath.resolve_career_event_choice(
            character,
            {"skill_name": "EDU"},
        )
    finally:
        dice.clear_forced_rolls()

    pending = result["pending_event_choice"]
    assert pending["type"] == "free_skill_choice"
    assert pending["options"] == ["Admin", "Mechanic"]

    resolved = lifepath.resolve_career_event_choice(character, {"skill": "Mechanic"})

    assert any("Increased Mechanic to 2" in msg for msg in resolved["auto_applied"])
    assert any(skill.name == "Mechanic" and skill.level == 2 for skill in character.skills)
