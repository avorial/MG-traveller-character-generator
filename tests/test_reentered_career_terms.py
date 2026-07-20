"""Regression tests for separate stints in the same career."""

from app.engine import lifepath
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

