"""
Dice rolling utilities for Traveller character creation.

Traveller uses 2D (two six-sided dice) for most rolls, occasionally 1D, D3, 3D.
Rolls are typically 2D + DMs vs a target number.
"""

import contextvars
import random
import re
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# GM Mode — forced roll queue
# ---------------------------------------------------------------------------
# In GM mode the client sends a list of raw dice totals that override the
# random rolls consumed in sequence. Set by the API layer before each
# lifepath call; cleared by middleware after the response is sent.
#
# Uses a contextvars.ContextVar so each async request gets its own isolated
# queue — concurrent requests can never bleed GM rolls into each other.

_forced_rolls_var: contextvars.ContextVar[list[int]] = contextvars.ContextVar(
    "forced_rolls", default=[]
)


def set_forced_rolls(rolls: list[int]) -> None:
    _forced_rolls_var.set([int(r) for r in rolls])


def clear_forced_rolls() -> None:
    _forced_rolls_var.set([])


def _pop_forced() -> Optional[int]:
    current = _forced_rolls_var.get()
    if not current:
        return None
    val = current[0]
    _forced_rolls_var.set(current[1:])
    return val


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

    In GM mode a forced raw total is consumed from the queue first; the
    modifier is still applied on top so natural-2 checks (raw_total == 2)
    continue to work correctly.
    """
    forced = _pop_forced()
    if forced is not None:
        total = forced + modifier
        return RollResult(
            dice=[forced],
            raw_total=forced,
            modifier=modifier,
            total=total,
            target=target,
            succeeded=(total >= target) if target is not None else None,
            margin=(total - target) if target is not None else None,
            notation=f"GM:{forced}",
        )

    notation = notation.strip().upper().replace(" ", "")

    # _MINX suffix: each die result is treated as at least X (e.g. 2D_MIN2 = roll 2D but
    # every die showing 1 counts as 2 instead).  Strip the suffix before the normal parse.
    min_per_die = 1
    min_match = re.match(r"^(.+?)_MIN(\d+)$", notation)
    if min_match:
        notation = min_match.group(1)
        min_per_die = int(min_match.group(2))

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

    dice = [max(min_per_die, random.randint(1, die_size)) for _ in range(num_dice)]
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
    Traveller's characteristic modifier table — extends above 15 for
    characteristics off the human scale (MgT 2e, High & Low Characteristics).
        0     -> -3
        1-2   -> -2
        3-5   -> -1
        6-8   -> 0
        9-11  -> +1
        12-14 -> +2
        15-17 -> +3
        18-20 -> +4
        21-23 -> +5
        ...   -> +1 to the DM for every +3 thereafter
    The closed form (score // 3) - 2 reproduces the whole table (0 is the
    single special case at -3).
    """
    if score <= 0:
        return -3
    return (score // 3) - 2


def roll_bane_2d(modifier: int = 0, target: Optional[int] = None) -> RollResult:
    """Roll 3D and drop the highest die (bane = take the two lowest).

    MgT 2e bane mechanic: generate three d6s, discard the best, sum
    the remaining two. The modifier and target are applied on top of
    that reduced sum, exactly like a normal 2D roll.
    """
    forced = _pop_forced()
    if forced is not None:
        # GM override: treat as a straight 2D result with the forced raw total.
        total = forced + modifier
        return RollResult(
            dice=[forced],
            raw_total=forced,
            modifier=modifier,
            total=total,
            target=target,
            succeeded=(total >= target) if target is not None else None,
            margin=(total - target) if target is not None else None,
            notation=f"BANE(GM:{forced})",
        )

    three = [random.randint(1, 6), random.randint(1, 6), random.randint(1, 6)]
    kept = sorted(three)[:2]          # two lowest
    raw_total = sum(kept)
    total = raw_total + modifier

    return RollResult(
        dice=three,
        raw_total=raw_total,
        modifier=modifier,
        total=total,
        target=target,
        succeeded=(total >= target) if target is not None else None,
        margin=(total - target) if target is not None else None,
        notation=f"BANE(3D drop highest:{three}→{kept})"
                 + (f"+{modifier}" if modifier > 0 else f"{modifier}" if modifier < 0 else ""),
    )


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
