"""Pre-career education regression tests."""

from app.engine import dice, lifepath
from app.engine.character import Character, Characteristics


def test_hard_knocks_event10_has_tutor_skill_pool_after_failed_graduation():
    character = Character(phase="pre_career")
    character.characteristics = Characteristics(
        STR=7, DEX=7, END=7, INT=6, EDU=6, SOC=5
    )

    qualify = lifepath.pre_career_qualify(character, "school_of_hard_knocks")
    assert qualify["passed"] is True

    lifepath.pre_career_choose_skills(character, ["Melee", "Stealth"])

    # Fail graduation, then roll education event 10.
    dice.set_forced_rolls([2, 10])
    graduation = lifepath.pre_career_graduate(character)
    dice.clear_forced_rolls()

    assert graduation["outcome"] == "fail"
    assert character.pre_career_status["pending_event10"] is True
    pool = character.pre_career_status["event10_skill_pool"]
    assert {"Streetwise", "Melee", "Stealth", "Athletics"}.issubset(set(pool))

    dice.set_forced_rolls([9])
    result = lifepath.pre_career_event10_skill(character, "Melee")
    dice.clear_forced_rolls()

    assert result["roll"]["succeeded"] is True
    assert character.phase == "career"
    assert any(skill.name == "Melee" and skill.level == 1 for skill in character.skills)
