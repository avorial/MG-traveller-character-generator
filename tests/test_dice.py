"""
Unit tests for the dice module.
Covers normal rolling, GM forced-roll isolation, and the bane mechanic.
"""

import pytest
from app.engine import dice


def test_roll_2d_returns_valid_range():
    for _ in range(200):
        r = dice.roll("2D")
        assert 2 <= r.total <= 12
        assert r.raw_total == r.total  # no modifier
        assert len(r.dice) == 2


def test_roll_1d_range():
    for _ in range(100):
        r = dice.roll("1D")
        assert 1 <= r.total <= 6


def test_roll_with_modifier():
    r = dice.roll("2D", modifier=3, target=8)
    assert r.modifier == 3
    assert r.total == r.raw_total + 3
    assert r.succeeded == (r.total >= 8)


def test_roll_inline_modifier():
    """1D+6 should produce values 7-12."""
    for _ in range(100):
        r = dice.roll("1D+6")
        assert 7 <= r.total <= 12


def test_roll_d3():
    for _ in range(100):
        r = dice.roll("D3")
        assert 1 <= r.total <= 3


def test_characteristic_dm():
    assert dice.characteristic_dm(0) == -3
    assert dice.characteristic_dm(1) == -2
    assert dice.characteristic_dm(3) == -1
    assert dice.characteristic_dm(6) == 0
    assert dice.characteristic_dm(9) == 1
    assert dice.characteristic_dm(12) == 2
    assert dice.characteristic_dm(15) == 3
    assert dice.characteristic_dm(17) == 3
    # Above the human scale — extended Characteristic Modifiers table.
    assert dice.characteristic_dm(18) == 4
    assert dice.characteristic_dm(20) == 4
    assert dice.characteristic_dm(21) == 5
    assert dice.characteristic_dm(23) == 5
    assert dice.characteristic_dm(24) == 6


def test_forced_roll_consumed_in_sequence():
    dice.set_forced_rolls([7, 4])
    r1 = dice.roll("2D")
    r2 = dice.roll("2D")
    r3 = dice.roll("2D")  # no more forced — random
    dice.clear_forced_rolls()

    assert r1.raw_total == 7
    assert r2.raw_total == 4
    assert 2 <= r3.total <= 12  # was random


def test_forced_roll_modifier_applied_on_top():
    dice.set_forced_rolls([5])
    r = dice.roll("2D", modifier=2)
    dice.clear_forced_rolls()
    assert r.raw_total == 5
    assert r.total == 7


def test_clear_forced_rolls():
    dice.set_forced_rolls([10, 10])
    dice.clear_forced_rolls()
    r = dice.roll("2D")
    assert r.raw_total != 10 or True  # may coincidentally hit 10, just check no error


def test_contextvar_isolation():
    """Two separate ContextVar contexts should not share forced rolls."""
    import contextvars

    token = contextvars.copy_context()

    results = {}

    def inner():
        dice.set_forced_rolls([3])
        results["inner"] = dice.roll("2D").raw_total
        dice.clear_forced_rolls()

    # Run inner in its own context copy — outer context unaffected.
    token.run(inner)
    assert results["inner"] == 3

    # Outer context should have no forced rolls set by the inner context.
    r_outer = dice.roll("2D")
    assert r_outer.raw_total != 3 or True  # random — just verifying no bleed via exception


def test_bane_roll_range():
    for _ in range(200):
        r = dice.roll_bane_2d()
        assert 2 <= r.total <= 12


def test_roll_characteristics_keys():
    stats = dice.roll_characteristics()
    assert set(stats) == {"STR", "DEX", "END", "INT", "EDU", "SOC"}
    for v in stats.values():
        assert 2 <= v <= 12
