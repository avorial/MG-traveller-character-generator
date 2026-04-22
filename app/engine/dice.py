"""
Dice rolling utilities for Traveller character creation.

Traveller uses 2D (two six-sided dice) for most rolls, occasionally 1D, D3, 3D.
Rolls are typically 2D + DMs vs a target number.
"""

import random
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class RollResult:
    """Outcome of a dice roll, with enough detail to show the player what happened."""
    dice: list[int]
    raw_total: int
    modifier: int
    total: int
    target: Optional[int] = None
    succeeded: Optional[bool] = None
    margin: Optional[int] = None
    notation: str = ""

    def to_dict(self) -> dict:
        return {
            "dice": self.dice,
            "raw_total": self.raw_total,
            "modifier": self.modifier,
            "total": self.total,
            "target": self.target,
            "succeeded": self.succeeded,
            "margin": self.margin,
            "notation": self.notation,
        }


def roll_d6() -> int:
    """Roll a single six-sided die."""
    return random.randint(1, 6)


def roll(notation: str, modifier: int = 0, target: Optional[int] = None) -> RollResult:
    """
    Roll dice using simple Traveller-style notation.

    Supports: 1D, 2D, 3D, 1D+n, 2D-n, D3, D6
    D3 is a 1D roll divided by 2 rounded up (1-1-2-2-3-3 on a d6).
    """
    notation = notation.strip().upper().replace(" ", "")

    # D3 is a special case - Traveller shorthand for "1 to 3"
    if notation in ("D3", "1D3"):
        dice = [roll_d6()]
        val = (dice[0] + 1) // 2  # 1,2 -> 1; 3,4 -> 2; 5,6 -> 3
        total = val + modifier
        return RollResult(
            dice=dice,
            raw_total=val,
            modifier=modifier,
            total=total,
            target=target,
            succeeded=(total >= target) if target is not None else None,
            margin=(total - target) if target is not None else None,
            notation=f"{notation}{'+' if modifier >= 0 else ''}{modifier if modifier else ''}".rstrip(),
        )

    # Match NdS or NdS+k  where S is 6 for Traveller defaults
    match = re.match(r"(\d*)D(\d*)([+-]\d+)?", notation)
    if not match:
        raise ValueError(f"Invalid dice notation: {notation}")

    num_dice = int(match.group(1)) if match.group(1) else 1
    die_size = int(match.group(2)) if match.group(2) else 6
    inline_mod = int(match.group(3)) if match.group(3) else 0

    dice = [random.randint(1, die_size) for _ in range(num_dice)]
    raw_total = sum(dice)
    total_mod = modifier + inline_mod
    total = raw_total + total_mod

    return RollResult(
        dice=dice,
        raw_total=raw_total,
        modifier=total_mod,
        total=total,
        target=target,
        succeeded=(total >= target) if target is not None else None,
        margin=(total - target) if target is not None else None,
        notation=notation + (f"+{modifier}" if modifier > 0 else f"{modifier}" if modifier < 0 else ""),
    )


def characteristic_dm(score: int) -> int:
    """
    Traveller's characteristic modifier table.
        0     -> -3
        1-2   -> -2
        3-5   -> -1
        6-8   -> 0
        9-11  -> +1
        12-14 -> +2
        15+   -> +3
    """
    if score <= 0:
        return -3
    if score <= 2:
        return -2
    if score <= 5:
        return -1
    if score <= 8:
        return 0
    if score <= 11:
        return 1
    if score <= 14:
        return 2
    return 3


def roll_characteristics() -> dict[str, int]:
    """Roll 2D for each of the six characteristics."""
    return {
        "STR": roll("2D").total,
        "DEX": roll("2D").total,
        "END": roll("2D").total,
        "INT": roll("2D").total,
        "EDU": roll("2D").total,
        "SOC": roll("2D").total,
    }
