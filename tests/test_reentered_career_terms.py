"""Regression tests for separate stints in the same career."""

import pytest

from app.engine import dice, lifepath
from app.engine.character import CareerTerm, Character


def test_reentering_prior_career_counts_only_current_stint_for_benefits():
    character = Character(age=30)
    character.total_terms = 3
    character.term_history = [
        CareerTerm(
            career_id="navy",
            assignment_id="line_crew",
            term_number=i,
            overall_term_number=i,
            rank=0,
            survived=True,
            advanced=False,
        )
        for i in range(1, 4)
    ]
    character.current_term = CareerTerm(
        career_id="navy",
        assignment_id="line_crew",
        term_number=1,
        overall_term_number=4,
        rank=0,
        survived=False,
        advanced=False,
    )

    result = lifepath.end_term(character, leaving=True, reason="mishap")

    assert result["character"]["completed_careers"][-1]["terms_served"] == 1
    assert result["character"]["completed_careers"][-1]["benefit_rolls_earned"] == 1
    assert result["character"]["pending_benefit_rolls"] == 1


def test_mishap_closes_career_and_blocks_requalification():
    character = Character(age=22, phase="career")
    character.current_term = CareerTerm(
        career_id="navy",
        assignment_id="line_crew",
        term_number=1,
        overall_term_number=1,
        rank=0,
        survived=False,
        advanced=False,
    )

    lifepath.end_term(character, leaving=True, reason="mishap")

    assert "navy" in character.banned_career_ids

    result = lifepath.qualify_for_career(character, "navy")

    assert result["succeeded"] is False
    assert result["roll"] is None
    assert "permanently closed" in result["reason"]


def test_voluntary_departure_does_not_close_career():
    character = Character(age=22, phase="career")
    character.current_term = CareerTerm(
        career_id="navy",
        assignment_id="line_crew",
        term_number=1,
        overall_term_number=1,
        rank=0,
        survived=True,
        advanced=False,
    )

    lifepath.end_term(character, leaving=True, reason="voluntary")

    assert "navy" not in character.banned_career_ids


def test_draft_rerolls_permanently_closed_career():
    character = Character(age=22, phase="career", banned_career_ids=["navy"])

    dice.set_forced_rolls([1, 2])
    try:
        result = lifepath.draft_into_service(character)
    finally:
        dice.clear_forced_rolls()

    assert result["career_id"] == "army"
    assert character.current_term.career_id == "army"
    assert result["draft_rerolls"][0]["career_id"] == "navy"


def test_draft_fails_when_all_table_careers_are_closed():
    character = Character(
        age=22,
        phase="career",
        banned_career_ids=["navy", "army", "marine", "merchant", "scout", "agent"],
    )

    with pytest.raises(ValueError, match="all draft careers are permanently closed"):
        lifepath.draft_into_service(character)
